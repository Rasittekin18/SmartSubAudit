"""
SmartSubAudit - models.py
Nesne Tabanlı Programlama (OOP) Modülü:
- Soyut Sınıf (ABC) ve @abstractmethod
- Kapsülleme (Encapsulation - __private nitelikler ve getter metotları)
- Kalıtım (Inheritance)
- Geçersiz Kılma (Overriding) ve Çok Biçimlilik (Polymorphism)
"""

from abc import ABC, abstractmethod
import datetime


class Subscription(ABC):
    """
    Tüm dijital ve fiziksel abonelik türlerinin temelini oluşturan soyut üst sınıf.
    """
    def __init__(self, name: str, monthly_cost: float, currency: str = "TL", renewal_day: int = 1, category: str = "general"):
        # Kapsülleme (Encapsulation): Nitelikler dışarıdan doğrudan değiştirilmesin diye private yapıldı
        self.__name = str(name).strip()
        self.__monthly_cost = float(monthly_cost)
        self.__currency = str(currency).strip().upper()
        self.__renewal_day = int(renewal_day)
        self.__category = str(category).strip().lower()

    # --- Getter Metotları ---
    def get_name(self) -> str:
        return self.__name

    def get_monthly_cost(self) -> float:
        return self.__monthly_cost

    def get_currency(self) -> str:
        return self.__currency

    def get_renewal_day(self) -> int:
        return self.__renewal_day

    def get_category(self) -> str:
        return self.__category

    # --- Ortak Metotlar ---
    def annual_cost(self) -> float:
        """Yıllık toplam abonelik maliyetini döner."""
        return self.__monthly_cost * 12.0

    def days_until_renewal(self) -> int:
        """
        Bir sonraki fatura yenilenme tarihine kaç gün kaldığını hesaplar.
        """
        today = datetime.date.today()
        current_year = today.year
        current_month = today.month

        # Bu ayki yenilenme tarihi
        try:
            target_date = datetime.date(current_year, current_month, self.__renewal_day)
        except ValueError:
            # Örneğin ay 28 veya 30 çekiyorsa ve gün 31 girildiyse ay sonuna yuvarla
            target_date = datetime.date(current_year, current_month, 28)

        if target_date < today:
            # Bu ayın günü geçtiyse, bir sonraki aya bakarız
            if current_month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = current_month + 1
                next_year = current_year

            try:
                target_date = datetime.date(next_year, next_month, self.__renewal_day)
            except ValueError:
                target_date = datetime.date(next_year, next_month, 28)

        delta = (target_date - today).days
        return delta

    # --- Soyut Metotlar (Abstract Methods) ---
    @abstractmethod
    def get_usage_unit(self) -> str:
        """Aboneliğin kullanım ölçü birimini döner (saat, ziyaret, çağrı vb.)."""
        pass

    @abstractmethod
    def calculate_value_score(self, total_usage: float) -> float:
        """
        Birim kullanım başına maliyeti (Cost per Unit) hesaplar.
        0 kullanım varsa float('inf') döner.
        """
        pass

    @abstractmethod
    def get_recommendation(self, total_usage: float) -> tuple[str, str]:
        """
        Kullanım miktarına ve birim maliyete göre tavsiye döner.
        Return: (Karar_Kodu, Aciklama)
        Karar_Kodu: 'TUT', 'GOZLE', 'DUSUR', 'IPTAL_ET'
        """
        pass

    def to_dict(self) -> dict:
        """Sözlük formatında özet döndürür."""
        return {
            "name": self.__name,
            "category": self.__category,
            "monthly_cost": self.__monthly_cost,
            "currency": self.__currency,
            "renewal_day": self.__renewal_day,
            "annual_cost": self.annual_cost(),
            "days_to_renewal": self.days_until_renewal()
        }

    def __str__(self) -> str:
        return f"[{self.__category.upper()}] {self.__name} - {self.__monthly_cost:.2f} {self.__currency}/ay (Yenilenme: {self.days_until_renewal()} gün sonra)"


class StreamingSub(Subscription):
    """
    Film, Dizi, Müzik platformları (Netflix, Spotify, YouTube Premium vb.)
    Kullanım birimi: Saat
    """
    def __init__(self, name: str, monthly_cost: float, currency: str = "TL", renewal_day: int = 1):
        super().__init__(name, monthly_cost, currency, renewal_day, category="streaming")

    def get_usage_unit(self) -> str:
        return "saat"

    def calculate_value_score(self, total_usage: float) -> float:
        """Saatlik izleme/dinleme maliyeti."""
        if total_usage <= 0:
            return float("inf")
        return round(self.get_monthly_cost() / total_usage, 2)

    def get_recommendation(self, total_usage: float) -> tuple[str, str]:
        cost_per_hour = self.calculate_value_score(total_usage)
        # Eşikler: < 15 TL/saat mükemmel, 15-35 iyi, 35-70 yüksek, >70 israf
        if total_usage == 0:
            return ("IPTAL_ET", "Bu ay hiç kullanılmadı! Acil iptal düşünülmeli.")
        elif cost_per_hour <= 15.0:
            return ("TUT", f"Mükemmel verim ({cost_per_hour:.1f} {self.get_currency()}/saat). Düzenli kullanılıyor.")
        elif cost_per_hour <= 35.0:
            return ("GOZLE", f"İyi düzeyde ({cost_per_hour:.1f} {self.get_currency()}/saat). Kullanım devam edebilir.")
        elif cost_per_hour <= 70.0:
            return ("DUSUR", f"Düşük kullanım ({cost_per_hour:.1f} {self.get_currency()}/saat). Aile veya alt pakete geçin.")
        else:
            return ("IPTAL_ET", f"Aşırı pahalı ({cost_per_hour:.1f} {self.get_currency()}/saat). İptal ederek tasarruf edin.")


class AIToolSub(Subscription):
    """
    Yapay Zeka ve Yazılım Üretkenlik Araçları (ChatGPT Plus, GitHub Copilot, Claude vb.)
    Kullanım birimi: Saat (Çalışma süresi)
    """
    def __init__(self, name: str, monthly_cost: float, currency: str = "TL", renewal_day: int = 1):
        super().__init__(name, monthly_cost, currency, renewal_day, category="ai_tool")

    def get_usage_unit(self) -> str:
        return "saat"

    def calculate_value_score(self, total_usage: float) -> float:
        """Çalışma saati başına maliyet."""
        if total_usage <= 0:
            return float("inf")
        return round(self.get_monthly_cost() / total_usage, 2)

    def get_recommendation(self, total_usage: float) -> tuple[str, str]:
        cost_per_hour = self.calculate_value_score(total_usage)
        # AI araçları mesleki/eğitim amaçlı olduğundan tolerans eşiği daha yüksektir
        if total_usage == 0:
            return ("IPTAL_ET", "Hiç kod/proje üretilmedi. Ücretsiz sürüme dönün.")
        elif cost_per_hour <= 25.0:
            return ("TUT", f"Yüksek yatırım getirisi ({cost_per_hour:.1f} {self.get_currency()}/saat). Çok aktif kullanılıyor.")
        elif cost_per_hour <= 60.0:
            return ("GOZLE", f"Makul verim ({cost_per_hour:.1f} {self.get_currency()}/saat).")
        elif cost_per_hour <= 120.0:
            return ("DUSUR", f"Düşük mesai ({cost_per_hour:.1f} {self.get_currency()}/saat). İhtiyaç anında aylık açın.")
        else:
            return ("IPTAL_ET", f"Verimsiz harcama ({cost_per_hour:.1f} {self.get_currency()}/saat). Ücretsiz alternatiflere bakın.")


class FitnessSub(Subscription):
    """
    Spor Salonu, Yüzme Havuzu, Stüdyo Abonelikleri
    Kullanım birimi: Ziyaret
    """
    def __init__(self, name: str, monthly_cost: float, currency: str = "TL", renewal_day: int = 1):
        super().__init__(name, monthly_cost, currency, renewal_day, category="fitness")

    def get_usage_unit(self) -> str:
        return "ziyaret"

    def calculate_value_score(self, total_usage: float) -> float:
        """Ziyaret başına maliyet."""
        if total_usage <= 0:
            return float("inf")
        return round(self.get_monthly_cost() / total_usage, 2)

    def get_recommendation(self, total_usage: float) -> tuple[str, str]:
        cost_per_visit = self.calculate_value_score(total_usage)
        # Ayda 8-12 gün gidiş hedeflenir
        if total_usage == 0:
            return ("IPTAL_ET", "Salona bu ay hiç gidilmedi! Kart dondurma veya iptal önerilir.")
        elif cost_per_visit <= 80.0:
            return ("TUT", f"Mükemmel devamlılık ({cost_per_visit:.1f} {self.get_currency()}/ziyaret).")
        elif cost_per_visit <= 150.0:
            return ("GOZLE", f"Ortalama katılım ({cost_per_visit:.1f} {self.get_currency()}/ziyaret). Haftada en az 2 gün hedefleyin.")
        elif cost_per_visit <= 300.0:
            return ("DUSUR", f"Az gidildi ({cost_per_visit:.1f} {self.get_currency()}/ziyaret). Kontörlü/günlük giriş daha karlı.")
        else:
            return ("IPTAL_ET", f"Salon bağışı yapılmış ({cost_per_visit:.1f} {self.get_currency()}/ziyaret)! İptal edilmeli.")


def subscription_factory(name: str, monthly_cost: float, category: str, currency: str = "TL", renewal_day: int = 1) -> Subscription:
    """
    Fabrika Fonksiyonu (Factory Pattern):
    Kategoriye göre uygun Subscription alt sınıfı nesnesini otomatik üretir.
    """
    cat = str(category).strip().lower()
    if cat in ["streaming", "yayın", "medya"]:
        return StreamingSub(name, monthly_cost, currency, renewal_day)
    elif cat in ["ai_tool", "ai", "yazılım", "software"]:
        return AIToolSub(name, monthly_cost, currency, renewal_day)
    elif cat in ["fitness", "spor", "gym"]:
        return FitnessSub(name, monthly_cost, currency, renewal_day)
    else:
        # Varsayılan olarak Streaming mantığı ile çalıştır
        return StreamingSub(name, monthly_cost, currency, renewal_day)
