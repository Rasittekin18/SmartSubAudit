"""
SmartSubAudit - test_subaudit.py
Kapsamlı Birim ve Entegrasyon Testleri (Unittest / PyTest):
- OOP Sınıfları ve Polimorfizm Testleri
- SQLite CRUD & Cascade Silme Testleri
- Sıfır Abonelik (0 State) & Yeniden Başlatma Dayanıklılık Testi
- Analitik Motoru ve KPI Hesaplama Testleri
"""

import os
import unittest
import pandas as pd
from models import StreamingSub, AIToolSub, FitnessSub, subscription_factory
from data_manager import DataManager
from analytics import AnalyticsEngine


class TestSubscriptionModels(unittest.TestCase):
    def test_streaming_sub(self):
        sub = StreamingSub("Netflix Test", 300.0, "TL", 15)
        self.assertEqual(sub.get_name(), "Netflix Test")
        self.assertEqual(sub.get_usage_unit(), "saat")
        self.assertEqual(sub.annual_cost(), 3600.0)

        # 0 kullanım -> inf ve IPTAL_ET
        self.assertEqual(sub.calculate_value_score(0), float("inf"))
        rec, _ = sub.get_recommendation(0)
        self.assertEqual(rec, "IPTAL_ET")

        # Yüksek kullanım -> TUT
        self.assertAlmostEqual(sub.calculate_value_score(30.0), 10.0)
        rec, _ = sub.get_recommendation(30.0)
        self.assertEqual(rec, "TUT")

    def test_ai_tool_sub(self):
        sub = AIToolSub("ChatGPT Test", 700.0, "TL", 20)
        self.assertEqual(sub.get_usage_unit(), "saat")
        # 35 saat -> 20 TL/saat -> TUT
        rec, _ = sub.get_recommendation(35.0)
        self.assertEqual(rec, "TUT")

    def test_fitness_sub(self):
        sub = FitnessSub("Gym Test", 800.0, "TL", 1)
        self.assertEqual(sub.get_usage_unit(), "ziyaret")
        # 1 ziyaret -> 800 TL/ziyaret -> IPTAL_ET
        rec, _ = sub.get_recommendation(1.0)
        self.assertEqual(rec, "IPTAL_ET")


class TestDatabaseAndZeroState(unittest.TestCase):
    def setUp(self):
        # Geçici izole test veritabanı
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_db = "test_subaudit_temp.db"
        self.dm = DataManager(base_dir=self.test_dir, db_name=self.test_db)

    def tearDown(self):
        # Test sonrası temizlik
        db_file = os.path.join(self.test_dir, "data", self.test_db)
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
            except Exception:
                pass

    def test_crud_and_zero_state_persistence(self):
        # 1. Yeni abonelik ekle
        self.assertTrue(self.dm.add_subscription("Spotify Deneme", "streaming", 100.0, "TL", 5))
        df = self.dm.load_subscriptions_df()
        self.assertEqual(len(df), 1)

        # 2. Kullanım ekle
        self.assertTrue(self.dm.log_usage("Spotify Deneme", 10.0, "2026-10-01"))
        usage_df = self.dm.load_usage_df()
        self.assertEqual(len(usage_df), 1)

        # 3. Aboneliği sil ve 0'a düşür
        self.assertTrue(self.dm.delete_subscription("Spotify Deneme"))
        df_after_del = self.dm.load_subscriptions_df()
        self.assertEqual(len(df_after_del), 0)

        # Bağlı kullanım da cascade ile silinmeli
        usage_after_del = self.dm.load_usage_df()
        self.assertEqual(len(usage_after_del), 0)

        # 4. KRİTİK TEST: Veritabanı 0 abonelikteyken DataManager tekrar başlatıldığında
        # CSV'den 7 servise ASLA geri dönmemeli, 0 kalmalı!
        dm_reloaded = DataManager(base_dir=self.test_dir, db_name=self.test_db)
        df_reloaded = dm_reloaded.load_subscriptions_df()
        self.assertEqual(len(df_reloaded), 0, "HATA: 0 abonelik varken otomatik migrasyon tetiklendi!")


class TestAnalytics(unittest.TestCase):
    def test_empty_analytics(self):
        # 0 abonelik durumunda Analytics çökmemeli, sıfır KPI dönmeli
        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_db = "test_subaudit_empty.db"
        dm = DataManager(base_dir=test_dir, db_name=test_db)

        # Tümünü temizle
        with dm.get_connection() as conn:
            conn.execute("DELETE FROM subscriptions;")
            conn.execute("DELETE FROM usage_logs;")
            conn.commit()

        engine = AnalyticsEngine(dm)
        audit_df = engine.perform_full_audit()
        self.assertTrue(audit_df.empty)

        kpi = engine.get_summary_kpi(audit_df)
        self.assertEqual(kpi["total_services"], 0)
        self.assertEqual(kpi["total_monthly"], 0.0)
        self.assertEqual(kpi["cancel_count"], 0)

class TestCurrencyService(unittest.TestCase):
    def test_currency_conversion(self):
        from currency_service import CurrencyService
        cs = CurrencyService()
        rates = cs.get_rates()
        self.assertIn("TRY", rates)
        self.assertIn("USD", rates)
        self.assertEqual(rates["TRY"], 1.0)
        self.assertGreater(rates["USD"], 10.0)

        # 100 TL -> 100 TL
        val, rate = cs.convert_to_try(100.0, "TL")
        self.assertEqual(val, 100.0)

        # 10 USD -> 10 * rate
        val_usd, rate_usd = cs.convert_to_try(10.0, "USD")
        self.assertAlmostEqual(val_usd, 10.0 * rate_usd, places=1)


class TestPDFGenerator(unittest.TestCase):
    def test_pdf_generation(self):
        from pdf_generator import ExecutiveReportGenerator
        gen = ExecutiveReportGenerator()
        df = pd.DataFrame([{
            "name": "Test Sub",
            "category": "streaming",
            "monthly_cost": 150.0,
            "display_cost": "150.00 TL",
            "total_usage": 10.0,
            "unit": "saat",
            "cost_per_unit": 15.0,
            "recommendation": "TUT",
            "annual_waste": 0.0
        }])
        kpi = {
            "total_monthly": 150.0,
            "total_annual": 1800.0,
            "potential_annual_savings": 0.0,
            "cancel_count": 0
        }
        pdf_bytes = gen.build_pdf(df, kpi)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)
        # PDF magic header check (%PDF-)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class TestUrgentRenewalAlerts(unittest.TestCase):
    def test_renewal_alert_detection(self):
        import datetime
        from data_manager import DataManager
        from analytics import AnalyticsEngine

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_db = "test_subaudit_alerts.db"
        dm = DataManager(base_dir=test_dir, db_name=test_db)

        try:
            today = datetime.date.today()
            # 1. Acil İptal Senaryosu: Yenilenmesi tam bugün veya yarın olan, 0 kullanımlı pahalı servis
            urgent_day = today.day
            dm.add_subscription("Pahalı İsraf AI", "ai_tool", 500.0, "TL", urgent_day)

            # 2. Güvenli Senaryo: Yenilenmesine 20 gün olan servis
            safe_day = ((today.day + 15 - 1) % 28) + 1
            dm.add_subscription("Uzak Güvenli Servis", "streaming", 100.0, "TL", safe_day)

            engine = AnalyticsEngine(dm)
            audit_df = engine.perform_full_audit()
            alerts = engine.get_urgent_renewal_alerts(audit_df, days_threshold=3)

            # Doğrulamalar:
            self.assertEqual(alerts["critical_count"], 1)
            self.assertEqual(alerts["critical_alerts"][0]["name"], "Pahalı İsraf AI")
            self.assertEqual(alerts["immediate_monthly_savings"], 500.0)
            self.assertEqual(alerts["immediate_annual_savings"], 6000.0)
            self.assertIn("BUGÜN", alerts["critical_alerts"][0]["urgency_label"])
        finally:
            # Temizlik
            db_file = os.path.join(test_dir, "data", test_db)
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass


class TestMLPredictor(unittest.TestCase):
    def test_ml_prediction_declining_and_zero(self):
        from data_manager import DataManager
        from ml_predictor import UsagePredictor

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_db = "test_subaudit_ml.db"
        dm = DataManager(base_dir=test_dir, db_name=test_db)

        try:
            # 1. Düşüş Trendi Testi
            dm.add_subscription("Düşen Netflix", "streaming", 300.0, "TL", 10)
            dm.log_usage("Düşen Netflix", 10.0, "2026-10-01")
            dm.log_usage("Düşen Netflix", 5.0, "2026-10-10")
            dm.log_usage("Düşen Netflix", 1.0, "2026-10-20")

            predictor = UsagePredictor(dm)
            res_dec = predictor.predict_subscription_usage("Düşen Netflix", 300.0, "streaming", "saat")

            self.assertEqual(res_dec["name"], "Düşen Netflix")
            self.assertEqual(res_dec["trend_direction"], "DÜŞÜŞ")
            self.assertGreaterEqual(res_dec["r2_score"], 0.8)
            self.assertEqual(res_dec["action_recommendation"], "DONDUR_VEYA_IPTAL")
            self.assertIn("Scikit-Learn", res_dec["model_name"])

            # 2. Sıfır Kullanım Testi
            dm.add_subscription("Sıfır Spor", "fitness", 800.0, "TL", 5)
            res_zero = predictor.predict_subscription_usage("Sıfır Spor", 800.0, "fitness", "ziyaret")

            self.assertEqual(res_zero["trend_direction"], "SIFIR_KULLANIM")
            self.assertEqual(res_zero["predicted_usage"], 0.0)
            self.assertEqual(res_zero["predicted_cpu"], float("inf"))
            self.assertEqual(res_zero["risk_level"], "KRİTİK RİSK 🚨")

            dm.delete_subscription("Düşen Netflix")
            dm.delete_subscription("Sıfır Spor")
        finally:
            db_file = os.path.join(test_dir, "data", test_db)
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass


class TestAlternativeAdvisor(unittest.TestCase):
    def test_netflix_downsell(self):
        from recommendation_engine import AlternativeAdvisor
        alts = AlternativeAdvisor.get_recommendations_for_subscription(
            sub_name="Netflix Özel (4K)",
            monthly_cost_try=380.0,
            category="streaming",
            total_usage=5.0,
            current_recommendation="DUSUR"
        )
        self.assertGreaterEqual(len(alts), 2)
        alt_names = [a["name"] for a in alts]
        self.assertTrue(any("Temel Plan" in name for name in alt_names))
        # 380 - 149.99 = 230.01 TL
        temel = next(a for a in alts if "Temel Plan" in a["name"])
        self.assertAlmostEqual(temel["monthly_savings"], 230.01, places=1)

    def test_chatgpt_free_tier(self):
        from recommendation_engine import AlternativeAdvisor
        alts = AlternativeAdvisor.get_recommendations_for_subscription(
            sub_name="ChatGPT Plus ($20)",
            monthly_cost_try=990.0,
            category="ai_tool",
            total_usage=2.0,
            current_recommendation="IPTAL_ET"
        )
        self.assertGreaterEqual(len(alts), 1)
        free_gpt = next(a for a in alts if "Free Tier" in a["name"])
        self.assertEqual(free_gpt["cost"], 0.0)
        self.assertEqual(free_gpt["monthly_savings"], 990.0)

    def test_active_service_no_alternative_needed(self):
        from recommendation_engine import AlternativeAdvisor
        alts = AlternativeAdvisor.get_recommendations_for_subscription(
            sub_name="Spotify",
            monthly_cost_try=59.99,
            category="streaming",
            total_usage=40.0,
            current_recommendation="TUT"
        )
        self.assertEqual(len(alts), 0)


class TestCategoryBudgets(unittest.TestCase):
    def test_category_budget_tracking_and_overrun(self):
        from data_manager import DataManager
        from analytics import AnalyticsEngine

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_db = "test_subaudit_budgets.db"
        dm = DataManager(base_dir=test_dir, db_name=test_db)

        try:
            # 1. Varsayılan kotaları kontrol et
            budgets = dm.get_category_budgets()
            self.assertIn("streaming", budgets)
            self.assertIn("fitness", budgets)

            # 2. Özel kota belirle (Streaming: 300 TL)
            dm.set_category_budget("streaming", 300.0)
            updated_budgets = dm.get_category_budgets()
            self.assertEqual(updated_budgets["streaming"], 300.0)

            # 3. Kotayı aşan abonelik ekle (Netflix 380 TL)
            dm.add_subscription("Pahalı Netflix", "streaming", 380.0, "TL", 15)

            engine = AnalyticsEngine(dm)
            analysis = engine.get_category_budget_analysis()

            streaming_item = next((item for item in analysis if item["category"] == "streaming"), None)
            self.assertIsNotNone(streaming_item)
            self.assertEqual(streaming_item["spend"], 380.0)
            self.assertEqual(streaming_item["limit"], 300.0)
            self.assertEqual(streaming_item["status"], "AŞILDI 🚨")
            self.assertEqual(streaming_item["overrun"], 80.0)
            self.assertAlmostEqual(streaming_item["ratio_pct"], 126.7, places=1)

            dm.delete_subscription("Pahalı Netflix")
        finally:
            db_file = os.path.join(test_dir, "data", test_db)
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass


class TestSubscriptionFactory(unittest.TestCase):
    def test_factory_variants(self):
        s1 = subscription_factory("Netflix", 200.0, "streaming")
        self.assertIsInstance(s1, StreamingSub)
        self.assertEqual(s1.get_usage_unit(), "saat")

        s2 = subscription_factory("ChatGPT", 500.0, "ai_tool")
        self.assertIsInstance(s2, AIToolSub)
        self.assertEqual(s2.get_usage_unit(), "saat")

        s3 = subscription_factory("MACFit", 1000.0, "fitness")
        self.assertIsInstance(s3, FitnessSub)
        self.assertEqual(s3.get_usage_unit(), "ziyaret")

        s4 = subscription_factory("Bilinmeyen", 100.0, "other")
        self.assertIsInstance(s4, StreamingSub)


class TestVisualizer(unittest.TestCase):
    def test_dashboard_plot_generation(self):
        import matplotlib
        matplotlib.use("Agg")  # Başsız (headless) test modu
        import matplotlib.pyplot as plt
        from visualizer import DashboardVisualizer

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_png = os.path.join(test_dir, "test_dashboard_output.png")

        try:
            viz = DashboardVisualizer(output_dir=test_dir)
            audit_df = pd.DataFrame([
                {
                    "name": "Netflix",
                    "category": "streaming",
                    "monthly_cost": 300.0,
                    "total_usage": 15.0,
                    "cost_per_unit": 20.0,
                    "recommendation": "GOZLE",
                    "annual_waste": 0.0
                },
                {
                    "name": "GymFit",
                    "category": "fitness",
                    "monthly_cost": 1000.0,
                    "total_usage": 0.0,
                    "cost_per_unit": float("inf"),
                    "recommendation": "IPTAL_ET",
                    "annual_waste": 12000.0
                }
            ])
            trend_df = pd.DataFrame([
                {"Month": "Ay 1", "Mevcut_Durum": 1300.0, "Optimize_Edilmis": 300.0},
                {"Month": "Ay 2", "Mevcut_Durum": 2600.0, "Optimize_Edilmis": 600.0}
            ])

            # Matplotlib plt.show headless iken pas geçilir
            orig_show = plt.show
            plt.show = lambda: None
            try:
                viz.plot_dashboard(audit_df, trend_df, save_path=test_png)
            finally:
                plt.show = orig_show
                plt.close("all")

            self.assertTrue(os.path.exists(test_png))
            self.assertGreater(os.path.getsize(test_png), 10000)
        finally:
            if os.path.exists(test_png):
                try:
                    os.remove(test_png)
                except Exception:
                    pass


class TestEndToEndAudit(unittest.TestCase):
    def test_full_audit_with_currency_and_kpis(self):
        from currency_service import CurrencyService

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_db = "test_subaudit_e2e.db"
        dm = DataManager(base_dir=test_dir, db_name=test_db)
        cs = CurrencyService(dm)

        try:
            # TL ve USD abonelikler
            dm.add_subscription("Spotify", "streaming", 60.0, "TL", 1)
            dm.add_subscription("Claude Pro", "ai_tool", 20.0, "USD", 5)

            # Kullanım kayıtları
            dm.log_usage("Spotify", 20.0, "2026-10-01")
            dm.log_usage("Claude Pro", 1.0, "2026-10-02")

            engine = AnalyticsEngine(dm, cs)
            audit_df = engine.perform_full_audit()

            self.assertEqual(len(audit_df), 2)
            self.assertIn("cost_per_unit", audit_df.columns)
            self.assertIn("display_cost", audit_df.columns)

            # USD kuru başarıyla çevrilmiş olmalı (20 USD > 600 TL)
            claude_row = audit_df[audit_df["name"] == "Claude Pro"].iloc[0]
            self.assertGreater(claude_row["monthly_cost"], 500.0)
            self.assertIn("$20", claude_row["display_cost"])

            # KPI Doğrulaması
            kpi = engine.get_summary_kpi(audit_df)
            self.assertEqual(kpi["total_services"], 2)
            self.assertGreater(kpi["total_monthly"], 560.0)

            # 6 Aylık Projeksiyon Doğrulaması
            trend_df = engine.generate_trend_simulation(audit_df, months=6)
            self.assertEqual(len(trend_df), 6)
            self.assertEqual(trend_df["Month"].tolist(), ["Ay 1", "Ay 2", "Ay 3", "Ay 4", "Ay 5", "Ay 6"])

            # Temizlik
            dm.delete_subscription("Spotify")
            dm.delete_subscription("Claude Pro")
        finally:
            db_file = os.path.join(test_dir, "data", test_db)
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass


class TestActivityHeatmap(unittest.TestCase):
    def test_heatmap_calculation_and_streaks(self):
        import datetime
        from data_manager import DataManager
        from analytics import AnalyticsEngine

        test_dir = os.path.dirname(os.path.abspath(__file__))
        test_db = "test_subaudit_heatmap.db"
        dm = DataManager(base_dir=test_dir, db_name=test_db)

        try:
            today = datetime.date.today()
            d1 = (today - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
            d2 = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            d3 = today.strftime("%Y-%m-%d")

            dm.add_subscription("Netflix", "streaming", 200.0, "TL", 1)
            dm.add_subscription("Gym", "fitness", 500.0, "TL", 5)

            # 3 gün üst üste Netflix kullanımı (Streak = 3)
            dm.log_usage("Netflix", 3.0, d1)
            dm.log_usage("Netflix", 2.0, d2)
            dm.log_usage("Netflix", 4.0, d3)

            # Tek gün Gym kullanımı
            dm.log_usage("Gym", 1.0, d1)

            engine = AnalyticsEngine(dm)

            # 1. Genel Isı Haritası
            general_data = engine.get_activity_heatmap_data(sub_name="Tümü", days=30)
            self.assertGreaterEqual(general_data["active_days"], 3)
            self.assertGreaterEqual(general_data["longest_streak"], 3)
            self.assertGreater(general_data["total_usage_sum"], 8.0)
            self.assertIn("insights", general_data)
            self.assertGreater(len(general_data["days"]), 30)

            # 2. Servis Filtreli Isı Haritası (Netflix)
            netflix_data = engine.get_activity_heatmap_data(sub_name="Netflix", days=30)
            self.assertEqual(netflix_data["total_usage_sum"], 9.0) # 3 + 2 + 4
            self.assertGreaterEqual(netflix_data["longest_streak"], 3)

            # 3. Gym Filtreli Isı Haritası
            gym_data = engine.get_activity_heatmap_data(sub_name="Gym", days=30)
            self.assertEqual(gym_data["total_usage_sum"], 1.0)
            self.assertEqual(gym_data["active_days"], 1)

            dm.delete_subscription("Netflix")
            dm.delete_subscription("Gym")
        finally:
            db_file = os.path.join(test_dir, "data", test_db)
            if os.path.exists(db_file):
                try:
                    os.remove(db_file)
                except Exception:
                    pass


class TestBundleOptimizer(unittest.TestCase):
    def test_spotify_youtube_overlap(self):
        from recommendation_engine import BundleAdvisor
        df = pd.DataFrame([
            {"name": "Spotify Premium", "category": "streaming", "monthly_cost": 59.99, "total_usage": 15.0},
            {"name": "YouTube Premium", "category": "streaming", "monthly_cost": 57.99, "total_usage": 30.0}
        ])
        deals = BundleAdvisor.analyze_bundles(df)
        self.assertEqual(len(deals), 1)
        deal = deals[0]
        self.assertEqual(deal["id"], "bundle_spotify_youtube")
        self.assertEqual(deal["sub_to_cancel"], "Spotify Premium")
        self.assertEqual(deal["sub_to_keep"], "YouTube Premium")
        self.assertEqual(deal["monthly_savings"], 59.99)
        self.assertEqual(deal["annual_savings"], round(59.99 * 12.0, 2))

    def test_blutv_hepsiburada_opportunity(self):
        from recommendation_engine import BundleAdvisor
        df = pd.DataFrame([
            {"name": "BluTV Standart", "category": "streaming", "monthly_cost": 99.90, "total_usage": 8.0}
        ])
        deals = BundleAdvisor.analyze_bundles(df)
        self.assertEqual(len(deals), 1)
        deal = deals[0]
        self.assertEqual(deal["id"], "bundle_blutv_hepsiburada")
        self.assertEqual(deal["sub_to_cancel"], "BluTV Standart")
        self.assertAlmostEqual(deal["monthly_savings"], 60.0, places=1) # 99.90 - 39.90
        self.assertIn("Hepsiburada Premium", deal["deal_name"])

    def test_dual_ai_conflict(self):
        from recommendation_engine import BundleAdvisor
        df = pd.DataFrame([
            {"name": "ChatGPT Plus", "category": "ai_tool", "monthly_cost": 650.0, "total_usage": 25.0},
            {"name": "Claude Pro", "category": "ai_tool", "monthly_cost": 650.0, "total_usage": 4.0}
        ])
        deals = BundleAdvisor.analyze_bundles(df)
        deal = next((d for d in deals if d["id"] == "bundle_dual_ai_conflict"), None)
        self.assertIsNotNone(deal)
        # Daha az kullanılan Claude Pro iptal edilmeli
        self.assertEqual(deal["sub_to_cancel"], "Claude Pro")
        self.assertEqual(deal["sub_to_keep"], "ChatGPT Plus")
        self.assertEqual(deal["monthly_savings"], 650.0)

    def test_no_overlap(self):
        from recommendation_engine import BundleAdvisor
        df = pd.DataFrame([
            {"name": "MACFit Gold", "category": "fitness", "monthly_cost": 850.0, "total_usage": 10.0}
        ])
        deals = BundleAdvisor.analyze_bundles(df)
        self.assertEqual(len(deals), 0)


if __name__ == "__main__":
    unittest.main()





