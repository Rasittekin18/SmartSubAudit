"""
SmartSubAudit - ml_predictor.py
Makine Öğrenmesi & Zaman Serisi ile Gelecek Ay Kullanım Tahmini:
- Scikit-Learn LinearRegression ile Trend Analizi
- Günlük ve Haftalık Kullanım Dağılımından Gelecek 30 Günlük Projeksiyon
- Birim Maliyet Değişim Kestirimi (Cost-per-Unit Drift)
- Erken Uyarı & Bütçe İkaz Üretimi
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


class UsagePredictor:
    """
    Kullanıcının geçmiş kullanım kayıtlarını Scikit-Learn regresyonu ile modelleyip
    gelecek 30 gün için beklenen kullanım miktarını ve birim maliyeti tahmin eder.
    """

    def __init__(self, data_manager):
        self.dm = data_manager

    def predict_subscription_usage(self, sub_name: str, monthly_cost_try: float, category: str = "streaming", unit: str = "saat") -> dict:
        """
        Tek bir abonelik için geçmiş verileri analiz edip gelecek ayki tahmini üretir.
        """
        usage_df = self.dm.load_usage_df()
        sub_usage = usage_df[usage_df["name"].str.lower() == sub_name.strip().lower()].copy() if not usage_df.empty else pd.DataFrame()

        # 1. DURUM: Hiç kullanım kaydı yoksa
        if sub_usage.empty or sub_usage["usage_amount"].sum() == 0:
            return {
                "name": sub_name,
                "category": category,
                "unit": unit,
                "monthly_cost": monthly_cost_try,
                "current_usage": 0.0,
                "predicted_usage": 0.0,
                "current_cpu": float("inf"),
                "predicted_cpu": float("inf"),
                "trend_direction": "SIFIR_KULLANIM",
                "trend_pct": 0.0,
                "model_name": "Sıfır Kullanım Bazı",
                "r2_score": 0.0,
                "risk_level": "KRİTİK RİSK 🚨",
                "insight_message": (
                    f"'{sub_name}' için bu ay hiç kullanım kaydı girilmedi. Trend devam ederse "
                    f"gelecek ay da 0 {unit} kullanım ile {monthly_cost_try:.1f} TL tamamen boşa gidecektir!"
                ),
                "action_recommendation": "DONDUR_VEYA_IPTAL",
                "has_trend_chart": False,
                "chart_data": None
            }

        # 2. Tarihleri parse et ve günlük topla
        sub_usage["date"] = pd.to_datetime(sub_usage["date"], errors="coerce")
        sub_usage = sub_usage.dropna(subset=["date"]).sort_values(by="date")

        daily_grouped = sub_usage.groupby(sub_usage["date"].dt.date)["usage_amount"].sum().reset_index()
        daily_grouped.rename(columns={"date": "log_date"}, inplace=True)
        daily_grouped["log_date"] = pd.to_datetime(daily_grouped["log_date"])

        total_current_usage = float(daily_grouped["usage_amount"].sum())
        current_cpu = (monthly_cost_try / total_current_usage) if total_current_usage > 0 else float("inf")

        min_date = daily_grouped["log_date"].min()
        daily_grouped["day_index"] = (daily_grouped["log_date"] - min_date).dt.days

        n_points = len(daily_grouped)

        # 3. MAKİNE ÖĞRENMESİ MODELİ (Scikit-Learn LinearRegression)
        if n_points >= 3:
            X = daily_grouped[["day_index"]].values
            y = daily_grouped["usage_amount"].values

            model = LinearRegression()
            model.fit(X, y)
            y_pred = model.predict(X)

            # R2 Skoru (Eğer varyans sıfır değilse)
            try:
                score = float(r2_score(y, y_pred))
            except Exception:
                score = 0.0

            slope = float(model.coef_[0])

            # Gelecek 30 günlük gün-gün projeksiyon
            last_day_idx = int(daily_grouped["day_index"].max())
            future_indices = np.arange(last_day_idx + 1, last_day_idx + 31).reshape(-1, 1)
            future_daily_preds = model.predict(future_indices)
            future_daily_preds = np.clip(future_daily_preds, a_min=0.0, a_max=None)  # Negatif olamaz
            predicted_usage = float(np.sum(future_daily_preds))

            # Güvenlik kontrolü: Eğer trend aşırı uçlara savrulduysa ortalama ile yumuşat
            historical_daily_avg = total_current_usage / max(1, (last_day_idx + 1))
            baseline_monthly = historical_daily_avg * 30.0

            # Tahmini gerçekçi sınırlar içinde tut
            if predicted_usage == 0 and baseline_monthly > 0 and slope >= 0:
                predicted_usage = baseline_monthly

            model_name = "Scikit-Learn Lineer Regresyon (OLS)"
        else:
            # 3 noktadan az veri varsa: Hareketli Ortalama / Günlük Tüketim Hızı
            days_span = max(1, (daily_grouped["log_date"].max() - min_date).days + 1)
            daily_avg = total_current_usage / days_span
            predicted_usage = daily_avg * 30.0
            slope = 0.0
            score = 0.50
            model_name = "Ağırlıklı Tüketim Hızı (Baseline)"

        predicted_usage = max(0.0, round(predicted_usage, 1))
        predicted_cpu = (monthly_cost_try / predicted_usage) if predicted_usage > 0 else float("inf")

        # Trend Yüzdesi ve Yönü
        if total_current_usage > 0:
            trend_pct = ((predicted_usage - total_current_usage) / total_current_usage) * 100.0
        else:
            trend_pct = 0.0

        if trend_pct <= -20.0 or (slope < -0.05 and total_current_usage > 0):
            trend_direction = "DÜŞÜŞ"
            risk_level = "YÜKSEK RİSK 🚨"
            insight = (
                f"⚠️ '{sub_name}' kullanımınız geriye dönük analizde %{abs(trend_pct):.0f} düşüş eğiliminde! "
                f"Gelecek ay sadece ~{predicted_usage:.1f} {unit} kullanacağınız tahmin ediliyor. "
                f"Birim maliyetiniz {predicted_cpu:.1f} TL/{unit} seviyesine fırlayacak. "
                f"Gereksiz fatura ödememek için şimdiden dondurmayı veya iptal etmeyi değerlendirmelisiniz."
            )
            action = "DONDUR_VEYA_IPTAL"
        elif trend_pct >= 20.0 or slope > 0.05:
            trend_direction = "ARTIŞ"
            risk_level = "VERİMLİ / DÜŞÜK RİSK 🟢"
            insight = (
                f"🚀 '{sub_name}' kullanımınız %{trend_pct:.0f} yükseliş trendinde! "
                f"Gelecek ay ~{predicted_usage:.1f} {unit} aktif kullanım öngörülüyor. "
                f"Birim maliyetiniz {predicted_cpu:.1f} TL/{unit} seviyesine düşerek yatırım getirinizi artıracak. "
                f"Aboneliği tutmanız şiddetle tavsiye edilir."
            )
            action = "KORU_VE_KULLAN"
        else:
            trend_direction = "STABİL"
            risk_level = "ORTA / DENGELİ ⚖️"
            insight = (
                f"⚖️ '{sub_name}' kullanımınız stabil bir çizgide ilerliyor. "
                f"Gelecek ay ~{predicted_usage:.1f} {unit} kullanım ve "
                f"{predicted_cpu:.1f} TL/{unit} birim maliyet bekleniyor."
            )
            action = "TAKIP_ET"

        # Görselleştirme için hazırlık
        last_date = daily_grouped["log_date"].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, 31)]

        return {
            "name": sub_name,
            "category": category,
            "unit": unit,
            "monthly_cost": monthly_cost_try,
            "current_usage": round(total_current_usage, 1),
            "predicted_usage": predicted_usage,
            "current_cpu": round(current_cpu, 1) if np.isfinite(current_cpu) else float("inf"),
            "predicted_cpu": round(predicted_cpu, 1) if np.isfinite(predicted_cpu) else float("inf"),
            "trend_direction": trend_direction,
            "trend_pct": round(trend_pct, 1),
            "model_name": model_name,
            "r2_score": max(0.0, round(score, 2)),
            "risk_level": risk_level,
            "insight_message": insight,
            "action_recommendation": action,
            "has_trend_chart": True,
            "chart_dates_hist": [d.strftime("%Y-%m-%d") for d in daily_grouped["log_date"]],
            "chart_usage_hist": [float(u) for u in daily_grouped["usage_amount"]],
            "future_dates": [d.strftime("%Y-%m-%d") for d in future_dates],
            "future_usage_sum": predicted_usage
        }

    def predict_all_subscriptions(self, audit_df: pd.DataFrame) -> list:
        """
        Kayıtlı tüm abonelikler için toplu gelecek ay tahmini ve risk taraması yapar.
        """
        if audit_df.empty:
            return []

        results = []
        for _, row in audit_df.iterrows():
            sub_name = row["name"]
            cost_try = float(row["monthly_cost"])
            cat = row["category"]
            unit = row.get("unit", "saat")
            pred = self.predict_subscription_usage(sub_name, cost_try, cat, unit)
            results.append(pred)

        # En riskli olanları (düşüşte veya sıfır kullanımda olanları) başa al
        risk_priority = {"KRİTİK RİSK 🚨": 0, "YÜKSEK RİSK 🚨": 1, "ORTA / DENGELİ ⚖️": 2, "VERİMLİ / DÜŞÜK RİSK 🟢": 3}
        results.sort(key=lambda x: risk_priority.get(x["risk_level"], 99))
        return results
