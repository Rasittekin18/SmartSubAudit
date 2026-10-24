"""
SmartSubAudit - pdf_generator.py
Kurumsal PDF Finans & Yönetici Raporu Üretici (ReportLab 5.0):
- Türkçe karakter desteği (Arial & Arial-Bold TrueType Font)
- Şık Yönetici Başlığı ve Meta Veri Bloğu
- 4'lü Finansal KPI Özet Kartları
- Renk Kodlu ve Karar Rozetli Detaylı Abonelik Tablosu
- Stratejik Tasarruf ve Eylem Reçetesi
- Bellekte (in-memory) BytesIO ve Dosyaya Kaydetme Desteği
"""

import os
import io
from datetime import datetime
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class ExecutiveReportGenerator:
    def __init__(self):
        self._setup_fonts()

    def _setup_fonts(self):
        """Türkçe karakterleri eksiksiz destekleyen sistem fontlarını kaydeder."""
        font_dir = "C:/Windows/Fonts"
        arial_path = os.path.join(font_dir, "arial.ttf")
        arial_bd_path = os.path.join(font_dir, "arialbd.ttf")

        if os.path.exists(arial_path):
            try:
                pdfmetrics.registerFont(TTFont("CustomArial", arial_path))
                self.font_normal = "CustomArial"
            except Exception:
                self.font_normal = "Helvetica"
        else:
            self.font_normal = "Helvetica"

        if os.path.exists(arial_bd_path):
            try:
                pdfmetrics.registerFont(TTFont("CustomArial-Bold", arial_bd_path))
                self.font_bold = "CustomArial-Bold"
            except Exception:
                self.font_bold = "Helvetica-Bold"
        else:
            self.font_bold = "Helvetica-Bold"

    def build_pdf(self, audit_df: pd.DataFrame, kpi: dict, currency_info: dict = None, output_path: str = None) -> bytes:
        """
        Kapsamlı A4 formatında resmi yönetici finans raporu üretir.
        output_path verilirse dosyaya kaydeder, her halükarda PDF bytes verisi döner.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm
        )

        elements = []
        styles = getSampleStyleSheet()

        # Özel Tipografi Stilleri
        style_title = ParagraphStyle(
            "DocTitle",
            fontName=self.font_bold,
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a")
        )

        style_subtitle = ParagraphStyle(
            "DocSubTitle",
            fontName=self.font_normal,
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b")
        )

        style_meta = ParagraphStyle(
            "MetaText",
            fontName=self.font_normal,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569")
        )

        style_section_title = ParagraphStyle(
            "SectionTitle",
            fontName=self.font_bold,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6
        )

        style_cell = ParagraphStyle(
            "TableCell",
            fontName=self.font_normal,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#1e293b")
        )

        style_cell_bold = ParagraphStyle(
            "TableCellBold",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a")
        )

        style_th = ParagraphStyle(
            "TableHead",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=colors.white
        )

        # -------------------------------------------------------------
        # 1. BAŞLIK VE KURUMSAL HEADER
        # -------------------------------------------------------------
        header_text = """
        <b>SMART SUBAUDIT</b> — YÖNETİCİ FİNANS VE MALİYET RAPORU
        """
        sub_text = "Abonelik & Birim Kullanım Başına Maliyet (Cost-per-Use) Denetleme ve Bütçe Tasarruf Özeti"
        elements.append(Paragraph(header_text, style_title))
        elements.append(Paragraph(sub_text, style_subtitle))
        elements.append(Spacer(1, 8))

        # Meta Bilgi Çubuğu (Tarih, Rapor ID, Döviz Kurları)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        usd_str = f"{currency_info['usd_try']:.2f} TL" if currency_info else "49.68 TL"
        eur_str = f"{currency_info['eur_try']:.2f} TL" if currency_info else "55.72 TL"

        meta_info = f"<b>Rapor Tarihi:</b> {now_str} &nbsp;|&nbsp; <b>Döviz Kurları:</b> USD: {usd_str} , EUR: {eur_str} &nbsp;|&nbsp; <b>Durum:</b> Resmi Analiz"
        elements.append(Paragraph(meta_info, style_meta))
        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=12))

        # -------------------------------------------------------------
        # 2. ÜST DÜZEY KPI KARTLARI TABLOSU (4 SÜTUN)
        # -------------------------------------------------------------
        total_m = kpi.get("total_monthly", 0.0)
        total_a = kpi.get("total_annual", 0.0)
        pot_s = kpi.get("potential_annual_savings", 0.0)
        canc_c = kpi.get("cancel_count", 0)

        kpi_data = [
            [
                Paragraph("<b>TOPLAM AYLIK YÜK</b>", style_meta),
                Paragraph("<b>YILLIK PROJEKSİYON</b>", style_meta),
                Paragraph("<b>KURTARILABİLİR İSRAF</b>", style_meta),
                Paragraph("<b>RİSKLİ / İPTAL LİSTESİ</b>", style_meta)
            ],
            [
                Paragraph(f"<b>{total_m:,.2f} TL</b>", style_title),
                Paragraph(f"<b>{total_a:,.2f} TL</b>", style_title),
                Paragraph(f"<font color='#16a34a'><b>+{pot_s:,.2f} TL</b></font>", style_title),
                Paragraph(f"<font color='#dc2626'><b>{canc_c} Servis</b></font>", style_title)
            ],
            [
                Paragraph("Aktif aylık abonelikler", style_meta),
                Paragraph("12 aylık kümülatif maliyet", style_meta),
                Paragraph("Yıllık cebe kalacak bütçe", style_meta),
                Paragraph("Acil eylem önerilen servisler", style_meta)
            ]
        ]

        kpi_table = Table(kpi_data, colWidths=[4.5 * cm, 4.5 * cm, 4.8 * cm, 4.2 * cm])
        kpi_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------
        # 3. DETAYLI ABONELİK & MALİYET DENETİM TABLOSU
        # -------------------------------------------------------------
        elements.append(Paragraph("Abonelik Portföyü ve Birim Kullanım Denetimi", style_section_title))

        if audit_df.empty:
            elements.append(Paragraph("<i>Kayıtlı abonelik bulunmamaktadır.</i>", style_cell))
        else:
            table_rows = [
                [
                    Paragraph("Servis Adı", style_th),
                    Paragraph("Kategori", style_th),
                    Paragraph("Aylık Tutar", style_th),
                    Paragraph("Kullanım", style_th),
                    Paragraph("Birim Maliyet", style_th),
                    Paragraph("Karar", style_th),
                    Paragraph("Yıllık İsraf", style_th)
                ]
            ]

            for _, r in audit_df.iterrows():
                rec = r["recommendation"]
                # Karar Rozet Rengi
                if rec == "TUT":
                    rec_html = "<font color='#16a34a'><b>[TUT]</b></font>"
                elif rec == "GOZLE":
                    rec_html = "<font color='#d97706'><b>[GÖZLE]</b></font>"
                elif rec == "DUSUR":
                    rec_html = "<font color='#ea580c'><b>[DÜŞÜR]</b></font>"
                else:
                    rec_html = "<font color='#dc2626'><b>[İPTAL ET]</b></font>"

                cost_text = r.get("display_cost", f"{r['monthly_cost']:.1f} TL")
                cpu_text = f"{r['cost_per_unit']:.1f} TL/{r['unit']}" if pd.notna(r['cost_per_unit']) and r['cost_per_unit'] > 0 else "0 Kullanım"
                waste_text = f"{r['annual_waste']:,.0f} TL" if r["annual_waste"] > 0 else "-"

                table_rows.append([
                    Paragraph(f"<b>{r['name']}</b>", style_cell_bold),
                    Paragraph(str(r["category"]).upper(), style_cell),
                    Paragraph(cost_text, style_cell),
                    Paragraph(f"{r['total_usage']:.1f} {r['unit']}", style_cell),
                    Paragraph(cpu_text, style_cell),
                    Paragraph(rec_html, style_cell),
                    Paragraph(waste_text, style_cell_bold)
                ])

            audit_table = Table(
                table_rows,
                colWidths=[3.6 * cm, 2.2 * cm, 3.1 * cm, 2.3 * cm, 2.7 * cm, 2.1 * cm, 2.0 * cm]
            )
            audit_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 1), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ]))
            elements.append(audit_table)

        elements.append(Spacer(1, 14))

        # -------------------------------------------------------------
        # 4. STRATEJİK YÖNETİCİ REÇETESİ VE EYLEM PLANI
        # -------------------------------------------------------------
        elements.append(Paragraph("Stratejik Optimizasyon ve Eylem Reçetesi", style_section_title))

        insights = []
        if not audit_df.empty:
            cancels = audit_df[audit_df["recommendation"] == "IPTAL_ET"]
            downgrades = audit_df[audit_df["recommendation"] == "DUSUR"]
            keeps = audit_df[audit_df["recommendation"] == "TUT"]

            if not cancels.empty:
                cancel_names = ", ".join(cancels["name"].tolist())
                total_c_waste = cancels["annual_waste"].sum()
                insights.append(f"• <b>Acil İptal Listesi:</b> {cancel_names} servisleri düşük/sıfır kullanım nedeniyle bütçede açık yaratmaktadır. Bu servislerin derhal iptal edilmesi halinde yıllık <b>+{total_c_waste:,.0f} TL</b> net nakit tasarrufu sağlanacaktır.")

            if not downgrades.empty:
                down_names = ", ".join(downgrades["name"].tolist())
                insights.append(f"• <b>Paket Düşürme Fırsatı:</b> {down_names} servisleri için mevcut kullanım hacmi tam paket fiyatını karşılamamaktadır. Aile planı, öğrenci paketi veya alt pakete geçilmesi önerilir.")

            if not keeps.empty:
                best_sub = keeps.iloc[0]["name"]
                insights.append(f"• <b>Maksimum Yatırım Getirisi:</b> '{best_sub}' servisi aktif olarak kullanılmakta olup saatlik/birim maliyeti piyasa standartlarının oldukça altındadır. Tutulması tavsiye edilir.")

            if not insights:
                insights.append("• Tebrikler! Tüm abonelikleriniz verimlilik eşiklerinin üzerinde kullanılmaktadır. Bütçe sızıntısı tespit edilmemiştir.")
        else:
            insights.append("• Henüz kayıtlı veri bulunmamaktadır.")

        for item in insights:
            elements.append(Paragraph(item, style_cell))
            elements.append(Spacer(1, 4))

        elements.append(Spacer(1, 14))
        elements.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#94a3b8"), spaceAfter=6))

        # Altbilgi (Footer)
        footer_text = f"Smart SubAudit v1.0 — Finansal Denetim & Raporlama Motoru — Oluşturulma: {now_str}"
        elements.append(Paragraph(footer_text, style_meta))

        # PDF Dokümanını Derle
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Dosya yoluna kaydet (opsiyonel)
        if output_path:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            print(f"[BAŞARILI] PDF Yönetici Raporu kaydedildi: {output_path}")

        return pdf_bytes
