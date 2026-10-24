"""
SmartSubAudit - analytics.py
Analitik & Karar Destek Motoru:
- Pandas ile Veri Manipülasyonu (merge, groupby, loc/iloc, sort_values)
- NumPy ile Vektörel Hesaplamalar
- "Birim Kullanım Başına Maliyet" (Cost-per-Use) Metriği
- Yıllık Finansal İsraf / Tasarruf Simülasyonu
- Tavsiye & Risk Matrisi Üretimi
"""

import pandas as pd
import numpy as np
from models import subscription_factory
from currency_service import CurrencyService
from ml_predictor import UsagePredictor


class AnalyticsEngine:
    def __init__(self, data_manager, currency_service: CurrencyService = None):
        self.dm = data_manager
        self.cs = currency_service if currency_service is not None else CurrencyService(data_manager)
        self.predictor = UsagePredictor(data_manager)

    def perform_full_audit(self) -> pd.DataFrame:
        """
        Abonelikler ile kullanım verilerini birleştirip birim maliyet,
        tavsiye ve verimlilik metriklerini içeren kapsamlı analiz tablosu üretir.
        Dövizli abonelikleri (USD, EUR, GBP) canlı API kurlarıyla otomatik TL'ye dönüştürür.
        """
        subs_df = self.dm.load_subscriptions_df()
        usage_df = self.dm.load_usage_df()

        if subs_df.empty:
            return pd.DataFrame()

        # Kullanım toplamlarını al
        if not usage_df.empty:
            usage_summary = usage_df.groupby("name")["usage_amount"].sum().reset_index()
            usage_summary.rename(columns={"usage_amount": "total_usage"}, inplace=True)
        else:
            usage_summary = pd.DataFrame(columns=["name", "total_usage"])

        # Sol birleşim (Left Join): Kullanımı olmayan abonelikler de gelsin (0 olarak)
        merged = pd.merge(subs_df, usage_summary, on="name", how="left")
        merged["total_usage"] = merged["total_usage"].fillna(0.0)

        # Analitik sütunları listeler halinde toplayıp ekleyelim
        cost_per_units = []
        recommendations = []
        rec_details = []
        units = []
        annual_wastes = []
        monthly_costs_try = []
        exchange_rates = []
        display_costs = []
        days_until_renewal_list = []

        for _, row in merged.iterrows():
            orig_cost = float(row["monthly_cost"])
            orig_curr = str(row.get("currency", "TL")).strip().upper()

            # Canlı döviz kuru ile TL karşılığına dönüştür
            cost_in_try, rate_used = self.cs.convert_to_try(orig_cost, orig_curr)
            monthly_costs_try.append(cost_in_try)
            exchange_rates.append(rate_used)

            # Görselleştirme ve özet metni
            if orig_curr in ["TL", "TRY"]:
                display_costs.append(f"{orig_cost:.2f} TL")
            elif orig_curr == "USD":
                display_costs.append(f"${orig_cost:.2f} ({cost_in_try:.1f} TL)")
            elif orig_curr == "EUR":
                display_costs.append(f"€{orig_cost:.2f} ({cost_in_try:.1f} TL)")
            elif orig_curr == "GBP":
                display_costs.append(f"£{orig_cost:.2f} ({cost_in_try:.1f} TL)")
            else:
                display_costs.append(f"{orig_cost:.2f} {orig_curr} ({cost_in_try:.1f} TL)")

            # Analiz ve puanlama TL bazlı tek potada yapılır
            sub_obj = subscription_factory(
                name=row["name"],
                monthly_cost=cost_in_try,
                category=row["category"],
                currency="TL",
                renewal_day=row["renewal_day"]
            )

            total_u = row["total_usage"]
            cpu = sub_obj.calculate_value_score(total_u)
            rec, detail = sub_obj.get_recommendation(total_u)
            days_left = sub_obj.days_until_renewal()

            cost_per_units.append(cpu if np.isfinite(cpu) else np.nan)
            recommendations.append(rec)
            rec_details.append(detail)
            units.append(sub_obj.get_usage_unit())
            days_until_renewal_list.append(days_left)

            # Yıllık israf hesabı: İptal veya düşür önerilenlerin yıllık yükü (TL)
            if rec == "IPTAL_ET":
                annual_wastes.append(sub_obj.annual_cost())
            elif rec == "DUSUR":
                annual_wastes.append(sub_obj.annual_cost() * 0.40)
            else:
                annual_wastes.append(0.0)

        merged["original_cost"] = merged["monthly_cost"]
        merged["original_currency"] = merged["currency"]
        merged["exchange_rate"] = exchange_rates
        merged["monthly_cost"] = monthly_costs_try  # Grafik ve hesaplamalar TL cinsinden
        merged["display_cost"] = display_costs
        merged["unit"] = units
        merged["cost_per_unit"] = cost_per_units
        merged["recommendation"] = recommendations
        merged["rec_detail"] = rec_details
        merged["annual_waste"] = annual_wastes
        merged["days_until_renewal"] = days_until_renewal_list

        # Sıralama: En yüksek TL maliyetten düşüğe
        merged.sort_values(by="monthly_cost", ascending=False, inplace=True)
        merged.reset_index(drop=True, inplace=True)
        return merged

    def get_summary_kpi(self, audit_df: pd.DataFrame) -> dict:
        """
        Üst düzey KPI özet kartı değerlerini döner.
        """
        if audit_df.empty:
            return {
                "total_monthly": 0.0,
                "total_annual": 0.0,
                "potential_annual_savings": 0.0,
                "total_services": 0,
                "cancel_count": 0,
                "best_service": "Yok",
                "worst_service": "Yok"
            }

        total_monthly = audit_df["monthly_cost"].sum()
        total_annual = total_monthly * 12.0
        potential_savings = audit_df["annual_waste"].sum()
        total_services = len(audit_df)
        cancel_count = (audit_df["recommendation"] == "IPTAL_ET").sum()

        # En verimli (birim maliyeti sonlu ve en düşük olan veya TUT kararı alan)
        valid_cpu = audit_df.dropna(subset=["cost_per_unit"])
        if not valid_cpu.empty:
            best_service = valid_cpu.loc[valid_cpu["cost_per_unit"].idxmin()]["name"]
        else:
            best_service = "Belirlenemedi"

        # En verimsiz (IPTAL_ET kararı alan ve en yüksek aylık ücrete sahip)
        cancels = audit_df[audit_df["recommendation"] == "IPTAL_ET"]
        if not cancels.empty:
            worst_service = cancels.loc[cancels["monthly_cost"].idxmax()]["name"]
        else:
            worst_service = "Yok"

        return {
            "total_monthly": round(total_monthly, 2),
            "total_annual": round(total_annual, 2),
            "potential_annual_savings": round(potential_savings, 2),
            "total_services": total_services,
            "cancel_count": int(cancel_count),
            "best_service": best_service,
            "worst_service": worst_service
        }

    def generate_trend_simulation(self, audit_df: pd.DataFrame, months: int = 6) -> pd.DataFrame:
        """
        Gelecek N ay için mevcut harcama vs optimize edilmiş harcama projeksiyonu simüle eder.
        """
        if audit_df.empty:
            return pd.DataFrame()

        current_monthly = audit_df["monthly_cost"].sum()
        monthly_savings = audit_df["annual_waste"].sum() / 12.0
        optimized_monthly = current_monthly - monthly_savings

        months_list = [f"Ay {i}" for i in range(1, months + 1)]
        cumulative_current = np.cumsum(np.full(months, current_monthly))
        cumulative_optimized = np.cumsum(np.full(months, optimized_monthly))

        trend_df = pd.DataFrame({
            "Month": months_list,
            "Mevcut_Durum": cumulative_current,
            "Optimize_Edilmis": cumulative_optimized,
            "Net_Tasarruf": cumulative_current - cumulative_optimized
        })
        return trend_df

    def get_urgent_renewal_alerts(self, audit_df: pd.DataFrame = None, days_threshold: int = 3) -> dict:
        """
        Akıllı Fatura Yenilenme Alarmı & Bildirim Merkezi:
        Yenilenmesine <= days_threshold (varsayılan 3) gün kalan servisleri ve
        özellikle acil iptal edilmesi gereken (IPTAL_ET) sızıntıları tespit eder.
        """
        if audit_df is None:
            audit_df = self.perform_full_audit()

        if audit_df.empty or "days_until_renewal" not in audit_df.columns:
            return {
                "critical_alerts": [],
                "upcoming_renewals": [],
                "critical_count": 0,
                "upcoming_count": 0,
                "immediate_monthly_savings": 0.0,
                "immediate_annual_savings": 0.0
            }

        # <= days_threshold gün kalanları filtrele
        near_renewals = audit_df[audit_df["days_until_renewal"] <= days_threshold].copy()
        if near_renewals.empty:
            return {
                "critical_alerts": [],
                "upcoming_renewals": [],
                "critical_count": 0,
                "upcoming_count": 0,
                "immediate_monthly_savings": 0.0,
                "immediate_annual_savings": 0.0
            }

        near_renewals.sort_values(by=["days_until_renewal", "monthly_cost"], ascending=[True, False], inplace=True)

        def make_urgency_label(days: int) -> str:
            if days == 0:
                return "🚨 BUGÜN YENİLENİYOR!"
            elif days == 1:
                return "🚨 YARIN YENİLENİYOR!"
            else:
                return f"⚠️ {days} GÜN KALDI"

        near_renewals["urgency_label"] = near_renewals["days_until_renewal"].apply(make_urgency_label)

        # Kritik İptal Alarmları: Hem yenilenmesi kapıda hem de IPTAL_ET tavsiyesi var
        critical_df = near_renewals[near_renewals["recommendation"] == "IPTAL_ET"]
        critical_alerts = critical_df.to_dict(orient="records")

        # Yaklaşan tüm yenilenmeler (bilgilendirme)
        upcoming_renewals = near_renewals.to_dict(orient="records")

        immediate_monthly = float(critical_df["monthly_cost"].sum()) if not critical_df.empty else 0.0
        immediate_annual = immediate_monthly * 12.0

        return {
            "critical_alerts": critical_alerts,
            "upcoming_renewals": upcoming_renewals,
            "critical_count": len(critical_alerts),
            "upcoming_count": len(upcoming_renewals),
            "immediate_monthly_savings": round(immediate_monthly, 2),
            "immediate_annual_savings": round(immediate_annual, 2)
        }

    def get_ml_predictions(self, audit_df: pd.DataFrame = None) -> list:
        """
        Kayıtlı tüm abonelikler için Scikit-Learn regresyonu ile gelecek ayki
        kullanım tahmini ve birim maliyet projeksiyonunu üretir.
        """
        if audit_df is None:
            audit_df = self.perform_full_audit()
        return self.predictor.predict_all_subscriptions(audit_df)

    def get_subscription_alternatives(self, sub_name: str, monthly_cost_try: float, category: str, total_usage: float, rec: str) -> list:
        """
        Belirtilen abonelik için pazar alternatifleri ve alt paket önerilerini döner.
        """
        from recommendation_engine import AlternativeAdvisor
        return AlternativeAdvisor.get_recommendations_for_subscription(
            sub_name, monthly_cost_try, category, total_usage, rec
        )

    def get_bundle_optimizations(self, audit_df: pd.DataFrame = None) -> list:
        """
        Sepetteki çapraz servis çakışmalarını ve piyasadaki paket tasarruf (bundle) fırsatlarını analiz eder.
        """
        if audit_df is None or audit_df.empty:
            audit_df = self.perform_full_audit()
        from recommendation_engine import BundleAdvisor
        return BundleAdvisor.analyze_bundles(audit_df)


    def get_category_budget_analysis(self, audit_df: pd.DataFrame = None) -> list:
        """
        Kategori bazlı aylık bütçe limitleri ile gerçekleşen toplam harcamayı
        karşılaştırarak kota doluluk oranlarını ve aşım uyarılarını hesaplar.
        """
        if audit_df is None:
            audit_df = self.perform_full_audit()

        budgets = self.dm.get_category_budgets()

        # Sistemdeki kategorileri topla
        cat_spend = {}
        cat_counts = {}
        cat_services = {}

        if not audit_df.empty:
            for _, r in audit_df.iterrows():
                c = str(r["category"]).lower().strip()
                cost = float(r["monthly_cost"])
                name = r["name"]
                cat_spend[c] = cat_spend.get(c, 0.0) + cost
                cat_counts[c] = cat_counts.get(c, 0) + 1
                if c not in cat_services:
                    cat_services[c] = []
                cat_services[c].append(name)

        # Hem bütçesi olan hem de harcaması olan tüm kategorileri birleştir
        all_categories = sorted(list(set(list(budgets.keys()) + list(cat_spend.keys()))))
        results = []

        category_labels = {
            "streaming": "🎬 Streaming (Dizi / Film / Müzik)",
            "ai_tool": "🤖 AI & Yazılım Araçları",
            "fitness": "🏋️ Fitness & Spor Salonu"
        }

        for cat in all_categories:
            spend = cat_spend.get(cat, 0.0)
            limit = budgets.get(cat, 500.0)
            ratio = (spend / limit) if limit > 0 else 0.0
            ratio_pct = ratio * 100.0
            overrun = max(0.0, spend - limit)
            remaining = max(0.0, limit - spend)

            if spend > limit:
                status = "AŞILDI 🚨"
                status_color = "#ef4444"
                status_message = f"Kotanızı {overrun:,.1f} TL aştınız! Lütfen gereksiz servisleri iptal edin veya düşürün."
            elif ratio_pct >= 85.0:
                status = "KRİTİK BÖLGE ⚠️"
                status_color = "#f59e0b"
                status_message = f"Kotanın %{ratio_pct:.0f}'i doldu! Sadece {remaining:,.1f} TL bütçeniz kaldı."
            else:
                status = "GÜVENLİ BÖLGE 🟢"
                status_color = "#22c55e"
                status_message = f"Bütçeniz kontrol altında. Kalan bütçe: {remaining:,.1f} TL (%{100 - ratio_pct:.0f})."

            results.append({
                "category": cat,
                "label": category_labels.get(cat, f"📦 {cat.capitalize()}"),
                "spend": round(spend, 2),
                "limit": round(limit, 2),
                "ratio": round(ratio, 4),
                "ratio_pct": round(ratio_pct, 1),
                "overrun": round(overrun, 2),
                "remaining": round(remaining, 2),
                "status": status,
                "status_color": status_color,
                "status_message": status_message,
                "service_count": cat_counts.get(cat, 0),
                "services": cat_services.get(cat, [])
            })

        # Aşımda olanları en başa sırala
        results.sort(key=lambda x: x["ratio"], reverse=True)
        return results

    def get_activity_heatmap_data(self, sub_name: str = None, days: int = 140) -> dict:
        """
        GitHub Tarzı Takvim Isı Haritası & Alışkanlık Analizi:
        Belirtilen gün aralığında (varsayılan 140 gün / 20 hafta) günlük kullanım matrisini,
        en aktif günleri, kesintisiz kullanım serilerini (streak) ve hafta içi/hafta sonu
        dağılımını hesaplar.
        """
        import datetime

        usage_df = self.dm.load_usage_df()
        today = datetime.date.today()

        # Takvim matrisini her zaman bir Pazartesi gününden başlatabilmek için:
        raw_start_date = today - datetime.timedelta(days=days)
        days_to_monday = raw_start_date.weekday()
        start_date = raw_start_date - datetime.timedelta(days=days_to_monday)

        date_list = [start_date + datetime.timedelta(days=i) for i in range((today - start_date).days + 1)]

        if not usage_df.empty:
            filtered_usage = usage_df.copy()
            if sub_name and sub_name not in ["Tümü", "Tüm Servisler (Genel Aktivite)"]:
                filtered_usage = filtered_usage[filtered_usage["name"].str.lower() == sub_name.strip().lower()]

            if not filtered_usage.empty:
                filtered_usage["parsed_date"] = pd.to_datetime(filtered_usage["date"]).dt.date
                daily_agg = filtered_usage.groupby("parsed_date").agg({
                    "usage_amount": "sum",
                    "name": lambda x: ", ".join(list(dict.fromkeys(x)))
                }).reset_index()
                daily_dict = {row["parsed_date"]: (row["usage_amount"], row["name"]) for _, row in daily_agg.iterrows()}
            else:
                daily_dict = {}
        else:
            daily_dict = {}

        weekdays_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        short_weekdays_tr = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
        months_tr = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]

        day_records = []
        weekday_totals = {i: 0.0 for i in range(7)}
        weekday_active_days = {i: 0 for i in range(7)}

        active_days_count = 0
        total_usage_sum = 0.0
        daily_usages_sequence = []

        for d in date_list:
            amount, services_used = daily_dict.get(d, (0.0, ""))
            weekday_idx = d.weekday()
            week_idx = (d - start_date).days // 7

            if amount > 0:
                active_days_count += 1
                total_usage_sum += amount
                weekday_totals[weekday_idx] += amount
                weekday_active_days[weekday_idx] += 1
                daily_usages_sequence.append(1)
            else:
                daily_usages_sequence.append(0)

            month_str = months_tr[d.month - 1]
            formatted_date = f"{d.day} {month_str} {d.year}"

            tooltip = f"{formatted_date} ({weekdays_tr[weekday_idx]}): "
            if amount > 0:
                tooltip += f"{amount:.1f} saat/ziyaret [{services_used}]"
            else:
                tooltip += "Kullanım kaydı yok (0)"

            day_records.append({
                "date": d.strftime("%Y-%m-%d"),
                "display_date": formatted_date,
                "weekday": weekday_idx,
                "weekday_name": short_weekdays_tr[weekday_idx],
                "full_weekday_name": weekdays_tr[weekday_idx],
                "week_idx": week_idx,
                "amount": amount,
                "services": services_used,
                "month_str": month_str,
                "tooltip": tooltip
            })

        total_days = len(date_list)
        activity_rate_pct = (active_days_count / total_days * 100.0) if total_days > 0 else 0.0

        longest_streak = 0
        current_streak = 0
        temp_streak = 0

        for val in daily_usages_sequence:
            if val == 1:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        rev_seq = list(reversed(daily_usages_sequence))
        start_idx = 0
        if rev_seq and rev_seq[0] == 0 and len(rev_seq) > 1 and rev_seq[1] == 1:
            start_idx = 1

        for val in rev_seq[start_idx:]:
            if val == 1:
                current_streak += 1
            else:
                break

        busiest_day_idx = max(weekday_totals, key=weekday_totals.get)
        busiest_day_name = weekdays_tr[busiest_day_idx]
        busiest_day_amount = weekday_totals[busiest_day_idx]

        weekend_usage = weekday_totals[5] + weekday_totals[6]
        weekend_ratio_pct = (weekend_usage / total_usage_sum * 100.0) if total_usage_sum > 0 else 0.0

        insights = []
        if active_days_count == 0:
            insights.append("Bu dönemde hiç kullanım kaydı girilmemiş. Servisleri kullanmıyorsanız dondurarak veya iptal ederek tasarruf sağlayabilirsiniz.")
        else:
            if weekend_ratio_pct >= 60.0:
                insights.append(f"Tüketiminizin %{weekend_ratio_pct:.0f}'i hafta sonuna yoğunlaşmış. Hafta içi neredeyse hiç açılmıyor; bütçe optimizasyonu için planı gözden geçirebilirsiniz.")
            elif weekend_ratio_pct <= 25.0:
                insights.append(f"Tüketiminizin %{100 - weekend_ratio_pct:.0f}'i mesai günlerinde (hafta içi) gerçekleşiyor. Düzenli çalışma/üretkenlik alışkanlığı tespit edildi.")

            if longest_streak >= 5:
                insights.append(f"Tebrikler! {longest_streak} gün üst üste kesintisiz kullanım serisi (streak) yakaladınız.")
            elif longest_streak <= 1 and active_days_count > 0:
                insights.append("Kullanımınız çok seyrek ve düzensiz. Sabit aylık abonelik yerine 'kullandıkça öde' modeli daha karlı olabilir.")

            busiest_day_pct = (busiest_day_amount / total_usage_sum * 100.0) if total_usage_sum > 0 else 0.0
            insights.append(f"Haftanın en yoğun günü {busiest_day_name} (Toplam tüketimin %{busiest_day_pct:.0f}'i).")

        return {
            "days": day_records,
            "total_days": total_days,
            "active_days": active_days_count,
            "inactive_days": total_days - active_days_count,
            "activity_rate_pct": round(activity_rate_pct, 1),
            "total_usage_sum": round(total_usage_sum, 1),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "busiest_day": busiest_day_name,
            "busiest_day_amount": round(busiest_day_amount, 1),
            "weekend_ratio_pct": round(weekend_ratio_pct, 1),
            "weekday_totals": weekday_totals,
            "weekdays_tr": weekdays_tr,
            "insights": insights
        }




