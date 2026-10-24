"""
SmartSubAudit - app.py
Modern Web Arayüzü (Streamlit — Executive FinTech Dark Mode & Bento UI)
Tasarım İlhamı: Copilot Money, Raycast, Linear, Revolut Ultra
"""

import os
import sys
from datetime import date, datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import importlib

# UTF-8 Akış Desteği
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Modül hot-reload
import models
import data_manager
import analytics
import visualizer
import currency_service
import pdf_generator
import ml_predictor
import recommendation_engine

importlib.reload(models)
importlib.reload(data_manager)
importlib.reload(analytics)
importlib.reload(visualizer)
importlib.reload(currency_service)
importlib.reload(pdf_generator)
importlib.reload(ml_predictor)
importlib.reload(recommendation_engine)

from data_manager import DataManager
from analytics import AnalyticsEngine
from visualizer import DashboardVisualizer
from currency_service import CurrencyService
from pdf_generator import ExecutiveReportGenerator
from ml_predictor import UsagePredictor
from recommendation_engine import AlternativeAdvisor, BundleAdvisor

# --- 1. SAYFA KONFİGÜRASYONU ---
st.set_page_config(
    page_title="Smart SubAudit — Kurumsal Abonelik & Finans Denetleyicisi",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. LUXURY FINTECH OBSIDIAN DARK THEME (CSS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stMarkdown, p, div, span, button, input {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Arka Plan: Derin Gece & Radyal Işık Halesi */
    .stApp {
        background-color: #07090e !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.09) 0px, transparent 45%),
            radial-gradient(at 50% 100%, rgba(16, 185, 129, 0.06) 0px, transparent 50%),
            radial-gradient(at 90% 80%, rgba(56, 189, 248, 0.05) 0px, transparent 40%) !important;
        background-attachment: fixed !important;
        color: #f1f5f9 !important;
    }

    /* İnce Zarif Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.6);
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(99, 102, 241, 0.5);
    }

    /* Kenar Çubuğu (Sidebar) Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(11, 15, 25, 0.85) !important;
        backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
    }

    /* Bento Grid KPI Kartları */
    .kpi-card {
        background: linear-gradient(135deg, rgba(22, 27, 44, 0.7) 0%, rgba(15, 20, 32, 0.55) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 18px;
        padding: 22px 20px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.45);
        box-shadow: 0 20px 40px -10px rgba(99, 102, 241, 0.25), inset 0 1px 0 0 rgba(255, 255, 255, 0.15);
    }
    .kpi-top-glow {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    .glow-indigo { background: linear-gradient(90deg, #6366f1, #818cf8); }
    .glow-emerald { background: linear-gradient(90deg, #10b981, #34d399); }
    .glow-cyan { background: linear-gradient(90deg, #06b6d4, #38bdf8); }
    .glow-rose { background: linear-gradient(90deg, #f43f5e, #fb7185); }
    .glow-amber { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

    .kpi-title {
        color: #94a3b8;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }
    .kpi-value {
        color: #ffffff;
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .kpi-sub {
        font-size: 0.8rem;
        font-weight: 500;
        color: #94a3b8;
    }

    /* Modern Floating Pill Sekmeler (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px !important;
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        padding: 6px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
        margin-bottom: 24px !important;
    }
    .stTabs [data-baseweb="tab"] {
        height: 46px !important;
        border-radius: 11px !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0 20px !important;
        border: 1px solid transparent !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.3) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
        border: 1px solid rgba(99, 102, 241, 0.55) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3) !important;
    }

    /* Karar Rozetleri (Badges) */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .badge-tut {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.15);
    }
    .badge-gozle {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
        box-shadow: 0 0 12px rgba(245, 158, 11, 0.15);
    }
    .badge-dusur {
        background: rgba(249, 115, 22, 0.15);
        color: #fb923c;
        border: 1px solid rgba(249, 115, 22, 0.4);
        box-shadow: 0 0 12px rgba(249, 115, 22, 0.15);
    }
    .badge-iptal {
        background: rgba(244, 63, 94, 0.15);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.45);
        box-shadow: 0 0 16px rgba(244, 63, 94, 0.2);
    }

    /* Acil Fatura Alarmı Banner */
    .critical-alert-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.14) 0%, rgba(185, 28, 28, 0.22) 100%);
        border: 1px solid rgba(239, 68, 68, 0.45);
        border-radius: 18px;
        padding: 22px 24px;
        margin-bottom: 24px;
        box-shadow: 0 12px 36px 0 rgba(239, 68, 68, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(16px);
    }

    /* Reçete Kartları */
    .advice-card {
        background: linear-gradient(135deg, rgba(22, 27, 44, 0.7) 0%, rgba(15, 20, 32, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px 22px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        transition: all 0.25s ease;
    }
    .advice-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
        transform: translateY(-2px);
    }

    /* Bundle Optimizer Kartları */
    .bundle-banner {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(99, 102, 241, 0.18) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 18px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 12px 32px rgba(16, 185, 129, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(16px);
    }
    .bundle-item-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
        transition: all 0.2s ease;
    }
    .bundle-item-card:hover {
        border-color: rgba(52, 211, 153, 0.5);
    }


    /* Butonlar */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
        transition: all 0.2s ease !important;
        padding: 10px 20px !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.04) !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* Girdi Alanları */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background-color: rgba(15, 23, 42, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }

    /* Tablolar */
    [data-testid="stDataFrame"] {
        border-radius: 14px !important;
        overflow: hidden !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
</style>
""", unsafe_allow_html=True)


# --- 3. VERİ VE SERVİS BAŞLATMA ---
def get_managers():
    dm = DataManager()
    cs = CurrencyService(dm)
    engine = AnalyticsEngine(dm, cs)
    viz = DashboardVisualizer()
    pdf_gen = ExecutiveReportGenerator()
    return dm, cs, engine, viz, pdf_gen

dm, cs, engine, viz, pdf_gen = get_managers()


# --- 4. YAN MENÜ (SIDEBAR) ---
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:14px; margin-bottom:20px;">
        <div style="background: linear-gradient(135deg, #6366f1, #a855f7); width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; box-shadow: 0 6px 20px rgba(99,102,241,0.45);">
            💳
        </div>
        <div>
            <div style="font-size:1.2rem; font-weight:800; color:#fff; line-height:1.2; letter-spacing:-0.02em;">Smart SubAudit</div>
            <div style="font-size:0.75rem; color:#94a3b8; font-weight:500;">Birim Maliyet Denetleyicisi</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Sistem Bilgisi Telemetrisi
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;'>SİSTEM TELEMETRİSİ</p>", unsafe_allow_html=True)
    audit_data = engine.perform_full_audit()
    kpi = engine.get_summary_kpi(audit_data)
    urgent_alerts = engine.get_urgent_renewal_alerts(audit_data, days_threshold=3)

    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:14px 16px; margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.85rem;">
            <span style="color:#94a3b8;">Veritabanı:</span>
            <span style="color:#10b981; font-weight:700;">🟢 SQLite ACID</span>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.85rem;">
            <span style="color:#94a3b8;">Aktif Servis:</span>
            <b style="color:#fff;">{kpi['total_services']} adet</b>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:0.85rem;">
            <span style="color:#94a3b8;">Aylık Yük:</span>
            <b style="color:#fff;">{kpi['total_monthly']:.1f} ₺</b>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
            <span style="color:#94a3b8;">Kurtarılabilir:</span>
            <span style="color:#10b981; font-weight:800;">+{kpi['potential_annual_savings']:,.0f} ₺/yıl</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if urgent_alerts["critical_count"] > 0:
        st.markdown(f"""
        <div style="background: rgba(239, 68, 68, 0.18); border: 1px solid rgba(239, 68, 68, 0.45); border-radius: 12px; padding: 10px 14px; margin-bottom: 14px; display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.3rem;">🚨</span>
            <div>
                <div style="color:#f87171; font-weight:800; font-size:0.85rem;">{urgent_alerts['critical_count']} Acil İptal Çağrısı!</div>
                <div style="color:#cbd5e1; font-size:0.75rem;">Fatura yenilenmesine &le; 3 gün kaldı</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif urgent_alerts["upcoming_count"] > 0:
        st.markdown(f"""
        <div style="background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 12px; padding: 10px 14px; margin-bottom: 14px; display:flex; align-items:center; gap:10px;">
            <span style="font-size:1.3rem;">🔔</span>
            <div>
                <div style="color:#38bdf8; font-weight:800; font-size:0.85rem;">{urgent_alerts['upcoming_count']} Yaklaşan Fatura</div>
                <div style="color:#cbd5e1; font-size:0.75rem;">Önümüzdeki 3 gün içinde</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Canlı Döviz Kuru Widget'ı
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;'>CANLI DÖVİZ KURLARI</p>", unsafe_allow_html=True)
    rate_info = cs.get_source_info()
    st.markdown(f"""
    <div style="background: rgba(22, 27, 44, 0.7); padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); font-size: 0.85rem; margin-bottom: 10px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#cbd5e1;">🇺🇸 USD / TRY:</span>
            <b style="color:#10b981; font-size:0.95rem;">{rate_info['usd_try']:.2f} ₺</b>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
            <span style="color:#cbd5e1;">🇪🇺 EUR / TRY:</span>
            <b style="color:#38bdf8; font-size:0.95rem;">{rate_info['eur_try']:.2f} ₺</b>
        </div>
        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
            <span style="color:#cbd5e1;">🇬🇧 GBP / TRY:</span>
            <b style="color:#fbbf24; font-size:0.95rem;">{rate_info['gbp_try']:.2f} ₺</b>
        </div>
        <div style="font-size:0.72rem; color:#8b949e; border-top:1px solid rgba(255,255,255,0.06); padding-top:6px;">
            🟢 {rate_info['source']} ({rate_info['last_updated']})
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Kurları Canlı Güncelle", use_container_width=True):
        cs.get_rates(force_refresh=True)
        st.toast("Canlı kurlar başarıyla güncellendi!")
        st.rerun()

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# --- 5. ULTRA-SLEEK HERO HEADER ---
h_col1, h_col2 = st.columns([3.2, 1.3])

with h_col1:
    st.markdown("""
    <div style="margin-bottom: 18px;">
        <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.35); border-radius:20px; padding:4px 12px; margin-bottom:10px;">
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:#10b981; box-shadow:0 0 8px #10b981;"></span>
            <span style="color:#c7d2fe; font-size:0.75rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase;">Finansal Zeka & Tasarruf Motoru</span>
        </div>
        <h1 style="font-size: 2.3rem; font-weight: 900; color: #ffffff; margin: 0 0 6px 0; letter-spacing: -0.03em; line-height: 1.15;">
            Dijital Abonelik & Maliyet Denetleyicisi
        </h1>
        <p style="color: #94a3b8; font-size: 0.95rem; margin: 0; line-height: 1.5;">
            Aboneliklerinizi sadece fatura tutarıyla değil, <b>Birim Kullanım Başına Maliyet (Cost-per-Use)</b> ile analiz edin; gereksiz bütçe sızıntılarını erken tespit edin.
        </p>
    </div>
    """, unsafe_allow_html=True)

with h_col2:
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    # Hızlı PDF Rapor Butonu
    pdf_bytes = pdf_gen.build_pdf(audit_data, kpi, cs.get_source_info())
    st.download_button(
        label="📄 Resmi Finans Raporu İndir (.PDF)",
        data=pdf_bytes,
        file_name=f"Smart_SubAudit_Yonetici_Raporu_{date.today().strftime('%Y_%m_%d')}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )


# --- 5.1. ACİL FATURA YENİLENME ALARMI BANNER'I ---
if urgent_alerts["critical_count"] > 0:
    st.markdown(f"""
    <div class="critical-alert-box">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:12px;">
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="background:#ef4444; color:#fff; padding:4px 12px; border-radius:20px; font-size:0.75rem; font-weight:900; letter-spacing:0.05em; text-transform:uppercase; box-shadow:0 0 16px rgba(239,68,68,0.5);">🚨 ACİL TASARRUF ÇAĞRISI</span>
                <span style="color:#fca5a5; font-size:0.85rem; font-weight:600;">Otomatik Para Çekilme Alarmı</span>
            </div>
            <div style="background:rgba(239,68,68,0.25); border:1px solid rgba(239,68,68,0.5); border-radius:10px; padding:6px 14px; font-size:0.85rem; color:#fecaca;">
                Kurtarılacak Tutar: <b>+{urgent_alerts['immediate_monthly_savings']:,.1f} ₺ / ay</b> (Yıllık: <b>+{urgent_alerts['immediate_annual_savings']:,.0f} ₺</b>)
            </div>
        </div>
        <div style="font-size:1.15rem; font-weight:800; color:#ffffff; margin-bottom:6px;">
            ⚠️ Dikkat: {urgent_alerts['critical_count']} Adet Servisin Fatura Yenilenmesine 3 Günden Az Kaldı!
        </div>
        <div style="color:#e2e8f0; font-size:0.9rem; line-height:1.5; margin-bottom:14px;">
            Analiz motorumuz bu servisleri <b>yetersiz veya sıfır kullanım</b> nedeniyle bütçe israfı olarak tespit etti. Kartınızdan otomatik tahsil edilmeden önce iptal ederek hemen tasarruf edebilirsiniz.
        </div>
    </div>
    """, unsafe_allow_html=True)

    for alert in urgent_alerts["critical_alerts"]:
        alert_col1, alert_col2 = st.columns([3.5, 1.2])
        with alert_col1:
            st.markdown(f"""
            <div style="background:rgba(22, 27, 44, 0.85); border:1px solid rgba(239,68,68,0.4); border-left:5px solid #ef4444; border-radius:12px; padding:12px 18px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <div>
                        <b style="font-size:1.05rem; color:#fff;">{alert['name']}</b>
                        <span style="font-size:0.75rem; color:#94a3b8; margin-left:8px;">({alert['category']})</span>
                    </div>
                    <div>
                        <span style="background:#dc2626; color:#fff; font-size:0.75rem; font-weight:800; padding:3px 9px; border-radius:8px;">{alert['urgency_label']}</span>
                        <b style="color:#f87171; font-size:1rem; margin-left:8px;">{alert['display_cost']}</b>
                    </div>
                </div>
                <div style="color:#cbd5e1; font-size:0.85rem; line-height:1.4;">
                    🎯 <b>Gerekçe:</b> {alert['rec_detail']} (Toplam Kullanım: {alert['total_usage']:.1f} {alert['unit']})
                </div>
            </div>
            """, unsafe_allow_html=True)
        with alert_col2:
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            if st.button(f"🗑️ İptal Et ({alert['name']})", key=f"quick_del_{alert['name']}", type="primary", use_container_width=True):
                if dm.delete_subscription(alert['name']):
                    st.success(f"'{alert['name']}' iptal edildi! Ayda {alert['monthly_cost']:.1f} ₺ tasarruf sağlandı.")
                    st.rerun()

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

elif urgent_alerts["upcoming_count"] > 0:
    upcoming_names = ", ".join([s['name'] for s in urgent_alerts['upcoming_renewals']])
    st.markdown(f"""
    <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; padding: 12px 18px; margin-bottom: 20px; display:flex; align-items:center; gap:12px;">
        <span style="font-size:1.4rem;">🔔</span>
        <div style="font-size:0.88rem; color:#e0f2fe;">
            <b>Yaklaşan Fatura Hatırlatması:</b> Önümüzdeki 3 gün içinde <b>{urgent_alerts['upcoming_count']} aktif servisin</b> ({upcoming_names}) faturası yenilenecek.
            Analiz motoru kullanım oranlarınızı verimli bulduğu için bu servisleri tutmanızı öneriyor.
        </div>
    </div>
    """, unsafe_allow_html=True)


# --- 5.2. EXECUTIVE BENTO KPI GRID ---
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

with kpi_c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-top-glow glow-indigo"></div>
        <div class="kpi-header">
            <span class="kpi-title">Toplam Aylık Yük</span>
            <div class="kpi-icon-pill" style="color:#818cf8;">💳</div>
        </div>
        <div class="kpi-value">{kpi['total_monthly']:,.1f} <span style="font-size:1.1rem; color:#94a3b8; font-weight:600;">₺</span></div>
        <div class="kpi-sub">Yıllık Projeksiyon: <b style="color:#f1f5f9; margin-left:4px;">{kpi['total_annual']:,.0f} ₺</b></div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-top-glow glow-emerald"></div>
        <div class="kpi-header">
            <span class="kpi-title">Kurtarılabilir Yıllık Bütçe</span>
            <div class="kpi-icon-pill" style="color:#34d399;">💸</div>
        </div>
        <div class="kpi-value" style="color:#10b981;">+{kpi['potential_annual_savings']:,.0f} <span style="font-size:1.1rem; color:#34d399; font-weight:600;">₺</span></div>
        <div class="kpi-sub"><span style="color:#f87171; font-weight:700;">{kpi['cancel_count']} servis</span> optimizasyon listesinde</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-top-glow glow-cyan"></div>
        <div class="kpi-header">
            <span class="kpi-title">En Verimli Yatırım</span>
            <div class="kpi-icon-pill" style="color:#38bdf8;">🏆</div>
        </div>
        <div class="kpi-value" style="font-size:1.45rem; color:#f1f5f9;">{kpi['best_service']}</div>
        <div class="kpi-sub"><span style="color:#10b981; font-weight:700;">Maksimum getiri</span> / düşük saatlik maliyet</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-top-glow glow-rose"></div>
        <div class="kpi-header">
            <span class="kpi-title">En Tehlikeli Sızıntı</span>
            <div class="kpi-icon-pill" style="color:#fb7185;">🚨</div>
        </div>
        <div class="kpi-value" style="font-size:1.45rem; color:#fb7185;">{kpi['worst_service']}</div>
        <div class="kpi-sub"><span style="color:#f43f5e; font-weight:700;">Yüksek fatura</span> / sıfıra yakın kullanım</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)


# --- 6. MODERN FLOATING PILL TABS ---
tab_dash, tab_advice, tab_ml, tab_heatmap, tab_manage, tab_usage, tab_export = st.tabs([
    "📊 Analitik Dashboard",
    "💡 Tasarruf & Karar Reçetesi",
    "🤖 Gelecek Ay Tahmini (Mini ML)",
    "📅 Alışkanlık & Isı Haritası",
    "📋 Abonelik Yönetimi",
    "⏱️ Günlük Kullanım Girişi",
    "📥 Rapor & Dışa Aktarma"
])


# ==============================================================================
# TAB 1: ANALİTİK DASHBOARD
# ==============================================================================
with tab_dash:
    if audit_data.empty:
        st.info("Henüz analiz edilecek abonelik bulunmuyor. 'Abonelik Yönetimi' sekmesinden ekleyin.")
    else:
        row1_col1, row1_col2 = st.columns([1.1, 0.9])

        with row1_col1:
            st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:4px;'>1. Birim Kullanım Başına Maliyet (TL/Saat veya TL/Ziyaret)</h4>", unsafe_allow_html=True)
            st.caption("Düşük çubuklar verimli yatırımı, aşırı yüksek çubuklar ise para israfını temsil eder.")

            plot_df = audit_data.copy()
            plot_df.sort_values(by="cost_per_unit", ascending=True, inplace=True)
            plot_df["display_cpu"] = plot_df["cost_per_unit"].fillna(plot_df["monthly_cost"] * 1.5)

            color_discrete_map = {
                "TUT": "#10b981",
                "GOZLE": "#f59e0b",
                "DUSUR": "#f97316",
                "IPTAL_ET": "#f43f5e"
            }

            fig_bar = px.bar(
                plot_df,
                x="display_cpu",
                y="name",
                orientation="h",
                color="recommendation",
                color_discrete_map=color_discrete_map,
                text="display_cpu",
                labels={"display_cpu": "Birim Maliyet (TL)", "name": "Servis", "recommendation": "Karar"},
                hover_data=["monthly_cost", "total_usage", "unit"]
            )
            fig_bar.update_traces(
                texttemplate='%{text:.1f} ₺',
                textposition='outside',
                marker_line_color='rgba(255,255,255,0.2)',
                marker_line_width=1
            )
            fig_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=20, t=20, b=20),
                height=350,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=False)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with row1_col2:
            st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:4px;'>2. Kategori Bazlı Harcama Dağılımı</h4>", unsafe_allow_html=True)
            st.caption("Aylık bütçenizin kategorilere göre dağılımı.")

            cat_summary = audit_data.groupby("category")["monthly_cost"].sum().reset_index()
            fig_donut = px.pie(
                cat_summary,
                values="monthly_cost",
                names="category",
                hole=0.65,
                color="category",
                color_discrete_sequence=["#6366f1", "#ec4899", "#10b981", "#f59e0b"]
            )
            fig_donut.update_traces(
                textinfo="percent+label",
                marker=dict(line=dict(color="#07090e", width=2))
            )
            fig_donut.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=20, b=20),
                height=350,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:4px;'>3. Değer & Risk Matrisi (Maliyet vs Kullanım)</h4>", unsafe_allow_html=True)
            st.caption("Sol üst: İdeal Yatırım | Sağ alt: Tehlikeli 'Kara Delik' Harcamaları.")

            fig_scatter = px.scatter(
                audit_data,
                x="monthly_cost",
                y="total_usage",
                size="monthly_cost",
                color="recommendation",
                color_discrete_map=color_discrete_map,
                text="name",
                hover_data=["cost_per_unit", "rec_detail"],
                labels={"monthly_cost": "Aylık Ücret (TL)", "total_usage": "Kullanım (Saat/Ziyaret)", "recommendation": "Karar"}
            )
            fig_scatter.update_traces(
                textposition='top center',
                marker=dict(line=dict(width=1.5, color='#ffffff'))
            )

            med_cost = audit_data["monthly_cost"].median()
            med_use = audit_data["total_usage"].median()
            fig_scatter.add_vline(x=med_cost, line_dash="dash", line_color="rgba(255,255,255,0.2)")
            fig_scatter.add_hline(y=med_use, line_dash="dash", line_color="rgba(255,255,255,0.2)")

            fig_scatter.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=20, t=20, b=20),
                height=360,
                xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with row2_col2:
            st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:4px;'>4. 6 Aylık Bütçe Tasarruf Simülasyonu</h4>", unsafe_allow_html=True)
            st.caption("Smart SubAudit tavsiyeleri uygulandığında kümülatif bütçe kazanımı.")

            trend_df = engine.generate_trend_simulation(audit_data, months=6)
            if not trend_df.empty:
                fig_line = go.Figure()
                fig_line.add_trace(go.Scatter(
                    x=trend_df["Month"],
                    y=trend_df["Mevcut_Durum"],
                    mode="lines+markers",
                    name="Mevcut Durum",
                    line=dict(color="#f43f5e", width=3)
                ))
                fig_line.add_trace(go.Scatter(
                    x=trend_df["Month"],
                    y=trend_df["Optimize_Edilmis"],
                    mode="lines+markers",
                    name="Optimize Edilmiş",
                    line=dict(color="#10b981", width=3),
                    fill='tonexty',
                    fillcolor='rgba(16, 185, 129, 0.15)'
                ))
                fig_line.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=10, r=20, t=20, b=20),
                    height=360,
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title="Kümülatif TL"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_line, use_container_width=True)

        # --- KATEGORİ BAZLI BÜTÇE KOTALARI ---
        st.markdown("---")
        st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>🎯 Kategori Bazlı Bütçe Kotaları & Harcama Limitleri</h3>", unsafe_allow_html=True)
        st.caption("Aylık tavan bütçe hedeflerinizi belirleyin; harcama aşımı olduğunda anlık uyarı alın.")

        budget_analyses = engine.get_category_budget_analysis(audit_data)
        b_col_cards, b_col_edit = st.columns([2.2, 1.0])

        with b_col_cards:
            for b_item in budget_analyses:
                progress_val = min(1.0, float(b_item["ratio"]))
                status_color = b_item["status_color"]
                overrun_text = f"<span style='color:#f43f5e; font-weight:800;'>+{b_item['overrun']:,.1f} ₺ Aşım</span>" if b_item["overrun"] > 0 else f"<span style='color:#10b981; font-weight:700;'>{b_item['remaining']:,.1f} ₺ Kalan</span>"

                st.markdown(f"""
                <div style="background:linear-gradient(135deg, rgba(22, 27, 44, 0.7) 0%, rgba(15, 20, 32, 0.6) 100%); border:1px solid rgba(255,255,255,0.08); border-left:5px solid {status_color}; border-radius:14px; padding:16px 20px; margin-bottom:12px; box-shadow:0 6px 20px rgba(0,0,0,0.3);">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                        <div>
                            <b style="font-size:1.1rem; color:#fff;">{b_item['label']}</b>
                            <span style="font-size:0.75rem; color:#94a3b8; margin-left:8px;">({b_item['service_count']} Servis: {', '.join(b_item['services']) if b_item['services'] else 'Yok'})</span>
                        </div>
                        <div>
                            <span style="background:{status_color}25; color:{status_color}; border:1px solid {status_color}50; font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:20px;">{b_item['status']}</span>
                        </div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.9rem; color:#cbd5e1; margin-bottom:8px;">
                        <div>Harcanan: <b style="color:#fff;">{b_item['spend']:,.1f} ₺</b> / Kota: <b style="color:#94a3b8;">{b_item['limit']:,.1f} ₺</b></div>
                        <div>Doluluk: <b>%{b_item['ratio_pct']:.0f}</b> ({overrun_text})</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(progress_val)
                st.caption(f"ℹ️ {b_item['status_message']}")
                st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        with b_col_edit:
            st.markdown("""
            <div style="background:rgba(22, 27, 44, 0.75); border:1px solid rgba(99, 102, 241, 0.3); border-radius:14px; padding:18px; margin-bottom:12px; box-shadow:0 8px 24px rgba(0,0,0,0.4);">
                <h4 style="margin-top:0; color:#818cf8; font-size:1.05rem; font-weight:800;">⚙️ Kotaları Güncelle</h4>
                <p style="font-size:0.8rem; color:#94a3b8; margin-bottom:0;">Kategoriler için aylık tavan harcama limitlerinizi (TL) buradan güncelleyebilirsiniz.</p>
            </div>
            """, unsafe_allow_html=True)

            with st.form("budget_limits_form"):
                current_budgets = dm.get_category_budgets()
                new_streaming = st.number_input("🎬 Streaming Limiti (TL):", min_value=50.0, max_value=10000.0, step=50.0, value=float(current_budgets.get("streaming", 450.0)))
                new_ai = st.number_input("🤖 AI Araçları Limiti (TL):", min_value=50.0, max_value=20000.0, step=50.0, value=float(current_budgets.get("ai_tool", 800.0)))
                new_fitness = st.number_input("🏋️ Fitness Limiti (TL):", min_value=50.0, max_value=20000.0, step=50.0, value=float(current_budgets.get("fitness", 1000.0)))

                if st.form_submit_button("💾 Bütçe Limitlerini Kaydet", type="primary", use_container_width=True):
                    dm.set_category_budget("streaming", new_streaming)
                    dm.set_category_budget("ai_tool", new_ai)
                    dm.set_category_budget("fitness", new_fitness)
                    st.success("Kategori bütçe limitleri başarıyla güncellendi!")
                    st.rerun()


# ==============================================================================
# TAB 2: TASARRUF & KARAR REÇETESİ
# ==============================================================================
with tab_advice:
    st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>💡 Akıllı Tasarruf Reçetesi & Eylem Planı</h3>", unsafe_allow_html=True)
    if audit_data.empty:
        st.info("Kayıtlı abonelik bulunmadığı için henüz bir tavsiye bulunmuyor. '📋 Abonelik Yönetimi' sekmesinden yeni abonelik ekleyebilirsiniz.")
    else:
        st.markdown("<p style='color:#94a3b8; font-size:0.92rem;'>Sistemimiz her bir abonelik için birim kullanım maliyetini hesaplayarak net aksiyon planı ve piyasadaki daha ucuz alternatifleri üretir:</p>", unsafe_allow_html=True)
        # 📦 Çapraz Paket (Bundle) & Birleştirme Tasarrufu Motoru
        bundle_deals = engine.get_bundle_optimizations(audit_data)
        if bundle_deals:
            total_bundle_monthly_savings = sum(b["monthly_savings"] for b in bundle_deals)
            total_bundle_annual_savings = sum(b["annual_savings"] for b in bundle_deals)
            st.markdown(f"""
            <div class="bundle-banner">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                    <div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:1.4rem;">📦</span>
                            <span style="font-size:1.15rem; font-weight:800; color:#ffffff;">Çapraz Paket (Bundle) & Birleştirme Tasarrufu Motoru</span>
                            <span style="background:rgba(16,185,129,0.2); color:#34d399; font-size:0.75rem; font-weight:800; padding:3px 10px; border-radius:20px; border:1px solid rgba(16,185,129,0.4);">
                                {len(bundle_deals)} FIRSAT YAKALANDI
                            </span>
                        </div>
                        <p style="color:#cbd5e1; font-size:0.86rem; margin:6px 0 0 0; line-height:1.4;">
                            Farkında olmadan aynı içeriğe veya avantaja sahip birden fazla servise ayrı ayrı ödüyorsunuz. Türkiye pazarındaki gerçek ortak paket hileleriyle doğrudan tasarruf edin!
                        </p>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:0.75rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.05em; font-weight:700;">Potansiyel Net Tasarruf</div>
                        <div style="font-size:1.35rem; font-weight:900; color:#34d399;">+{total_bundle_monthly_savings:,.1f} ₺ <span style="font-size:0.85rem; color:#94a3b8;">/ay</span></div>
                        <div style="font-size:0.8rem; color:#a5b4fc; font-weight:600;">(Yıllık +{total_bundle_annual_savings:,.0f} ₺)</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            for b_idx, deal in enumerate(bundle_deals):
                deal_c1, deal_c2 = st.columns([3.8, 1.2])
                with deal_c1:
                    st.markdown(f"""
                    <div class="bundle-item-card">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
                            <div>
                                <span style="background:rgba(99,102,241,0.25); color:#a5b4fc; font-size:0.72rem; font-weight:800; padding:3px 8px; border-radius:6px; letter-spacing:0.04em;">
                                    {deal['badge']}
                                </span>
                                <b style="color:#ffffff; font-size:1.05rem; margin-left:8px;">{deal['title']}</b>
                            </div>
                            <div style="color:#34d399; font-weight:900; font-size:0.95rem; background:rgba(16,185,129,0.12); padding:3px 10px; border-radius:8px; border:1px solid rgba(16,185,129,0.3);">
                                +{deal['monthly_savings']:.1f} ₺/ay (+{deal['annual_savings']:,.0f} ₺/yıl)
                            </div>
                        </div>
                        <div style="font-size:0.85rem; color:#cbd5e1; line-height:1.45; margin-bottom:8px;">
                            💡 {deal['rationale']}
                        </div>
                        <div style="display:flex; gap:16px; font-size:0.78rem; color:#94a3b8; flex-wrap:wrap;">
                            <div>❌ Kapatılacak/İptal: <b style="color:#fb7185;">{deal['sub_to_cancel']}</b></div>
                            <div>✅ Kalacak / Geçilecek: <b style="color:#38bdf8;">{deal['sub_to_keep']}</b></div>
                            <div>🎁 Paket: <b style="color:#e2e8f0;">{deal['deal_name']}</b></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with deal_c2:
                    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
                    # Eğer kapatılacak servis veritabanında aktif bir abonelikse hızlı iptal butonu sun
                    sub_exists = any(deal['sub_to_cancel'].lower() == str(r_name).lower() for r_name in audit_data['name'].tolist())
                    if sub_exists:
                        if st.button(f"🗑️ '{deal['sub_to_cancel']}' İptal Et", key=f"bundle_cancel_{b_idx}", use_container_width=True):
                            if dm.delete_subscription(deal['sub_to_cancel']):
                                st.success(f"'{deal['sub_to_cancel']}' aboneliği silindi! Aylık +{deal['monthly_savings']:.1f} ₺ tasarruf bütçenize eklendi.")
                                st.rerun()
                    else:
                        st.info("💡 Paket Geçiş Fırsatı")

            st.markdown("<div style='height:16px; border-bottom:1px solid rgba(255,255,255,0.06); margin-bottom:20px;'></div>", unsafe_allow_html=True)

        filter_decision = st.selectbox("Filtrele:", ["Tümü", "Sadece İptal Edilecekler 🚨", "Sadece Düşürülecekler 🔽", "Sadece Tutulacaklar ✅"])


        for _, row in audit_data.iterrows():
            rec = row["recommendation"]
            if filter_decision == "Sadece İptal Edilecekler 🚨" and rec != "IPTAL_ET":
                continue
            elif filter_decision == "Sadece Düşürülecekler 🔽" and rec != "DUSUR":
                continue
            elif filter_decision == "Sadece Tutulacaklar ✅" and rec != "TUT":
                continue

            badge_class = f"badge-{rec.lower().replace('_', '')}"
            badge_label = {"TUT": "✅ TUT", "GOZLE": "⚠️ GÖZLE", "DUSUR": "🔽 DÜŞÜR", "IPTAL_ET": "🚫 İPTAL ET"}.get(rec, rec)

            waste_text = ""
            if row["annual_waste"] > 0:
                waste_text = f"<span style='color:#10b981; font-weight:800; background:rgba(16,185,129,0.12); padding:3px 8px; border-radius:6px;'>Yıllık Tasarruf: +{row['annual_waste']:,.0f} ₺</span>"

            cpu_text = f"{row['cost_per_unit']:.1f} ₺ / {row['unit']}" if pd.notna(row['cost_per_unit']) else "Kullanım Yok (0)"
            cost_display_str = row.get("display_cost", f"{row['monthly_cost']:.1f} ₺")

            # Ana Reçete Kartı
            st.markdown(f"""
            <div class="advice-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <div>
                        <b style="font-size:1.2rem; color:#fff; letter-spacing:-0.01em;">{row['name']}</b>
                        <span style="font-size:0.75rem; color:#94a3b8; background:rgba(255,255,255,0.06); padding:3px 8px; border-radius:6px; margin-left:8px; font-weight:600;">{row['category'].upper()}</span>
                    </div>
                    <div>
                        <span class="badge-pill {badge_class}">{badge_label}</span>
                    </div>
                </div>
                <div style="display:flex; gap:18px; font-size:0.88rem; color:#cbd5e1; margin-bottom:10px; flex-wrap:wrap;">
                    <div style="background:rgba(255,255,255,0.03); padding:4px 10px; border-radius:8px;">Aylık: <b style="color:#fff;">{cost_display_str}</b></div>
                    <div style="background:rgba(255,255,255,0.03); padding:4px 10px; border-radius:8px;">Kullanım: <b style="color:#fff;">{row['total_usage']:.1f} {row['unit']}</b></div>
                    <div style="background:rgba(255,255,255,0.03); padding:4px 10px; border-radius:8px;">Birim Maliyet: <b style="color:#fff;">{cpu_text}</b></div>
                    <div>{waste_text}</div>
                </div>
                <div style="font-size:0.85rem; color:#e2e8f0; background:rgba(0,0,0,0.35); border-left:3px solid #6366f1; padding:10px 14px; border-radius:8px; margin-bottom:8px; line-height:1.4;">
                    💬 <b>Sistem Tavsiyesi:</b> {row['rec_detail']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Akıllı Pazar Alternatifleri & Alt Plan (Downsell) Önerileri
            alts = AlternativeAdvisor.get_recommendations_for_subscription(
                sub_name=row['name'],
                monthly_cost_try=float(row['monthly_cost']),
                category=row['category'],
                total_usage=float(row['total_usage']),
                current_recommendation=rec
            )

            if alts:
                with st.expander(f"💡 {row['name']} İçin Daha Ucuz Alternatifler & Alt Planlar ({len(alts)} Seçenek Mevcut)", expanded=(rec in ["IPTAL_ET", "DUSUR"])):
                    for idx, alt in enumerate(alts):
                        alt_col1, alt_col2 = st.columns([3.5, 1.2])
                        with alt_col1:
                            st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                    <div>
                                        <span style="background:rgba(99, 102, 241, 0.2); color:#a5b4fc; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:6px;">{alt['badge']}</span>
                                        <b style="color:#ffffff; font-size:1rem; margin-left:8px;">{alt['name']}</b>
                                    </div>
                                    <div style="color:#34d399; font-weight:800; font-size:0.9rem;">
                                        +{alt['monthly_savings']:.1f} ₺ / ay tasarruf
                                    </div>
                                </div>
                                <div style="font-size:0.83rem; color:#cbd5e1; line-height:1.4;">
                                    🎯 {alt['rationale']}
                                </div>
                                <div style="font-size:0.78rem; color:#94a3b8; margin-top:4px;">
                                    Yeni Aylık Tutar: <b style="color:#fff;">{alt['cost']:.2f} ₺</b> | Yıllık Tasarruf: <b style="color:#34d399;">+{alt['annual_savings']:,.0f} ₺</b>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with alt_col2:
                            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
                            if alt["cost"] > 0:
                                btn_label = f"⚡ Plana Düşür ({alt['cost']:.0f} ₺)"
                            else:
                                btn_label = "🎁 Ücretsiz Plana Geç"
                            if st.button(btn_label, key=f"downsell_{row['name']}_{idx}", use_container_width=True):
                                if dm.update_subscription_cost(row['name'], alt['cost']):
                                    st.success(f"'{row['name']}' aylık ücreti {alt['cost']:.1f} ₺ olarak güncellendi! Ayda {alt['monthly_savings']:.1f} ₺ tasarruf sağlandı.")
                                    st.rerun()

            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)


# ==============================================================================
# TAB 3: MAKİNE ÖĞRENMESİ İLE GELECEK AY KULLANIM TAHMİNİ (PREDICTIVE AI)
# ==============================================================================
with tab_ml:
    st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>🤖 Scikit-Learn ile Gelecek Ay Kullanım & Harcama Tahmini (Predictive AI)</h3>", unsafe_allow_html=True)
    st.caption("Geçmiş kullanım zaman serisi verilerini Lineer Regresyon modeli ile analiz ederek gelecek 30 günlük tüketimi ve birim maliyet sapmalarını tahmin eder.")

    if audit_data.empty:
        st.info("Kayıtlı abonelik bulunmadığı için makine öğrenmesi modeli çalıştırılamıyor. 'Abonelik Yönetimi' sekmesinden servis ekleyin.")
    else:
        ml_predictions = engine.get_ml_predictions(audit_data)

        high_risk_count = sum(1 for p in ml_predictions if p["trend_direction"] in ["DÜŞÜŞ", "SIFIR_KULLANIM"])
        growing_count = sum(1 for p in ml_predictions if p["trend_direction"] == "ARTIŞ")
        steady_count = sum(1 for p in ml_predictions if p["trend_direction"] == "STABİL")
        predicted_waste = sum(p["monthly_cost"] for p in ml_predictions if p["action_recommendation"] == "DONDUR_VEYA_IPTAL")

        ml_k1, ml_k2, ml_k3, ml_k4 = st.columns(4)
        with ml_k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-top-glow glow-rose"></div>
                <div class="kpi-header"><span class="kpi-title">Düşüş / Risk Trendinde</span><div class="kpi-icon-pill" style="color:#fb7185;">📉</div></div>
                <div class="kpi-value" style="color:#f43f5e;">{high_risk_count} <span style="font-size:1rem; color:#94a3b8;">Servis</span></div>
                <div class="kpi-sub" style="color:#f87171;">Gelecek ay birim maliyet fırlayacak</div>
            </div>
            """, unsafe_allow_html=True)
        with ml_k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-top-glow glow-emerald"></div>
                <div class="kpi-header"><span class="kpi-title">Yükseliş / Verimli Trend</span><div class="kpi-icon-pill" style="color:#34d399;">📈</div></div>
                <div class="kpi-value" style="color:#10b981;">{growing_count} <span style="font-size:1rem; color:#94a3b8;">Servis</span></div>
                <div class="kpi-sub" style="color:#34d399;">Kullanım artıyor, getiri yüksek</div>
            </div>
            """, unsafe_allow_html=True)
        with ml_k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-top-glow glow-cyan"></div>
                <div class="kpi-header"><span class="kpi-title">Stabil / Dengeli</span><div class="kpi-icon-pill" style="color:#38bdf8;">⚖️</div></div>
                <div class="kpi-value" style="color:#38bdf8;">{steady_count} <span style="font-size:1rem; color:#94a3b8;">Servis</span></div>
                <div class="kpi-sub" style="color:#94a3b8;">Öngörülen tüketim sabit</div>
            </div>
            """, unsafe_allow_html=True)
        with ml_k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-top-glow glow-amber"></div>
                <div class="kpi-header"><span class="kpi-title">Önleyici Tasarruf</span><div class="kpi-icon-pill" style="color:#fbbf24;">🛡️</div></div>
                <div class="kpi-value" style="color:#f59e0b;">{predicted_waste:,.1f} <span style="font-size:1rem; color:#94a3b8;">₺/ay</span></div>
                <div class="kpi-sub" style="color:#fbbf24;">Erken iptalle önlenebilecek yük</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # Regresyon İnceleme
        st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:4px;'>🔍 Servis Bazlı Regresyon Analizi & Gelecek 30 Gün Projeksiyonu</h4>", unsafe_allow_html=True)
        sub_names = [p["name"] for p in ml_predictions]
        selected_sub_name = st.selectbox("Tahminini incelemek istediğiniz servisi seçin:", sub_names)
        selected_pred = next((p for p in ml_predictions if p["name"] == selected_sub_name), ml_predictions[0])

        col_details, col_chart = st.columns([1.1, 1.4])

        with col_details:
            border_color = "#f43f5e" if selected_pred["trend_direction"] in ["DÜŞÜŞ", "SIFIR_KULLANIM"] else ("#10b981" if selected_pred["trend_direction"] == "ARTIŞ" else "#38bdf8")
            st.markdown(f"""
            <div style="background:linear-gradient(135deg, rgba(22, 27, 44, 0.75) 0%, rgba(15, 20, 32, 0.6) 100%); border:1px solid rgba(255,255,255,0.08); border-left:5px solid {border_color}; border-radius:14px; padding:20px; margin-bottom:14px; box-shadow:0 8px 24px rgba(0,0,0,0.4);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span style="font-size:1.2rem; font-weight:800; color:#fff;">{selected_pred['name']}</span>
                    <span style="background:{border_color}25; color:{border_color}; border:1px solid {border_color}50; font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:20px;">{selected_pred['risk_level']}</span>
                </div>
                <div style="font-size:0.9rem; color:#cbd5e1; line-height:1.5; margin-bottom:12px;">
                    {selected_pred['insight_message']}
                </div>
                <div style="font-size:0.78rem; color:#94a3b8; border-top:1px solid rgba(255,255,255,0.08); padding-top:8px;">
                    ⚙️ <b>Model:</b> {selected_pred['model_name']} | <b>R² Doğruluk Skoru:</b> {selected_pred['r2_score']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            m_col1, m_col2 = st.columns(2)
            with m_col1:
                st.metric("Geçmiş Tüketim", f"{selected_pred['current_usage']:.1f} {selected_pred['unit']}")
                curr_cpu_str = f"{selected_pred['current_cpu']:.1f} ₺" if np.isfinite(selected_pred['current_cpu']) else "Kullanım Yok"
                st.metric("Mevcut Birim Maliyet", curr_cpu_str)
            with m_col2:
                delta_usage = selected_pred['predicted_usage'] - selected_pred['current_usage']
                st.metric("🔮 Tahmini Gelecek Ay", f"{selected_pred['predicted_usage']:.1f} {selected_pred['unit']}", delta=f"{delta_usage:+.1f} {selected_pred['unit']}")
                pred_cpu_str = f"{selected_pred['predicted_cpu']:.1f} ₺" if np.isfinite(selected_pred['predicted_cpu']) else "Sonsuz"
                st.metric("📈 Beklenen Birim Maliyet", pred_cpu_str)

        with col_chart:
            if selected_pred["has_trend_chart"] and len(selected_pred["chart_dates_hist"]) > 0:
                fig_ml = go.Figure()
                fig_ml.add_trace(go.Scatter(
                    x=selected_pred["chart_dates_hist"],
                    y=selected_pred["chart_usage_hist"],
                    mode="markers+lines",
                    name="Geçmiş Gerçek Kullanım",
                    line=dict(color="#38bdf8", width=2.5),
                    marker=dict(size=8, color="#38bdf8")
                ))
                fig_ml.add_trace(go.Scatter(
                    x=selected_pred["future_dates"],
                    y=np.linspace(selected_pred["chart_usage_hist"][-1], selected_pred["predicted_usage"] / 30.0, len(selected_pred["future_dates"])),
                    mode="lines",
                    name="🤖 ML Gelecek Projeksiyonu",
                    line=dict(color="#a855f7", width=3, dash="dash"),
                    fill='tozeroy',
                    fillcolor='rgba(168, 85, 247, 0.12)'
                ))
                fig_ml.update_layout(
                    title=dict(text=f"{selected_pred['name']} — Zaman Serisi Trend & Tahmin Çizgisi", font=dict(color="#fff", size=13)),
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=340,
                    margin=dict(l=10, r=20, t=40, b=20),
                    xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", title=f"Kullanım ({selected_pred['unit']})"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_ml, use_container_width=True)
            else:
                st.markdown("""
                <div style="background:rgba(22, 27, 44, 0.6); border:1px dashed rgba(255,255,255,0.15); border-radius:14px; height:320px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:20px;">
                    <span style="font-size:2.5rem; margin-bottom:10px;">📉</span>
                    <b style="color:#e2e8f0; font-size:1.1rem;">Geçmiş Kullanım Kaydı Bulunmuyor</b>
                    <p style="color:#94a3b8; font-size:0.85rem; max-width:380px; margin-top:6px;">
                        Bu servis için henüz tarihli kullanım girilmedi. <b>'Günlük Kullanım Girişi'</b> sekmesinden kayıt ekleyerek yapay zeka modelini besleyebilirsiniz.
                    </p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # Risk Tablosu
        st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:8px;'>📋 Tüm Aboneliklerin Gelecek Ay Risk & Tahmin Tablosu</h4>", unsafe_allow_html=True)
        summary_rows = []
        for p in ml_predictions:
            curr_cpu_disp = f"{p['current_cpu']:.1f} ₺/{p['unit']}" if np.isfinite(p['current_cpu']) else "Kullanım Yok"
            pred_cpu_disp = f"{p['predicted_cpu']:.1f} ₺/{p['unit']}" if np.isfinite(p['predicted_cpu']) else "Sonsuz 🚨"
            trend_disp = f"%{p['trend_pct']:+.1f}" if p['trend_direction'] != "SIFIR_KULLANIM" else "Sıfır"

            summary_rows.append({
                "Servis": p["name"],
                "Kategori": p["category"],
                "Aylık Bütçe": f"{p['monthly_cost']:.1f} ₺",
                "Mevcut Kullanım": f"{p['current_usage']:.1f} {p['unit']}",
                "🔮 Tahmini Gelecek Kullanım": f"{p['predicted_usage']:.1f} {p['unit']}",
                "Trend Değişimi": trend_disp,
                "Mevcut Birim Maliyet": curr_cpu_disp,
                "📈 Tahmini Birim Maliyet": pred_cpu_disp,
                "Risk Durumu": p["risk_level"],
                "Önerilen Eylem": p["action_recommendation"]
            })

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)


# ==============================================================================
# TAB 4: GITHUB TARZI ABONELİK KULLANIM ISI HARİTASI & ALIŞKANLIK ANALİZİ
# ==============================================================================
with tab_heatmap:
    st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>📅 GitHub Tarzı Abonelik Kullanım Isı Haritası & Alışkanlık Analizi</h3>", unsafe_allow_html=True)
    st.caption("Yılın her bir gününde aboneliklerinizin ne kadar aktif kullanıldığını renk tonlarıyla inceleyin, aktiflik serilerinizi (streak) ve haftalık tüketim desenlerinizi keşfedin.")

    subs_df_heat = dm.load_subscriptions_df()

    # Filtre Alanı
    h_filter_col1, h_filter_col2 = st.columns([1.5, 1])
    with h_filter_col1:
        sub_options = ["Tüm Servisler (Genel Aktivite)"] + (subs_df_heat["name"].tolist() if not subs_df_heat.empty else [])
        selected_heat_sub = st.selectbox("Aktivitesini incelemek istediğiniz servisi seçin:", sub_options, key="heat_sub_select")
    with h_filter_col2:
        range_options = {
            "Son 90 Gün (~13 Hafta)": 90,
            "Son 140 Gün (~20 Hafta - Önerilen)": 140,
            "Son 180 Gün (~26 Hafta / 6 Ay)": 180,
            "Son 365 Gün (Tüm Yıl)": 365
        }
        selected_range_label = st.selectbox("Zaman Aralığı:", list(range_options.keys()), index=1, key="heat_range_select")
        selected_days = range_options[selected_range_label]

    heat_data = engine.get_activity_heatmap_data(sub_name=selected_heat_sub, days=selected_days)

    # 4 Adet Alışkanlık KPI Kartı
    hk1, hk2, hk3, hk4 = st.columns(4)
    with hk1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-top-glow glow-emerald"></div>
            <div class="kpi-header"><span class="kpi-title">Kesintisiz Seri (Streak)</span><div class="kpi-icon-pill" style="color:#10b981;">🔥</div></div>
            <div class="kpi-value" style="color:#10b981;">{heat_data['current_streak']} <span style="font-size:1.1rem; color:#94a3b8; font-weight:600;">gün</span></div>
            <div class="kpi-sub">En uzun rekor: <b style="color:#f1f5f9; margin-left:4px;">{heat_data['longest_streak']} gün üst üste</b></div>
        </div>
        """, unsafe_allow_html=True)
    with hk2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-top-glow glow-cyan"></div>
            <div class="kpi-header"><span class="kpi-title">Aktivite Oranı</span><div class="kpi-icon-pill" style="color:#38bdf8;">⚡</div></div>
            <div class="kpi-value" style="color:#38bdf8;">%{heat_data['activity_rate_pct']:.0f}</div>
            <div class="kpi-sub">{heat_data['active_days']} aktif / {heat_data['inactive_days']} boş gün</div>
        </div>
        """, unsafe_allow_html=True)
    with hk3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-top-glow glow-indigo"></div>
            <div class="kpi-header"><span class="kpi-title">Zirve Kullanım Günü</span><div class="kpi-icon-pill" style="color:#818cf8;">🏆</div></div>
            <div class="kpi-value" style="font-size:1.45rem; color:#f1f5f9;">{heat_data['busiest_day']}</div>
            <div class="kpi-sub">Toplam: <b style="color:#818cf8; margin-left:4px;">{heat_data['busiest_day_amount']:.1f} saat/ziyaret</b></div>
        </div>
        """, unsafe_allow_html=True)
    with hk4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-top-glow glow-amber"></div>
            <div class="kpi-header"><span class="kpi-title">Hafta Sonu Yoğunluğu</span><div class="kpi-icon-pill" style="color:#fbbf24;">📊</div></div>
            <div class="kpi-value" style="color:#f59e0b;">%{heat_data['weekend_ratio_pct']:.0f}</div>
            <div class="kpi-sub">Hafta içi payı: <b style="color:#f1f5f9; margin-left:4px;">%{100 - heat_data['weekend_ratio_pct']:.0f}</b></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # Plotly Calendar Heatmap Oluşturma
    days_data = heat_data["days"]
    if days_data:
        max_week = max(d["week_idx"] for d in days_data)
        num_weeks = max_week + 1

        z_matrix = np.zeros((7, num_weeks))
        text_matrix = [["" for _ in range(num_weeks)] for _ in range(7)]

        for d in days_data:
            w_idx = d["week_idx"]
            wd_idx = d["weekday"]
            z_matrix[wd_idx, w_idx] = d["amount"]
            text_matrix[wd_idx][w_idx] = d["tooltip"]

        month_labels = []
        month_positions = []
        seen_months = set()
        for d in days_data:
            m_key = f"{d['month_str']}_{d['date'][:7]}"
            if m_key not in seen_months:
                seen_months.add(m_key)
                month_labels.append(d["month_str"])
                month_positions.append(d["week_idx"])

        custom_colorscale = [
            [0.0, "#161e2e"],       # Boş gün (derin lacivert/koyu slate)
            [0.001, "#064e3b"],     # Çok az kullanım (Koyu zümrüt)
            [0.35, "#059669"],      # Orta kullanım
            [0.70, "#10b981"],      # Yüksek kullanım
            [1.0, "#34d399"]        # Zirve kullanım (Neon parlak zümrüt)
        ]

        weekday_names_display = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

        fig_heat = go.Figure(data=go.Heatmap(
            z=z_matrix,
            x=list(range(num_weeks)),
            y=weekday_names_display,
            text=text_matrix,
            hoverinfo="text",
            colorscale=custom_colorscale,
            showscale=False,
            xgap=4,
            ygap=4
        ))

        fig_heat.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=280,
            margin=dict(l=10, r=20, t=10, b=30),
            xaxis=dict(
                tickmode="array",
                tickvals=month_positions,
                ticktext=month_labels,
                showgrid=False,
                zeroline=False,
                tickfont=dict(color="#cbd5e1", size=11, family="Plus Jakarta Sans")
            ),
            yaxis=dict(
                autorange="reversed",
                showgrid=False,
                zeroline=False,
                tickfont=dict(color="#94a3b8", size=11, family="Plus Jakarta Sans")
            )
        )

        st.markdown(f"""
        <div style="background:linear-gradient(135deg, rgba(22, 27, 44, 0.75) 0%, rgba(15, 20, 32, 0.6) 100%); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:20px; margin-bottom:18px; box-shadow:0 8px 30px rgba(0,0,0,0.4);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <b style="color:#fff; font-size:1.05rem;">{selected_heat_sub} — Günlük Aktivite Matrisi</b>
                <div style="display:flex; align-items:center; gap:6px; font-size:0.75rem; color:#94a3b8;">
                    <span>Daha Az</span>
                    <span style="display:inline-block; width:12px; height:12px; background:#161e2e; border-radius:2px; border:1px solid rgba(255,255,255,0.1);"></span>
                    <span style="display:inline-block; width:12px; height:12px; background:#064e3b; border-radius:2px;"></span>
                    <span style="display:inline-block; width:12px; height:12px; background:#059669; border-radius:2px;"></span>
                    <span style="display:inline-block; width:12px; height:12px; background:#10b981; border-radius:2px;"></span>
                    <span style="display:inline-block; width:12px; height:12px; background:#34d399; border-radius:2px;"></span>
                    <span>Daha Çok</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.plotly_chart(fig_heat, use_container_width=True)

        # Alt Bölüm: İçgörüler & Gün Dağılım Çubuk Grafiği
        col_insights, col_day_bar = st.columns([1.2, 1.0])

        with col_insights:
            st.markdown("<h4 style='font-size:1.05rem; font-weight:800; color:#fff; margin-bottom:10px;'>💡 Yapay Zeka Alışkanlık & Davranış Analizi</h4>", unsafe_allow_html=True)
            for insight in heat_data["insights"]:
                st.markdown(f"""
                <div style="background:rgba(22, 27, 44, 0.6); border:1px solid rgba(255,255,255,0.06); border-left:4px solid #6366f1; border-radius:10px; padding:12px 16px; margin-bottom:8px; font-size:0.88rem; color:#cbd5e1; line-height:1.45;">
                    🎯 {insight}
                </div>
                """, unsafe_allow_html=True)

        with col_day_bar:
            st.markdown("<h4 style='font-size:1.05rem; font-weight:800; color:#fff; margin-bottom:10px;'>📊 Günlere Göre Toplam Tüketim</h4>", unsafe_allow_html=True)
            wk_df = pd.DataFrame({
                "Gün": ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"],
                "Kullanım": [heat_data["weekday_totals"][i] for i in range(7)]
            })
            fig_wk_bar = px.bar(
                wk_df,
                x="Gün",
                y="Kullanım",
                color="Kullanım",
                color_continuous_scale=[[0, "#064e3b"], [1, "#10b981"]],
                text="Kullanım"
            )
            fig_wk_bar.update_traces(
                texttemplate='%{text:.1f}',
                textposition='outside',
                marker_line_color='rgba(255,255,255,0.15)',
                marker_line_width=1
            )
            fig_wk_bar.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=240,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=20),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
            )
            st.plotly_chart(fig_wk_bar, use_container_width=True)


# ==============================================================================
# TAB 5: ABONELİK YÖNETİMİ
# ==============================================================================
with tab_manage:
    st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>📋 Abonelik Yönetimi (Ekle, Sil, Düzenle)</h3>", unsafe_allow_html=True)
    subs_table = dm.load_subscriptions_df()

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(22, 27, 44, 0.75) 0%, rgba(15, 20, 32, 0.6) 100%); padding: 18px 20px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
            <h4 style="margin:0; color:#10b981; font-weight:800;">➕ Yeni Abonelik Ekle</h4>
        </div>
        """, unsafe_allow_html=True)
        with st.form("quick_add_sub_form", clear_on_submit=True):
            f_name = st.text_input("Abonelik / Servis Adı:", placeholder="örn: ChatGPT Plus, Netflix, MacFit")
            f_cat_choice = st.selectbox("Kategori:", [
                ("streaming", "Yayın & Medya (Film, Dizi, Müzik)"),
                ("ai_tool", "Yapay Zeka & Yazılım Araçları"),
                ("fitness", "Spor Salonu & Fiziksel Üyelik")
            ], format_func=lambda x: x[1])[0]

            col_cost, col_curr = st.columns([1.5, 1])
            with col_cost:
                f_cost = st.number_input("Aylık Ücret:", min_value=0.0, step=5.0, value=20.0)
            with col_curr:
                f_curr = st.selectbox("Para Birimi:", ["TL", "USD", "EUR", "GBP"])

            f_day = st.slider("Ayın hangi günü yenileniyor?", min_value=1, max_value=31, value=1)

            if st.form_submit_button("➕ Sisteme Ekle", type="primary", use_container_width=True):
                if not f_name.strip():
                    st.error("Lütfen bir abonelik adı girin!")
                else:
                    if dm.add_subscription(f_name, f_cat_choice, f_cost, f_curr, f_day):
                        st.success(f"'{f_name}' ({f_cost} {f_curr}) başarıyla eklendi!")
                        st.rerun()

    with action_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(22, 27, 44, 0.75) 0%, rgba(15, 20, 32, 0.6) 100%); padding: 18px 20px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
            <h4 style="margin:0; color:#f43f5e; font-weight:800;">🗑️ Abonelik Sil</h4>
        </div>
        """, unsafe_allow_html=True)

        if not subs_table.empty:
            del_target = st.selectbox("Silinecek Servisi Seçin:", subs_table["name"].tolist(), key="quick_del_sub")
            st.caption(f"'{del_target}' silindiğinde tüm geçmiş kullanım verileri de otomatik silinir.")
            if st.button(f"🗑️ '{del_target}' Aboneliğini Sil", type="secondary", use_container_width=True):
                if dm.delete_subscription(del_target):
                    st.success(f"'{del_target}' başarıyla silindi!")
                    st.rerun()

            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            if st.button("⚠️ Tüm Abonelikleri Temizle (Veritabanını Sıfırla)", type="secondary", use_container_width=True):
                if dm.delete_all_subscriptions():
                    st.success("Tüm abonelikler ve kullanım geçmişi başarıyla silindi!")
                    st.rerun()
        else:
            st.info("Silinecek abonelik bulunmuyor.")

    st.markdown("---")

    # Mevcut Tablo ve Düzenleme
    if not subs_table.empty:
        st.markdown("<h4 style='font-size:1.1rem; font-weight:800; color:#fff; margin-bottom:8px;'>📑 Kayıtlı Abonelikler Envanteri</h4>", unsafe_allow_html=True)
        objs = dm.load_subscription_objects()
        days_left = [sub.days_until_renewal() for sub in objs]
        annuals = [sub.annual_cost() for sub in objs]

        display_df = subs_table.copy()
        display_df["Yıllık Maliyet (TL)"] = annuals
        display_df["Kalan Gün"] = [f"{d} gün" for d in days_left]

        cols_order = [c for c in ["name", "category", "monthly_cost", "currency", "renewal_day", "Yıllık Maliyet (TL)", "Kalan Gün"] if c in display_df.columns]
        st.dataframe(display_df[cols_order], use_container_width=True, hide_index=True)

        with st.expander("✏️ Bir Aboneliğin Fiyatını veya Gününü Düzenle"):
            edit_sub_name = st.selectbox("Düzenlenecek Servis:", subs_table["name"].tolist(), key="edit_sub_select_box")
            target_row = subs_table[subs_table["name"] == edit_sub_name].iloc[0]

            with st.form("edit_sub_form"):
                e_cost = st.number_input("Yeni Aylık Ücret (TL):", min_value=0.0, step=10.0, value=float(target_row["monthly_cost"]))
                e_day = st.slider("Yeni Yenilenme Günü:", 1, 31, int(target_row.get("renewal_day", 1)))

                if st.form_submit_button("💾 Güncelle", type="primary", use_container_width=True):
                    if dm.update_subscription(target_row["id"], target_row["name"], target_row["category"], e_cost, "TL", e_day):
                        st.success(f"'{edit_sub_name}' güncellendi!")
                        st.rerun()


# ==============================================================================
# TAB 5: GÜNLÜK KULLANIM GİRİŞİ
# ==============================================================================
with tab_usage:
    st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>⏱️ Günlük Kullanım Girişi & Takip</h3>", unsafe_allow_html=True)
    subs_df = dm.load_subscriptions_df()

    u_col1, u_col2 = st.columns([1, 1.2])

    with u_col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(22, 27, 44, 0.75) 0%, rgba(15, 20, 32, 0.6) 100%); padding: 18px 20px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
            <h4 style="margin:0; color:#6366f1; font-weight:800;">⏱️ Hızlı Kullanım Kaydı Gir</h4>
        </div>
        """, unsafe_allow_html=True)

        if subs_df.empty:
            st.warning("Kullanım girebilmek için önce bir abonelik eklemelisiniz.")
        else:
            with st.form("fast_usage_form", clear_on_submit=True):
                target_sub = st.selectbox("Hangi servisi kullandınız?:", subs_df["name"].tolist())
                amount = st.number_input("Kullanım Süresi (Saat) veya Ziyaret Sayısı:", min_value=0.25, max_value=100.0, step=0.5, value=2.0)
                log_d = st.date_input("Kullanım Tarihi:", value=date.today())

                if st.form_submit_button("✅ Kullanımı Kaydet", type="primary", use_container_width=True):
                    if dm.log_usage(target_sub, amount, log_d.strftime("%Y-%m-%d")):
                        st.success(f"{target_sub} için {amount} kullanım kaydedildi!")
                        st.rerun()

    with u_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(22, 27, 44, 0.75) 0%, rgba(15, 20, 32, 0.6) 100%); padding: 18px 20px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 16px;">
            <h4 style="margin:0; color:#94a3b8; font-weight:800;">📜 Son Kullanım Geçmişi & Silme</h4>
        </div>
        """, unsafe_allow_html=True)

        usage_df = dm.load_usage_df()
        if not usage_df.empty:
            usage_df_sorted = usage_df.sort_values(by="date", ascending=False)
            safe_cols = [c for c in ["log_id", "name", "date", "usage_amount", "usage_unit"] if c in usage_df_sorted.columns]
            st.dataframe(usage_df_sorted[safe_cols], use_container_width=True, hide_index=True)

            if "log_id" in usage_df_sorted.columns:
                st.markdown("<h5 style='color:#fff; font-size:0.95rem; margin-top:12px;'>🗑️ Hatalı Kaydı Sil</h5>", unsafe_allow_html=True)
                log_options = [f"#{row['log_id']} - {row['name']} ({row['usage_amount']} {row['usage_unit']} | {row['date']})" for _, row in usage_df_sorted.iterrows()]
                selected_log_str = st.selectbox("Silinecek log kaydı:", log_options, key="del_log_select")
                selected_log_id = int(selected_log_str.split(" - ")[0].replace("#", ""))

                if st.button("🗑️ Seçilen Kullanım Kaydını Sil", type="secondary", use_container_width=True):
                    if dm.delete_usage_log(selected_log_id):
                        st.success(f"Log #{selected_log_id} silindi!")
                        st.rerun()
        else:
            st.info("Henüz kullanım kaydı bulunmuyor.")


# ==============================================================================
# TAB 6: RAPOR & DIŞA AKTARMA
# ==============================================================================
with tab_export:
    st.markdown("<h3 style='font-size:1.3rem; font-weight:800; color:#fff; margin-bottom:4px;'>📥 Veri ve Rapor Dışa Aktarma</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8; font-size:0.92rem;'>Tüm analiz sonuçlarını Excel/CSV olarak indirebilir veya Matplotlib ile oluşturulan görsel raporu kaydedebilirsiniz.</p>", unsafe_allow_html=True)

    export_col1, export_col2, export_col3 = st.columns(3)

    with export_col1:
        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom:12px;">
            <div class="kpi-top-glow glow-indigo"></div>
            <div class="kpi-header"><span class="kpi-title">Yönetici Finans Raporu</span><div class="kpi-icon-pill" style="color:#818cf8;">📄</div></div>
            <p style="font-size:0.82rem; color:#cbd5e1; margin-bottom:12px;">ReportLab ile hazırlanmış resmi A4 kapaklı PDF raporu.</p>
        </div>
        """, unsafe_allow_html=True)
        pdf_bytes = pdf_gen.build_pdf(audit_data, kpi, cs.get_source_info())
        st.download_button(
            label="📄 PDF Raporunu İndir",
            data=pdf_bytes,
            file_name=f"Smart_SubAudit_Yonetici_Raporu_{date.today().strftime('%Y_%m_%d')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    with export_col2:
        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom:12px;">
            <div class="kpi-top-glow glow-emerald"></div>
            <div class="kpi-header"><span class="kpi-title">Ham Veri Tablosu</span><div class="kpi-icon-pill" style="color:#34d399;">📊</div></div>
            <p style="font-size:0.82rem; color:#cbd5e1; margin-bottom:12px;">Excel veya Tableau gibi BI araçlarında incelemek için CSV verisi.</p>
        </div>
        """, unsafe_allow_html=True)
        csv_data = audit_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📊 Analiz Verilerini İndir (.CSV)",
            data=csv_data,
            file_name=f"Smart_SubAudit_Raporu_{date.today().strftime('%Y_%m_%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with export_col3:
        st.markdown(f"""
        <div class="kpi-card" style="margin-bottom:12px;">
            <div class="kpi-top-glow glow-cyan"></div>
            <div class="kpi-header"><span class="kpi-title">Dashboard Görseli</span><div class="kpi-icon-pill" style="color:#38bdf8;">🖼️</div></div>
            <p style="font-size:0.82rem; color:#cbd5e1; margin-bottom:12px;">Sunumlar için 4 panelli statik analitik infografik görseli.</p>
        </div>
        """, unsafe_allow_html=True)
        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_report.png")
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            st.download_button(
                label="🖼️ Dashboard Görselini İndir (.PNG)",
                data=img_bytes,
                file_name="Smart_SubAudit_Dashboard.png",
                mime="image/png",
                use_container_width=True
            )
        else:
            st.info("Görsel rapor henüz oluşturulmadı. Terminalden veya 'Dashboard' sekmesinden oluşturabilirsiniz.")

    st.markdown("---")
    st.markdown("<h4 style='font-size:1.05rem; font-weight:800; color:#fff;'>🔄 Demo / Örnek Veriler</h4>", unsafe_allow_html=True)
    st.caption("Eğer sıfırdan abonelik eklemek yerine örnek 7 abonelik ve 30 kullanım kaydını geri getirmek isterseniz bu butonu kullanabilirsiniz.")
    if st.button("🔄 Örnek Verileri Sıfırdan Yükle", type="secondary"):
        if dm.reset_to_sample_data():
            st.success("Örnek demo verileri başarıyla yüklendi!")
            st.rerun()
