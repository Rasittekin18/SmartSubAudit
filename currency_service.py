"""
SmartSubAudit - currency_service.py
Canlı Döviz Kuru API Entegrasyonu & Para Birimi Dönüştürücü:
- Açık ve ücretsiz REST API üzerinden anlık kurları çekme (open.er-api.com)
- Döviz Kurlarını SQLite & Bellekte Önbelleğe Alma (TTL Caching)
- Çevrimdışı / Bağlantı Hatası Durumunda Güvenli Yedekleme (Fallback)
- USD, EUR, GBP, TRY otomatik dönüştürme ve normalizasyon
"""

import urllib.request
import json
import time
from datetime import datetime


class CurrencyService:
    # İnternet kesilirse veya API geçici olarak yanıt vermezse kullanılacak güvenlik kurları
    DEFAULT_FALLBACK_RATES = {
        "TRY": 1.0,
        "USD": 49.50,
        "EUR": 53.80,
        "GBP": 64.20
    }

    def __init__(self, data_manager=None, cache_ttl_seconds: int = 3600):
        self.dm = data_manager
        self.cache_ttl_seconds = cache_ttl_seconds
        self._memory_cache = {}
        self._last_fetch_time = 0
        self._source = "Belirlenmedi"

    def get_rates(self, force_refresh: bool = False) -> dict[str, float]:
        """
        Canlı döviz kurlarını döner (Her para biriminin 1 biriminin TL karşılığı).
        Örnek: {'USD': 49.68, 'EUR': 53.90, 'GBP': 64.10, 'TRY': 1.0}
        """
        current_time = time.time()

        # Bellek önbelleği geçerli mi?
        if not force_refresh and self._memory_cache and (current_time - self._last_fetch_time < self.cache_ttl_seconds):
            return self._memory_cache

        # Veritabanında yakın zamanda kaydedilmiş kur var mı?
        if not force_refresh and self.dm is not None:
            db_rates, db_time = self._load_from_db()
            if db_rates and (current_time - db_time < self.cache_ttl_seconds):
                self._memory_cache = db_rates
                self._last_fetch_time = db_time
                self._source = "Veritabanı Önbelleği"
                return self._memory_cache

        # Canlı API'den çekmeyi dene
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            req = urllib.request.Request(url, headers={"User-Agent": "SmartSubAudit/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    rates_from_usd = data.get("rates", {})
                    try_rate = rates_from_usd.get("TRY", 49.50)

                    # Tüm kurları TL bazına çevir: 1 Yabancı Para = ? TL
                    computed_rates = {
                        "TRY": 1.0,
                        "USD": round(try_rate, 4),
                        "EUR": round(try_rate / rates_from_usd.get("EUR", 0.92), 4) if "EUR" in rates_from_usd else 53.80,
                        "GBP": round(try_rate / rates_from_usd.get("GBP", 0.78), 4) if "GBP" in rates_from_usd else 64.20
                    }

                    self._memory_cache = computed_rates
                    self._last_fetch_time = current_time
                    self._source = "Canlı API (open.er-api.com)"

                    # Veritabanına kaydet
                    if self.dm is not None:
                        self._save_to_db(computed_rates, current_time)

                    return self._memory_cache
        except Exception as e:
            print(f"[UYARI] Canlı kur API bağlantısı kurulamadı, yedek kurlar devrede: {e}")

        # Başarısız olursa hafızadaki, DB'deki veya varsayılan yedek kurları kullan
        if self._memory_cache:
            return self._memory_cache

        self._memory_cache = self.DEFAULT_FALLBACK_RATES.copy()
        self._last_fetch_time = current_time
        self._source = "Yedek Kurlar (Çevrimdışı)"
        return self._memory_cache

    def convert_to_try(self, amount: float, currency: str = "TL") -> tuple[float, float]:
        """
        Belirtilen para birimindeki tutarı TL'ye dönüştürür.
        Return: (tutarin_tl_karsiligi, kullanilan_kur)
        """
        curr = str(currency).strip().upper()
        rates = self.get_rates()
        rate = rates.get(curr, 1.0)
        amount_try = round(float(amount) * rate, 2)
        return amount_try, rate

    def get_source_info(self) -> dict:
        """Kurların kaynağı ve son güncellenme zamanı hakkında bilgi döner."""
        rates = self.get_rates()
        dt_str = datetime.fromtimestamp(self._last_fetch_time).strftime("%d.%m.%Y %H:%M") if self._last_fetch_time > 0 else "Bilinmiyor"
        return {
            "source": self._source,
            "last_updated": dt_str,
            "usd_try": rates.get("USD", 49.50),
            "eur_try": rates.get("EUR", 53.80),
            "gbp_try": rates.get("GBP", 64.20)
        }

    def _save_to_db(self, rates: dict, timestamp: float):
        try:
            with self.dm.get_connection() as conn:
                conn.execute("INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('currency_rates_json', ?);", (json.dumps(rates),))
                conn.execute("INSERT OR REPLACE INTO db_metadata (key, value) VALUES ('currency_rates_time', ?);", (str(timestamp),))
                conn.commit()
        except Exception:
            pass

    def _load_from_db(self) -> tuple[dict, float]:
        try:
            with self.dm.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM db_metadata WHERE key = 'currency_rates_json';")
                row_json = cursor.fetchone()
                cursor.execute("SELECT value FROM db_metadata WHERE key = 'currency_rates_time';")
                row_time = cursor.fetchone()

                if row_json and row_time:
                    rates = json.loads(row_json["value"])
                    timestamp = float(row_time["value"])
                    return rates, timestamp
        except Exception:
            pass
        return None, 0.0
