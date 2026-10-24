"""
SmartSubAudit - data_manager.py
İlişkisel Veritabanı (SQLite) & Veri Yönetimi Modülü:
- SQLite3 ile ACID uyumlu, ilişkisel veritabanı yönetimi (Foreign Key & ON DELETE CASCADE)
- Mevcut CSV verilerinden SQLite'a Otomatik Migrasyon (Geçiş)
- Pandas ile SQL Sorguları Entegrasyonu (pd.read_sql_query)
- Dinamik Veri Giriş / Çıkış, Güncelleme (UPDATE) ve Silme (DELETE)
- Güvenli Parametrik Sorgular (SQL Injection korumalı)
"""

import os
import sqlite3
import pandas as pd
from datetime import date
from models import subscription_factory, Subscription


class DataManager:
    def __init__(self, base_dir: str = None, db_name: str = "smart_subaudit.db"):
        if base_dir is None:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        else:
            self.base_dir = base_dir

        self.data_dir = os.path.join(self.base_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.db_path = os.path.join(self.data_dir, db_name)
        self.csv_subs = os.path.join(self.data_dir, "subscriptions.csv")
        self.csv_usage = os.path.join(self.data_dir, "usage_log.csv")
        self._init_database()
        # Otomatik varsayılan yükleme TAMAMEN kaldırıldı.
        # Veritabanı kullanıcının kontrolündedir ve 0 abonelik kalıcı olarak 0 kalır.

    def get_connection(self) -> sqlite3.Connection:
        """
        SQLite veritabanı bağlantısı açar.
        Foreign Key desteğini ve satırların sözlük gibi okunmasını (Row) aktif eder.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")  # Hızlı ve eşzamanlı okuma/yazma
        return conn

    def _init_database(self):
        """İlişkisel tabloları ve indeksleri oluşturur."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Abonelikler Tablosu (Ana Tablo)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                category TEXT NOT NULL,
                monthly_cost REAL NOT NULL CHECK(monthly_cost >= 0),
                currency TEXT NOT NULL DEFAULT 'TL',
                renewal_day INTEGER NOT NULL DEFAULT 1 CHECK(renewal_day BETWEEN 1 AND 31),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Kullanım Kayıtları Tablosu (İlişkili Tablo - Cascade Silme Korumalı)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subscription_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                usage_amount REAL NOT NULL CHECK(usage_amount >= 0),
                usage_unit TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE CASCADE
            );
            """)

            # 3. Sistem Meta Verileri (Migrasyon ve Ayarlar Tablosu)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """)

            # 4. Kategori Bütçe Kotaları Tablosu
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS category_budgets (
                category TEXT PRIMARY KEY COLLATE NOCASE,
                monthly_limit REAL NOT NULL CHECK(monthly_limit >= 0),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Hızlı sorgulama için indeksler
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_subs_name ON subscriptions(name);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_sub_date ON usage_logs(subscription_id, date);")
            conn.commit()

    def _auto_migrate_from_csv(self):
        """
        Sadece veritabanı İLK KEZ oluşturulduğunda bir kerelik çalışır.
        Kullanıcı tüm abonelikleri silip 0'a indirse dahi ASLA tekrar çalışmaz!
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Migrasyon daha önce yapıldı mı kontrol et
                cursor.execute("SELECT value FROM db_metadata WHERE key = 'csv_migrated';")
                res = cursor.fetchone()
                if res and res["value"] == "true":
                    return  # Daha önce yapılmış, kesinlikle çık

                # Henüz yapılmadıysa, CSV dosyaları varsa oku ve aktar
                if os.path.exists(self.csv_subs):
                    df_subs = pd.read_csv(self.csv_subs)
                    for _, row in df_subs.iterrows():
                        cursor.execute("""
                            INSERT OR IGNORE INTO subscriptions (name, category, monthly_cost, currency, renewal_day)
                            VALUES (?, ?, ?, ?, ?);
                        """, (
                            str(row["name"]).strip(),
                            str(row["category"]).strip().lower(),
                            float(row["monthly_cost"]),
                            str(row.get("currency", "TL")).strip().upper(),
                            int(row.get("renewal_day", 1))
                        ))
                    conn.commit()

                # Kullanım kayıtlarını aktar
                if os.path.exists(self.csv_usage):
                    df_usage = pd.read_csv(self.csv_usage)
                    for _, row in df_usage.iterrows():
                        sub_name = str(row["name"]).strip()
                        cursor.execute("SELECT id FROM subscriptions WHERE name = ? COLLATE NOCASE;", (sub_name,))
                        sub_res = cursor.fetchone()
                        if sub_res:
                            sub_id = sub_res["id"]
                            cursor.execute("""
                                INSERT INTO usage_logs (subscription_id, date, usage_amount, usage_unit)
                                VALUES (?, ?, ?, ?);
                            """, (
                                sub_id,
                                str(row["date"]).strip(),
                                float(row["usage_amount"]),
                                str(row["usage_unit"]).strip()
                            ))
                    conn.commit()

                # Migrasyonun tamamlandığını kaydet (bir daha asla otomatik çalışmayacak)
                cursor.execute("INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('csv_migrated', 'true');")
                conn.commit()
        except Exception as e:
            print(f"[UYARI] Otomatik CSV migrasyonunda hata: {e}")

    def reset_to_sample_data(self) -> bool:
        """
        Kullanıcı dilediğinde demo verilerini yeniden yüklemek isterse çalıştırılır.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM usage_logs;")
                cursor.execute("DELETE FROM subscriptions;")
                cursor.execute("DELETE FROM db_metadata WHERE key = 'csv_migrated';")
                conn.commit()
            self._auto_migrate_from_csv()
            return True
        except Exception as e:
            print(f"[HATA] Örnek veriler yüklenemedi: {e}")
            return False

    # =========================================================================
    # ABONELİK (SUBSCRIPTIONS) CRUD İŞLEMLERİ
    # =========================================================================
    def load_subscriptions_df(self) -> pd.DataFrame:
        """Tüm abonelikleri Pandas DataFrame olarak sorgular."""
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT id, name, category, monthly_cost, currency, renewal_day, created_at
                    FROM subscriptions
                    ORDER BY monthly_cost DESC;
                """
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"[HATA] Abonelikler sorgulanamadı: {e}")
            return pd.DataFrame(columns=["id", "name", "category", "monthly_cost", "currency", "renewal_day"])

    def load_subscription_objects(self) -> list[Subscription]:
        """Abonelikleri OOP nesneleri listesi olarak döner (Polymorphism örneği)."""
        df = self.load_subscriptions_df()
        objects = []
        for _, row in df.iterrows():
            sub_obj = subscription_factory(
                name=row["name"],
                monthly_cost=row["monthly_cost"],
                category=row["category"],
                currency=row.get("currency", "TL"),
                renewal_day=row.get("renewal_day", 1)
            )
            objects.append(sub_obj)
        return objects

    def add_subscription(self, name: str, category: str, monthly_cost: float, currency: str = "TL", renewal_day: int = 1) -> bool:
        """Yeni bir aboneliği veritabanına ekler."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO subscriptions (name, category, monthly_cost, currency, renewal_day)
                    VALUES (?, ?, ?, ?, ?);
                """, (
                    name.strip(),
                    category.strip().lower(),
                    float(monthly_cost),
                    currency.strip().upper(),
                    int(renewal_day)
                ))
                conn.commit()
                print(f"[BAŞARILI] '{name}' SQLite veritabanına kaydedildi.")
                return True
        except sqlite3.IntegrityError:
            print(f"[UYARI] '{name}' isimli abonelik zaten veritabanında mevcut!")
            return False
        except Exception as e:
            print(f"[HATA] Abonelik eklenemedi: {e}")
            return False

    def update_subscription(self, sub_id: int, name: str, category: str, monthly_cost: float, currency: str = "TL", renewal_day: int = 1) -> bool:
        """Mevcut bir aboneliğin bilgilerini günceller (UPDATE)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE subscriptions
                    SET name = ?, category = ?, monthly_cost = ?, currency = ?, renewal_day = ?
                    WHERE id = ?;
                """, (
                    name.strip(),
                    category.strip().lower(),
                    float(monthly_cost),
                    currency.strip().upper(),
                    int(renewal_day),
                    int(sub_id)
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"[HATA] Abonelik güncellenemedi: {e}")
            return False

    def update_subscription_cost(self, name: str, new_cost: float) -> bool:
        """Aboneliğin aylık ücretini günceller (Downsell ve plan düşürme için)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE subscriptions
                    SET monthly_cost = ?
                    WHERE name = ? COLLATE NOCASE;
                """, (float(new_cost), name.strip()))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"[HATA] Ücret güncellenemedi: {e}")
            return False

    def delete_subscription(self, name: str) -> bool:
        """
        Aboneliği ve ilişkili tüm kullanım loglarını siler (ON DELETE CASCADE).
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM subscriptions WHERE name = ? COLLATE NOCASE;", (name.strip(),))
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    print(f"[BAŞARILI] '{name}' ve bağlı tüm kayıtlar silindi.")
                return deleted
        except Exception as e:
            print(f"[HATA] Silme işleminde sorun: {e}")
            return False

    def delete_all_subscriptions(self) -> bool:
        """
        Tüm abonelikleri ve bağlı tüm kullanım loglarını siler (veritabanını tamamen boşaltır).
        """
        try:
            with self.get_connection() as conn:
                conn.execute("DELETE FROM usage_logs;")
                conn.execute("DELETE FROM subscriptions;")
                conn.commit()
                print("[BAŞARILI] Tüm abonelikler ve kullanım geçmişi temizlendi.")
                return True
        except Exception as e:
            print(f"[HATA] Tüm abonelikler temizlenemedi: {e}")
            return False

    # =========================================================================
    # KATEGORİ BÜTÇE KOTALARI (CATEGORY BUDGETS) YÖNETİMİ
    # =========================================================================
    DEFAULT_CATEGORY_BUDGETS = {
        "streaming": 450.0,
        "ai_tool": 800.0,
        "fitness": 1000.0
    }

    def set_category_budget(self, category: str, limit: float) -> bool:
        """Kategori için aylık bütçe limitini belirler veya günceller."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO category_budgets (category, monthly_limit, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(category) DO UPDATE SET
                        monthly_limit = excluded.monthly_limit,
                        updated_at = CURRENT_TIMESTAMP;
                """, (category.strip().lower(), float(limit)))
                conn.commit()
                return True
        except Exception as e:
            print(f"[HATA] Kategori bütçesi kaydedilemedi: {e}")
            return False

    def get_category_budgets(self) -> dict:
        """Tüm kategori bütçe limitlerini sözlük olarak döner. Tanımlanmamışsa varsayılanları tamamlar."""
        budgets = dict(self.DEFAULT_CATEGORY_BUDGETS)
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT category, monthly_limit FROM category_budgets;")
                rows = cursor.fetchall()
                for row in rows:
                    budgets[str(row["category"]).lower()] = float(row["monthly_limit"])
        except Exception as e:
            print(f"[UYARI] Bütçe limitleri sorgulanamadı: {e}")
        return budgets


    # =========================================================================
    # KULLANIM KAYITLARI (USAGE LOGS) CRUD İŞLEMLERİ
    # =========================================================================
    def load_usage_df(self) -> pd.DataFrame:
        """
        Kullanım kayıtlarını, ilişkili abonelik adıyla JOIN yaparak çeker.
        """
        try:
            with self.get_connection() as conn:
                query = """
                    SELECT u.id AS log_id, s.name, u.date, u.usage_amount, u.usage_unit, s.category
                    FROM usage_logs u
                    JOIN subscriptions s ON u.subscription_id = s.id
                    ORDER BY u.date DESC, u.id DESC;
                """
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"[HATA] Kullanım logları sorgulanamadı: {e}")
            return pd.DataFrame(columns=["log_id", "name", "date", "usage_amount", "usage_unit", "category"])

    def log_usage(self, name: str, amount: float, log_date: str = None) -> bool:
        """Belirtilen servise ait kullanım miktarını veritabanına kaydeder."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, category FROM subscriptions WHERE name = ? COLLATE NOCASE;", (name.strip(),))
                res = cursor.fetchone()

                if not res:
                    print(f"[UYARI] '{name}' adında kayıtlı bir abonelik bulunamadı.")
                    return False

                sub_id = res["id"]
                cat = res["category"]
                sub_obj = subscription_factory(name=name, monthly_cost=10, category=cat)
                unit = sub_obj.get_usage_unit()

                if log_date is None or not str(log_date).strip():
                    log_date = date.today().strftime("%Y-%m-%d")

                cursor.execute("""
                    INSERT INTO usage_logs (subscription_id, date, usage_amount, usage_unit)
                    VALUES (?, ?, ?, ?);
                """, (
                    sub_id,
                    str(log_date).strip(),
                    float(amount),
                    unit
                ))
                conn.commit()
                print(f"[BAŞARILI] {log_date} tarihinde {name} için {amount} {unit} kaydedildi.")
                return True
        except Exception as e:
            print(f"[HATA] Kullanım kaydedilemedi: {e}")
            return False

    def delete_usage_log(self, log_id: int) -> bool:
        """Tek bir kullanım logunu id ile siler."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM usage_logs WHERE id = ?;", (int(log_id),))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"[HATA] Log silinemedi: {e}")
            return False
