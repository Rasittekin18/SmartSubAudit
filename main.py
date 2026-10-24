"""
SmartSubAudit - main.py
Uygulama Giriş Noktası & Etkileşimli Konsol Menüsü
"""

import sys
import os

# Windows konsolunda UTF-8 / Emoji karakter desteği sağla
if sys.platform.startswith("win"):
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from data_manager import DataManager
from analytics import AnalyticsEngine
from visualizer import DashboardVisualizer


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║               🔍 SMART SUBAUDIT v1.0                          ║
║     Abonelik & Birim Kullanım Başına Maliyet Denetleyicisi    ║
║         (OOP + Pandas + NumPy + Matplotlib Projesi)          ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def print_menu():
    print(" -------------------------------------------------------------")
    print("  [1] 📋 Aboneliklerimi Listele (OOP Nesneleri)")
    print("  [2] ➕ Yeni Abonelik Ekle")
    print("  [3] ⏱️  Kullanım Kaydı Gir (Saat / Ziyaret)")
    print("  [4] 📊 Kapsamlı Maliyet & Tavsiye Analizi Çalıştır")
    print("  [5] 📈 4 Panelli Görsel Dashboard Aç (Matplotlib)")
    print("  [6] 🗑️  Abonelik Sil")
    print("  [7] 📄 Resmi PDF Finans Raporu Üret (ReportLab)")
    print("  [8] 🤖 Gelecek Ay Kullanım Tahmini (Scikit-Learn ML)")
    print("  [9] 🎯 Kategori Bütçe Kotalarını Yönet & Güncelle")
    print("  [10] 📅 Kullanım Isı Haritası & Alışkanlık Analizi (GitHub Tarzı)")
    print("  [11] 📦 Çapraz Paket (Bundle) & Birleştirme Tasarrufu Motoru")
    print("  [Q] 🚪 Çıkış")
    print(" -------------------------------------------------------------")


def list_subscriptions(dm: DataManager):
    objects = dm.load_subscription_objects()
    if not objects:
        print("\n[BİLGİ] Kayıtlı abonelik bulunamadı. Lütfen [2] ile ekleyin.\n")
        return

    print(f"\n--- KAYITLI ABONELİKLER ({len(objects)} Adet) ---")
    print(f"{'Servis Adı':<18} | {'Kategori':<12} | {'Aylık Ücret':<12} | {'Yıllık Yük':<12} | {'Kalan Gün'}")
    print("-" * 72)
    for sub in objects:
        print(f"{sub.get_name():<18} | {sub.get_category():<12} | {sub.get_monthly_cost():>6.2f} {sub.get_currency():<3} | {sub.annual_cost():>7.2f} {sub.get_currency():<3} | {sub.days_until_renewal()} gün")
    print("-" * 72 + "\n")


def add_subscription_flow(dm: DataManager):
    print("\n--- YENİ ABONELİK EKLE ---")
    name = input("Abonelik/Servis Adı (örn: Netflix, ChatGPT): ").strip()
    if not name:
        print("[HATA] Servis adı boş bırakılamaz!")
        return

    print("\nKategori Seçin:")
    print("  1 - Streaming (Film, Dizi, Müzik, YouTube)")
    print("  2 - AI Tool (ChatGPT, Copilot, Claude, Yazılım)")
    print("  3 - Fitness (Spor Salonu, Yüzme)")
    cat_choice = input("Seçiminiz (1/2/3): ").strip()

    category_map = {"1": "streaming", "2": "ai_tool", "3": "fitness"}
    category = category_map.get(cat_choice, "streaming")

    try:
        monthly_cost = float(input("Aylık Ücret (TL): ").strip())
        if monthly_cost < 0:
            print("[HATA] Ücret negatif olamaz!")
            return
    except ValueError:
        print("[HATA] Lütfen geçerli bir sayısal ücret girin!")
        return

    currency = input("Para Birimi (Varsayılan TL): ").strip().upper() or "TL"

    try:
        renewal_day_str = input("Her ayın hangi günü yenileniyor? (1-31): ").strip() or "1"
        renewal_day = int(renewal_day_str)
        if not (1 <= renewal_day <= 31):
            renewal_day = 1
    except ValueError:
        renewal_day = 1

    dm.add_subscription(name, category, monthly_cost, currency, renewal_day)


def log_usage_flow(dm: DataManager):
    subs_df = dm.load_subscriptions_df()
    if subs_df.empty:
        print("\n[UYARI] Önce kayıtlı bir abonelik eklemelisiniz.\n")
        return

    print("\n--- KULLANIM KAYDI GİR ---")
    print("Mevcut Abonelikler:", ", ".join(subs_df["name"].tolist()))
    name = input("Hangi servis için kullanım gireceksiniz?: ").strip()

    try:
        amount = float(input("Kullanım miktarı (Saat veya Ziyaret sayısı): ").strip())
        if amount <= 0:
            print("[HATA] Miktar 0'dan büyük olmalıdır!")
            return
    except ValueError:
        print("[HATA] Geçersiz miktar girdiniz!")
        return

    date_input = input("Tarih (YYYY-AA-GG, bugün için Enter): ").strip() or None
    dm.log_usage(name, amount, date_input)


def run_analysis_flow(engine: AnalyticsEngine):
    import pandas as pd
    audit_df = engine.perform_full_audit()
    if audit_df.empty:
        print("\n[UYARI] Analiz edilecek abonelik verisi yok.\n")
        return

    kpi = engine.get_summary_kpi(audit_df)
    urgent_alerts = engine.get_urgent_renewal_alerts(audit_df, days_threshold=3)

    print("\n" + "=" * 78)
    print("                   📊 AKILLI SUBAUDIT ANALİZ RAPORU")
    print("=" * 78)
    print(f"Toplam Servis: {kpi['total_services']} Adet | Toplam Aylık Yük: {kpi['total_monthly']:.2f} TL | Yıllık Yük: {kpi['total_annual']:.2f} TL")
    print(f"🚨 Acil İptal Önerilen: {kpi['cancel_count']} Servis | 💰 Kurtarılabilir Yıllık Bütçe: {kpi['potential_annual_savings']:.2f} TL/Yıl")
    print(f"⭐ En Verimli Yatırım: {kpi['best_service']} | ⚠️ En Zararlı Sızıntı: {kpi['worst_service']}")
    print("-" * 78)

    # Kategori Bütçe Kotaları Özeti
    cat_budgets = engine.get_category_budget_analysis(audit_df)
    print("\n🎯 KATEGORİ BÜTÇE KOTALARI & DOLULUK ORANLARI:")
    for cb in cat_budgets:
        over_msg = f"(+{cb['overrun']:.1f} TL AŞIM!)" if cb['overrun'] > 0 else f"({cb['remaining']:.1f} TL Kalan)"
        print(f"   • {cb['label']:<34} | Harcanan: {cb['spend']:>6.1f} / {cb['limit']:>6.1f} TL (%{cb['ratio_pct']:>3.0f}) [{cb['status']}] {over_msg}")
    print("-" * 78)

    if urgent_alerts["critical_count"] > 0:
        print("\n🚨 ╔═══════════════════════════════════════════════════════════════════════╗")
        print(f"   ║ ⚠️  ACİL FATURA YENİLENME ALARMI ({urgent_alerts['critical_count']} Servis)                         ║")
        print("   ╚═══════════════════════════════════════════════════════════════════════╝")
        print("   Analiz motoru aşağıdaki servisleri İPTAL etmenizi öneriyor!")
        print(f"   Kartınızdan çekilmeden iptal ederseniz anında +{urgent_alerts['immediate_monthly_savings']:.2f} TL tasarruf edersiniz:")
        for al in urgent_alerts["critical_alerts"]:
            print(f"   • [{al['urgency_label']}] {al['name']} - {al['display_cost']} (Kalan Gün: {al['days_until_renewal']})")
            print(f"     ↳ Neden: {al['rec_detail']}")
        print("   " + "-" * 72)

    print(f"\n{'Servis Adı':<16} | {'Aylık':<18} | {'Kullanım':<10} | {'Birim Maliyet':<15} | {'Karar':<10}")
    print("-" * 78)
    for _, r in audit_df.iterrows():
        usage_str = f"{r['total_usage']:.1f} {r['unit']}"
        cost_str = r.get("display_cost", f"{r['monthly_cost']:>6.1f} TL")
        cpu_val = r["cost_per_unit"]
        cpu_str = f"{cpu_val:.1f} TL" if pd.notna(cpu_val) else "Kullanım Yok"
        print(f"{r['name']:<16} | {cost_str:<18} | {usage_str:<10} | {cpu_str:<15} | [{r['recommendation']}]")
        print(f"   ↳ Tavsiye Notu: {r['rec_detail']}")
        alts = engine.get_subscription_alternatives(r['name'], r['monthly_cost'], r['category'], r['total_usage'], r['recommendation'])
        if alts:
            best_alt = alts[0]
            print(f"   💡 Akıllı Alternatif: [{best_alt['badge']}] {best_alt['name']} ➔ Tasarruf: +{best_alt['monthly_savings']:.1f} TL/ay")
            print(f"      ↳ Gerekçe: {best_alt['rationale']}")

    # 📦 Çapraz Paket (Bundle) & Konsolidasyon Fırsatları
    bundles = engine.get_bundle_optimizations(audit_df)
    if bundles:
        print("\n📦 ÇAPRAZ PAKET (BUNDLE) & KONSOLİDASYON TASARRUF FIRSATLARI:")
        for b in bundles:
            print(f"   • [{b['badge']}] {b['title']}")
            print(f"     Net Tasarruf: +{b['monthly_savings']:.1f} TL/ay (+{b['annual_savings']:,.0f} TL/yıl)")
            print(f"     Aksiyon: '{b['sub_to_cancel']}' iptal et ➔ '{b['sub_to_keep']}' paketini kullan ({b['deal_name']})")
            print(f"     Gerekçe: {b['rationale']}")
    print("=" * 78 + "\n")


def open_dashboard_flow(engine: AnalyticsEngine, visualizer: DashboardVisualizer):
    audit_df = engine.perform_full_audit()
    if audit_df.empty:
        print("\n[UYARI] Gösterge paneli için yeterli veri bulunmuyor.\n")
        return

    trend_df = engine.generate_trend_simulation(audit_df, months=6)
    print("\n[BİLGİ] Matplotlib Gösterge Paneli açılıyor ve 'dashboard_report.png' olarak kaydediliyor...")
    visualizer.plot_dashboard(audit_df, trend_df)


def delete_subscription_flow(dm: DataManager):
    print("\n--- ABONELİK SİL ---")
    name = input("Silinecek aboneliğin tam adını girin: ").strip()
    if not name:
        return
    confirm = input(f"'{name}' aboneliğini ve tüm geçmiş kayıtlarını silmek istediğinize emin misiniz? (e/h): ").strip().lower()
    if confirm in ["e", "evet", "y", "yes"]:
        dm.delete_subscription(name)


def generate_pdf_flow(engine: AnalyticsEngine, dm: DataManager):
    from pdf_generator import ExecutiveReportGenerator
    from currency_service import CurrencyService

    audit_df = engine.perform_full_audit()
    kpi = engine.get_summary_kpi(audit_df)
    cs = CurrencyService(dm)
    rate_info = cs.get_source_info()

    pdf_gen = ExecutiveReportGenerator()
    out_file = "Smart_SubAudit_Yonetici_Raporu.pdf"
    print("\n[BİLGİ] ReportLab ile A4 resmi yönetici finans raporu üretiliyor...")
    pdf_gen.build_pdf(audit_df, kpi, rate_info, out_file)
    print(f"[BAŞARILI] PDF Raporunuz hazır: {os.path.abspath(out_file)}\n")


def run_ml_prediction_flow(engine: AnalyticsEngine):
    audit_df = engine.perform_full_audit()
    if audit_df.empty:
        print("\n[UYARI] Tahmin yapılacak abonelik verisi bulunmuyor.\n")
        return

    print("\n" + "=" * 80)
    print("      🤖 MAKİNE ÖĞRENMESİ İLE GELECEK AY KULLANIM TAHMİNİ (SCIKIT-LEARN)")
    print("=" * 80)
    print("Geçmiş kullanım kayıtları zaman serisi lineer regresyonu ile taranıyor...\n")

    predictions = engine.get_ml_predictions(audit_df)
    for p in predictions:
        print(f"📌 {p['name']} ({p['category']}) - Aylık Bütçe: {p['monthly_cost']:.1f} TL")
        print(f"   • Model: {p['model_name']} (R²: {p['r2_score']}) | Risk: {p['risk_level']}")
        curr_cpu_str = f"{p['current_cpu']:.1f} TL/{p['unit']}" if p['current_cpu'] != float('inf') else "Kullanım Yok"
        pred_cpu_str = f"{p['predicted_cpu']:.1f} TL/{p['unit']}" if p['predicted_cpu'] != float('inf') else "Sonsuz"
        print(f"   • Tüketim: Mevcut {p['current_usage']:.1f} {p['unit']} ➔ Tahmini {p['predicted_usage']:.1f} {p['unit']} ({p['trend_direction']})")
        print(f"   • Birim Maliyet: {curr_cpu_str} ➔ {pred_cpu_str}")
        print(f"   ↳ AI Notu: {p['insight_message']}")
        print("-" * 80)
    print()


def manage_category_budgets_flow(dm: DataManager, engine: AnalyticsEngine):
    audit_df = engine.perform_full_audit()
    cat_budgets = engine.get_category_budget_analysis(audit_df)

    print("\n" + "=" * 78)
    print("           🎯 KATEGORİ BAZLI BÜTÇE KOTALARI & HARCAMA LİMİTLERİ")
    print("=" * 78)
    for idx, cb in enumerate(cat_budgets, start=1):
        over_msg = f"(+{cb['overrun']:.1f} TL AŞIM!)" if cb['overrun'] > 0 else f"({cb['remaining']:.1f} TL Kalan)"
        print(f"  [{idx}] {cb['label']:<32} | Kota: {cb['limit']:>6.1f} TL | Harcanan: {cb['spend']:>6.1f} TL (%{cb['ratio_pct']:>3.0f}) [{cb['status']}] {over_msg}")
    print("-" * 78)

    print("Kotasını güncellemek istediğiniz kategoriyi seçin (veya çıkmak için ENTER):")
    cat_choice = input("Seçiminiz (1/2/3): ").strip()
    idx_map = {"1": "streaming", "2": "ai_tool", "3": "fitness"}

    if cat_choice in idx_map:
        cat_key = idx_map[cat_choice]
        try:
            new_limit = float(input(f"'{cat_key}' kategorisi için yeni aylık limit (TL): ").strip())
            if new_limit <= 0:
                print("[HATA] Bütçe limiti 0'dan büyük olmalıdır!")
                return
            dm.set_category_budget(cat_key, new_limit)
            print(f"[BAŞARILI] '{cat_key}' kategorisinin aylık bütçe limiti {new_limit:.1f} TL olarak güncellendi!\n")
        except ValueError:
            print("[HATA] Lütfen geçerli bir sayısal değer girin!\n")
    else:
        print("[BİLGİ] Değişiklik yapılmadı.\n")


def run_heatmap_flow(engine: AnalyticsEngine):
    audit_df = engine.perform_full_audit()
    sub_names = ["Tüm Servisler"] + (audit_df["name"].tolist() if not audit_df.empty else [])

    print("\n" + "=" * 78)
    print("    📅 GITHUB TARZI ABONELİK KULLANIM ISI HARİTASI & ALIŞKANLIK ANALİZİ")
    print("=" * 78)
    for idx, s in enumerate(sub_names, start=1):
        print(f"  [{idx}] {s}")

    sel = input("\nİncelemek istediğiniz servisi seçin (1-N, varsayılan 1): ").strip()
    sel_sub = "Tümü"
    if sel.isdigit() and 1 <= int(sel) <= len(sub_names):
        chosen = sub_names[int(sel) - 1]
        sel_sub = "Tümü" if chosen == "Tüm Servisler" else chosen

    heat_data = engine.get_activity_heatmap_data(sub_name=sel_sub, days=60)

    print("\n" + "-" * 78)
    print(f"📌 {sel_sub.upper()} ALIŞKANLIK METRİKLERİ (Son {heat_data['total_days']} Günlük Analiz):")
    print(f"   • 🔥 Kesintisiz Seri: {heat_data['current_streak']} Gün (Rekor: {heat_data['longest_streak']} gün üst üste)")
    print(f"   • ⚡ Aktif Gün Sayısı: {heat_data['active_days']} / {heat_data['total_days']} Gün (%{heat_data['activity_rate_pct']:.0f} Aktiflik)")
    print(f"   • 🏆 En Yoğun Gün: {heat_data['busiest_day']} ({heat_data['busiest_day_amount']:.1f} saat/ziyaret)")
    print(f"   • 📊 Zaman Dağılımı: %{heat_data['weekend_ratio_pct']:.0f} Hafta Sonu / %{100 - heat_data['weekend_ratio_pct']:.0f} Hafta İçi")
    print("-" * 78)

    # Mini ASCII takvim ısı haritası
    print("\n📅 Son 4 Haftanın Günlük Aktivite Matrisi (■: Aktif, ·: Boş Gün):")
    days_data = heat_data["days"]
    recent_days = days_data[-28:] if len(days_data) >= 28 else days_data
    short_days = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]

    # Hafta hafta grupla
    weeks_grid = {i: [] for i in range(7)}
    for r in recent_days:
        symbol = "■" if r["amount"] > 0 else "·"
        weeks_grid[r["weekday"]].append(symbol)

    for w_idx in range(7):
        row_str = "  ".join(weeks_grid[w_idx])
        print(f"  {short_days[w_idx]:<4} | {row_str}")
    print("       ↳ (En sağdaki sütun: Mevcut hafta)\n")

    print("💡 Yapay Zeka Alışkanlık Reçetesi:")
    for ins in heat_data["insights"]:
        print(f"   🎯 {ins}")
    print("=" * 78 + "\n")


def run_bundle_optimizer_flow(engine: AnalyticsEngine, dm: DataManager):
    audit_df = engine.perform_full_audit()
    if audit_df.empty:
        print("\n[UYARI] Analiz edilecek kayıtlı abonelik bulunmuyor.\n")
        return

    print("\n" + "=" * 78)
    print("      📦 ÇAPRAZ PAKET (BUNDLE) & BİRLEŞTİRME TASARRUFU MOTORU")
    print("=" * 78)
    print("Sistem sepetinizi Türkiye pazarındaki ortak paketler ve çakışmalara göre tarıyor...\n")

    deals = engine.get_bundle_optimizations(audit_df)
    if not deals:
        print("✅ Harika haber! Sepetinizde birbirini tekrarlayan veya ortak paketle ikame")
        print("   edilebilecek gereksiz bir çakışma bulunamadı.")
        print("=" * 78 + "\n")
        return

    total_m_save = sum(d["monthly_savings"] for d in deals)
    total_y_save = sum(d["annual_savings"] for d in deals)
    print(f"🔥 {len(deals)} ADET KONSOLİDASYON & PAKET FIRSATI YAKALANDI!")
    print(f"💰 Toplam Potansiyel Tasarruf: +{total_m_save:.1f} TL/ay (+{total_y_save:,.0f} TL/yıl)\n")

    for idx, d in enumerate(deals, start=1):
        print(f"[{idx}] ─────────────────────────────────────────────────────────────")
        print(f"    🏷️  {d['title']} ({d['badge']})")
        print(f"    💰 Net Tasarruf : +{d['monthly_savings']:.1f} TL / ay  (Yıllık: +{d['annual_savings']:,.0f} TL)")
        print(f"    🎁 Ortak Paket  : {d['deal_name']}")
        print(f"    ❌ Kapatılacak   : {d['sub_to_cancel']}")
        print(f"    ✅ Korunacak     : {d['sub_to_keep']}")
        print(f"    💡 Gerekçe       : {d['rationale']}")
        print()

    print("=" * 78)
    cancel_choice = input("Çakışan bir servisi şimdi iptal etmek ister misiniz? (Servis Adı veya Enter): ").strip()
    if cancel_choice:
        exists = any(cancel_choice.lower() == str(name).lower() for name in audit_df["name"].tolist())
        if exists:
            dm.delete_subscription(cancel_choice)
            print(f"\n[BAŞARILI] '{cancel_choice}' iptal edildi! Bütçeniz koruma altına alındı.\n")
        else:
            print(f"\n[UYARI] '{cancel_choice}' isimli aktif bir abonelik bulunamadı.\n")


def main():
    dm = DataManager()
    engine = AnalyticsEngine(dm)
    visualizer = DashboardVisualizer()

    print_banner()

    while True:
        print_menu()
        choice = input("Lütfen bir işlem seçin (1-11 veya Q): ").strip().upper()

        if choice == "1":
            list_subscriptions(dm)
        elif choice == "2":
            add_subscription_flow(dm)
        elif choice == "3":
            log_usage_flow(dm)
        elif choice == "4":
            run_analysis_flow(engine)
        elif choice == "5":
            open_dashboard_flow(engine, visualizer)
        elif choice == "6":
            delete_subscription_flow(dm)
        elif choice == "7":
            generate_pdf_flow(engine, dm)
        elif choice == "8":
            run_ml_prediction_flow(engine)
        elif choice == "9":
            manage_category_budgets_flow(dm, engine)
        elif choice == "10":
            run_heatmap_flow(engine)
        elif choice == "11":
            run_bundle_optimizer_flow(engine, dm)
        elif choice in ["Q", "QUIT", "EXIT", "ÇIKIŞ"]:
            print("\nSmart SubAudit'ten çıkılıyor. Bütçeniz güvende kalsın! İyi günler.\n")
            sys.exit(0)
        else:
            print("\n[HATA] Geçersiz seçenek! Lütfen menüdeki numaralardan birini seçin.\n")



if __name__ == "__main__":
    main()

