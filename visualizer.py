"""
SmartSubAudit - visualizer.py
Veri Görselleştirme Modülü (Matplotlib):
- 4 Panelli Analitik Gösterge Paneli (2x2 Subplots)
- Panel 1: Birim Kullanım Başına Maliyet Karşılaştırması (Yatay Bar)
- Panel 2: Gelecek 6 Ay Kümülatif Maliyet vs Tasarruf Simülasyonu (Çizgi Grafik)
- Panel 3: Risk & Değer Matrisi (Scatter Plot - 4 Kadranlı Karar Haritası)
- Panel 4: Yıllık İsraf & Kurtarılabilecek Bütçe Sıralaması (Bar Grafik)
"""

import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class DashboardVisualizer:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            self.output_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.output_dir = output_dir

    def plot_dashboard(self, audit_df: pd.DataFrame, trend_df: pd.DataFrame, save_path: str = None):
        """
        Kapsamlı 4 panelli görsel gösterge panelini çizer ve ekranda gösterir.
        """
        if audit_df.empty:
            print("[UYARI] Görselleştirilecek veri bulunamadı!")
            return

        # Modern koyu tema estetiği
        plt.style.use("seaborn-v0_8-darkgrid" if "seaborn-v0_8-darkgrid" in plt.style.available else "default")
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.patch.set_facecolor("#1e222d")

        # Renk paletleri
        color_map = {
            "TUT": "#2ecc71",       # Zümrüt Yeşili
            "GOZLE": "#f1c40f",     # Sarı/Altın
            "DUSUR": "#e67e22",     # Turuncu
            "IPTAL_ET": "#e74c3c"   # Kırmızı
        }

        # ----------------------------------------------------
        # Panel 1: Birim Kullanım Başına Maliyet (Sol Üst)
        # ----------------------------------------------------
        ax1 = axes[0, 0]
        ax1.set_facecolor("#282c37")

        # Sıralama: Birim maliyete göre
        plot_df = audit_df.copy()
        # NaN veya sonsuz değerleri grafikte göstermek için makul bir tavan belirle
        finite_series = plot_df["cost_per_unit"].replace([np.inf, -np.inf], np.nan)
        max_finite = finite_series.max()
        if pd.isna(max_finite) or max_finite <= 0:
            max_finite = 100.0
        plot_df["display_cpu"] = finite_series.fillna(max_finite * 1.5)

        colors1 = [color_map.get(rec, "#95a5a6") for rec in plot_df["recommendation"]]
        bars1 = ax1.barh(plot_df["name"], plot_df["display_cpu"], color=colors1, edgecolor="#ffffff", alpha=0.85)

        ax1.set_title("1. Birim Kullanım Başı Maliyet (TL / Birim)", fontsize=13, fontweight="bold", color="#ffffff", pad=12)
        ax1.set_xlabel("Maliyet (TL/Saat veya TL/Ziyaret)", fontsize=10, color="#dcdde1")
        ax1.tick_params(colors="#ffffff", labelsize=10)
        ax1.invert_yaxis()  # En üstte ilk servis

        # Çubukların üstüne değer yazma
        for bar, raw_val, rec in zip(bars1, plot_df["cost_per_unit"], plot_df["recommendation"]):
            w = bar.get_width()
            text = f"{raw_val:.1f} TL" if np.isfinite(raw_val) else "Hiç kullanılmadı (0)"
            ax1.text(w + 1, bar.get_y() + bar.get_height() / 2, f" {text} [{rec}]",
                     va="center", ha="left", color="#ffffff", fontsize=9, fontweight="bold")

        # ----------------------------------------------------
        # Panel 2: 6 Aylık Finansal Yük & Tasarruf Projeksiyonu (Sağ Üst)
        # ----------------------------------------------------
        ax2 = axes[0, 1]
        ax2.set_facecolor("#282c37")

        if not trend_df.empty:
            ax2.plot(trend_df["Month"], trend_df["Mevcut_Durum"], marker="o", color="#e74c3c",
                     linewidth=2.5, label="Mevcut Durum (Müdahalesiz)")
            ax2.plot(trend_df["Month"], trend_df["Optimize_Edilmis"], marker="s", color="#2ecc71",
                     linewidth=2.5, label="Optimize Durum (Smart SubAudit)")
            ax2.fill_between(trend_df["Month"], trend_df["Mevcut_Durum"], trend_df["Optimize_Edilmis"],
                             color="#2ecc71", alpha=0.2, label="Kümülatif Net Tasarruf Alanı")

            ax2.set_title("2. Kümülatif 6 Aylık Bütçe Projeksiyonu", fontsize=13, fontweight="bold", color="#ffffff", pad=12)
            ax2.set_ylabel("Kümülatif Harcama (TL)", fontsize=10, color="#dcdde1")
            ax2.tick_params(colors="#ffffff", labelsize=10)
            ax2.legend(loc="upper left", facecolor="#1e222d", edgecolor="#ffffff", labelcolor="#ffffff", fontsize=9)

        # ----------------------------------------------------
        # Panel 3: Risk ve Değer Matrisi (Sol Alt - Scatter Plot)
        # ----------------------------------------------------
        ax3 = axes[1, 0]
        ax3.set_facecolor("#282c37")

        x = audit_df["monthly_cost"]
        y = audit_df["total_usage"]
        point_colors = [color_map.get(rec, "#3498db") for rec in audit_df["recommendation"]]

        scatter = ax3.scatter(x, y, s=200, c=point_colors, edgecolors="#ffffff", linewidth=1.5, alpha=0.9, zorder=5)

        # Servis isimlerini noktaların yanına yerleştir
        for _, r in audit_df.iterrows():
            ax3.annotate(
                r["name"],
                (r["monthly_cost"], r["total_usage"]),
                textcoords="offset points",
                xytext=(8, 5),
                ha="left",
                color="#f5f6fa",
                fontsize=9,
                fontweight="bold"
            )

        # Kadran çizgileri (Maliyet ve Kullanım medyanları)
        mid_cost = x.median() if not x.empty else 200
        mid_usage = y.median() if not y.empty else 5
        ax3.axvline(mid_cost, color="#7f8c8d", linestyle="--", alpha=0.6)
        ax3.axhline(mid_usage, color="#7f8c8d", linestyle="--", alpha=0.6)

        ax3.set_title("3. Değer & Risk Matrisi (Aylık Ücret vs Kullanım Miktarı)", fontsize=13, fontweight="bold", color="#ffffff", pad=12)
        ax3.set_xlabel("Aylık Ücret (TL)", fontsize=10, color="#dcdde1")
        ax3.set_ylabel("Toplam Kullanım (Saat/Ziyaret)", fontsize=10, color="#dcdde1")
        ax3.tick_params(colors="#ffffff", labelsize=10)

        # ----------------------------------------------------
        # Panel 4: Yıllık İsraf & Tasarruf Potansiyeli (Sağ Alt)
        # ----------------------------------------------------
        ax4 = axes[1, 1]
        ax4.set_facecolor("#282c37")

        waste_df = audit_df[audit_df["annual_waste"] > 0].copy()
        if not waste_df.empty:
            waste_df.sort_values(by="annual_waste", ascending=True, inplace=True)
            w_bars = ax4.barh(waste_df["name"], waste_df["annual_waste"], color="#e74c3c", edgecolor="#ffffff", alpha=0.85)
            ax4.set_title("4. İptal/Düşürme İle Yıllık Cepte Kalacak Tutar (TL/Yıl)", fontsize=13, fontweight="bold", color="#ffffff", pad=12)
            ax4.set_xlabel("Kurtarılabilecek Tutar (TL)", fontsize=10, color="#dcdde1")
            ax4.tick_params(colors="#ffffff", labelsize=10)

            for b in w_bars:
                val = b.get_width()
                ax4.text(val + 50, b.get_y() + b.get_height() / 2, f"{val:.0f} TL/yıl",
                         va="center", ha="left", color="#ffffff", fontsize=9, fontweight="bold")
        else:
            ax4.text(0.5, 0.5, "Tüm abonelikleriniz verimli!\nKurtarılacak israf bulunamadı.",
                     va="center", ha="center", color="#2ecc71", fontsize=12, fontweight="bold")
            ax4.set_title("4. Yıllık İsraf Analizi", fontsize=13, fontweight="bold", color="#ffffff", pad=12)
            ax4.tick_params(colors="#ffffff")

        plt.suptitle("SMART SUBAUDIT - ABONELIK & MALIYET DENETLEME GOSTERGE PANELI",
                     fontsize=15, fontweight="bold", color="#f5f6fa", y=0.98)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        # Dosyaya kaydet
        if save_path is None:
            save_path = os.path.join(self.output_dir, "dashboard_report.png")
        plt.savefig(save_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
        print(f"[BAŞARILI] Gösterge paneli görseli kaydedildi: {save_path}")

        # Ekranda interaktif göster
        plt.show()
