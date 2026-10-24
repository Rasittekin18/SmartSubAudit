"""
SmartSubAudit - recommendation_engine.py
Akıllı Alternatif & Tasarruf Reçetesi Motoru (Smart Alternatives & Downsell):
- Kural ve Pazar Veritabanı Tabanlı Eşleştirme Motoru
- Düşük Kullanımlı veya İsraf Statüsündeki Servisler İçin:
  * Downsell (Aynı servisin daha ucuz alt planı)
  * Free-Tier (Ücretsiz sürüm ikamesi)
  * Competitor (Pazardaki daha ekonomik rakip alternatifler)
- Net Aylık ve Yıllık Tasarruf Hesabı
"""

import re
from typing import List, Dict, Optional
import pandas as pd


class AlternativeAdvisor:
    """
    Abonelik türü, adı ve kullanım miktarına göre piyasadaki daha ucuz veya
    ücretsiz alternatifleri tespit edip kişiselleştirilmiş finansal reçete sunar.
    """

    # Piyasa Alternatifleri ve Alt Plan Veritabanı (Knowledge Base)
    CATALOG = {
        "netflix": {
            "keywords": ["netflix"],
            "downsell_plans": [
                {
                    "name": "Netflix Temel Plan (720p / 1 Cihaz)",
                    "cost": 149.99,
                    "type": "DOWNSELL",
                    "badge": "🔽 DAHA UCUZ ALT PLAN",
                    "condition": lambda cost, usage: cost > 180.0,
                    "rationale": "Kullanımınız düşük olduğu için 4K aile paketine gerek yok; tek profilli Temel Plana geçebilirsiniz."
                },
                {
                    "name": "Netflix Standart Plan (1080p / 2 Cihaz)",
                    "cost": 299.99,
                    "type": "DOWNSELL",
                    "badge": "🔽 STANDART PLAN",
                    "condition": lambda cost, usage: cost > 350.0,
                    "rationale": "Özel 4K paket yerine Standart HD plana geçerek bütçenizi rahatlatabilirsiniz."
                }
            ],
            "competitor_alternatives": [
                {
                    "name": "Amazon Prime Video",
                    "cost": 39.00,
                    "type": "COMPETITOR",
                    "badge": "🔄 FİYAT/PERFORMANS RAKİP",
                    "condition": lambda cost, usage: cost > 100.0,
                    "rationale": "Prime Video aylık sadece 39 TL'dir ve Prime kargo avantajıyla birlikte gelir. %85 daha ucuzdur."
                }
            ]
        },
        "chatgpt": {
            "keywords": ["chatgpt", "openai", "gpt-4", "gpt"],
            "downsell_plans": [
                {
                    "name": "Ücretsiz ChatGPT (GPT-4o Free Tier)",
                    "cost": 0.0,
                    "type": "FREE_TIER",
                    "badge": "🎁 ÜCRETSİZ SÜRÜM",
                    "condition": lambda cost, usage: usage < 15.0,
                    "rationale": "Aylık aktif kodlama ve sorgu saatiniz 15 saatin altında kaldı. Ücretsiz GPT-4o web sürümü günlük limitleriyle ihtiyaçlarınızı karşılayacaktır."
                }
            ],
            "competitor_alternatives": [
                {
                    "name": "Claude 3.5 Sonnet (Ücretsiz Web Sürümü)",
                    "cost": 0.0,
                    "type": "COMPETITOR",
                    "badge": "🔄 ÜCRETSİZ RAKİP",
                    "condition": lambda cost, usage: True,
                    "rationale": "Kod yazımı ve metin analizinde Anthropic Claude 3.5 Sonnet ücretsiz sürümü mükemmel bir alternatiftir."
                },
                {
                    "name": "GitHub Copilot Bireysel ($10/ay)",
                    "cost": 490.0,
                    "type": "COMPETITOR",
                    "badge": "💻 DAHA UCUZ GELİŞTİRİCİ PLANI",
                    "condition": lambda cost, usage: cost > 700.0,
                    "rationale": "$20 ödemek yerine doğrudan IDE içinde çalışan $10'lık Copilot planını tercih edebilirsiniz."
                }
            ]
        },
        "spotify": {
            "keywords": ["spotify"],
            "downsell_plans": [
                {
                    "name": "Spotify Ücretsiz (Reklamlı)",
                    "cost": 0.0,
                    "type": "FREE_TIER",
                    "badge": "🎁 ÜCRETSİZ SÜRÜM",
                    "condition": lambda cost, usage: usage < 10.0,
                    "rationale": "Ayda 10 saatten az müzik dinliyorsanız reklamlı ücretsiz sürüm bütçenizi korur."
                },
                {
                    "name": "Spotify Öğrenci / Aile Paylaşımı",
                    "cost": 32.99,
                    "type": "DOWNSELL",
                    "badge": "🔽 İNDİRİMLİ PLAN",
                    "condition": lambda cost, usage: cost > 50.0,
                    "rationale": "Bireysel plan yerine aile üyeleriyle ortak hesap açarak kişi başı maliyeti üçte bire düşürebilirsiniz."
                }
            ],
            "competitor_alternatives": [
                {
                    "name": "YouTube Music (YouTube Premium Dahil)",
                    "cost": 57.99,
                    "type": "COMPETITOR",
                    "badge": "🔄 2'Sİ 1 ARADA",
                    "condition": lambda cost, usage: True,
                    "rationale": "Hem reklamsız YouTube videosu izleyip hem de YouTube Music dinleyerek iki ayrı abonelikten kurtulabilirsiniz."
                }
            ]
        },
        "youtube": {
            "keywords": ["youtube", "youtube premium"],
            "downsell_plans": [
                {
                    "name": "YouTube Aile Planı (Kişi Başı Maliyet)",
                    "cost": 23.0,
                    "type": "DOWNSELL",
                    "badge": "🔽 AİLE PAYLAŞIMI",
                    "condition": lambda cost, usage: cost >= 57.99,
                    "rationale": "5 kişilik aile grubu kurarak kişi başı aylık maliyeti 23 TL'ye düşürebilirsiniz."
                }
            ],
            "competitor_alternatives": [
                {
                    "name": "Brave Browser / Reklam Engelleyici",
                    "cost": 0.0,
                    "type": "FREE_TIER",
                    "badge": "🛡️ 0 TL ÇÖZÜM",
                    "condition": lambda cost, usage: True,
                    "rationale": "Sadece reklamları engellemek için ödüyorsanız, gizlilik odaklı Brave tarayıcısı aynı deneyimi ücretsiz sunar."
                }
            ]
        },
        "gym": {
            "keywords": ["gym", "spor", "fitness", "macfit", "salon"],
            "downsell_plans": [
                {
                    "name": "Gündüz / Off-Peak Üyeliği",
                    "cost": 650.0,
                    "type": "DOWNSELL",
                    "badge": "🔽 SAAT KISITLI PLAN",
                    "condition": lambda cost, usage: cost > 900.0,
                    "rationale": "Akşam yoğun saatler yerine gündüz saatleri geçerli üyelik paketine geçerek %40 tasarruf edebilirsiniz."
                }
            ],
            "competitor_alternatives": [
                {
                    "name": "Nike Training Club & Açık Alan Koşusu",
                    "cost": 0.0,
                    "type": "FREE_TIER",
                    "badge": "🏃‍♂️ 0 TL EV & DIŞ MEKAN",
                    "condition": lambda cost, usage: usage < 4.0,
                    "rationale": "Ayda 4 defadan az gidiyorsanız, salona 1.000+ TL bağlamak yerine açık alanda veya evde ücretsiz antrenman yapabilirsiniz."
                },
                {
                    "name": "Günlük / Giriş Başına Ödeme (Pay-per-visit)",
                    "cost": 150.0,
                    "type": "COMPETITOR",
                    "badge": "🎟️ KULLANDIKÇA ÖDE",
                    "condition": lambda cost, usage: usage <= 2.0,
                    "rationale": "Ayda sadece 1-2 kez gidiyorsanız aylık sabit paket yerine gittiğiniz gün kadar giriş bileti almak çok daha kârlıdır."
                }
            ]
        }
    }

    # Kategori Bazlı Genel Yedek Tavsiyeler (Jenerik Servisler İçin)
    CATEGORY_FALLBACKS = {
        "streaming": [
            {
                "name": "Amazon Prime Video",
                "cost": 39.00,
                "type": "COMPETITOR",
                "badge": "🔄 FİYAT/PERFORMANS",
                "condition": lambda cost, usage: cost > 80.0,
                "rationale": "Daha uygun fiyatlı bir dizi/film platformu olarak aylık 39 TL'lik Prime üyeliğini tercih edebilirsiniz."
            }
        ],
        "ai_tool": [
            {
                "name": "Google AI Studio / Hugging Face Modelleri",
                "cost": 0.0,
                "type": "FREE_TIER",
                "badge": "🎁 ÜCRETSİZ GELİŞTİRİCİ PLANI",
                "condition": lambda cost, usage: cost > 200.0,
                "rationale": "Aylık ücretli yapay zeka aracı yerine cömert ücretsiz limitleri olan Gemini 1.5 Flash veya Hugging Face modellerini kullanabilirsiniz."
            }
        ],
        "fitness": [
            {
                "name": "Evde Egzersiz & Vücut Ağırlığı Antrenmanı",
                "cost": 0.0,
                "type": "FREE_TIER",
                "badge": "💪 0 TL MALİYET",
                "condition": lambda cost, usage: cost > 300.0,
                "rationale": "Kullanılmayan spor üyeliğini dondurup yürüyüş ve ev egzersizlerine geçebilirsiniz."
            }
        ]
    }

    @classmethod
    def get_recommendations_for_subscription(cls, sub_name: str, monthly_cost_try: float, category: str, total_usage: float, current_recommendation: str) -> List[Dict]:
        """
        Belirtilen abonelik için uygun pazar alternatiflerini ve alt paketleri döner.
        Yalnızca IPTAL_ET, DUSUR veya yüksek maliyetli durumlarda devreye girer.
        """
        # Sadece tasarruf fırsatı olan durumlarda öner
        if current_recommendation == "TUT" and total_usage > 20:
            # Kullanıcı zaten çok aktif ve verimli kullanıyor, alternatif zorlamaya gerek yok
            return []

        name_lower = sub_name.strip().lower()
        matched_catalog_key = None

        # 1. Anahtar Kelime Taraması
        for cat_key, config in cls.CATALOG.items():
            for kw in config["keywords"]:
                if kw in name_lower:
                    matched_catalog_key = cat_key
                    break
            if matched_catalog_key:
                break

        recommendations = []

        if matched_catalog_key:
            entry = cls.CATALOG[matched_catalog_key]
            # Downsell paketlerini tara
            for plan in entry.get("downsell_plans", []):
                if plan["condition"](monthly_cost_try, total_usage) and plan["cost"] < monthly_cost_try:
                    savings = monthly_cost_try - plan["cost"]
                    recommendations.append({
                        "name": plan["name"],
                        "cost": plan["cost"],
                        "type": plan["type"],
                        "badge": plan["badge"],
                        "monthly_savings": round(savings, 2),
                        "annual_savings": round(savings * 12.0, 2),
                        "rationale": plan["rationale"]
                    })

            # Rakip alternatiflerini tara
            for alt in entry.get("competitor_alternatives", []):
                if alt["condition"](monthly_cost_try, total_usage) and alt["cost"] < monthly_cost_try:
                    savings = monthly_cost_try - alt["cost"]
                    recommendations.append({
                        "name": alt["name"],
                        "cost": alt["cost"],
                        "type": alt["type"],
                        "badge": alt["badge"],
                        "monthly_savings": round(savings, 2),
                        "annual_savings": round(savings * 12.0, 2),
                        "rationale": alt["rationale"]
                    })

        # 2. Eğer katalogda bulunamadıysa Kategori Bazlı Genel Öneriyi Al
        if not recommendations:
            cat_clean = category.lower().strip()
            fallback_list = cls.CATEGORY_FALLBACKS.get(cat_clean, [])
            for fb in fallback_list:
                if fb["condition"](monthly_cost_try, total_usage) and fb["cost"] < monthly_cost_try:
                    savings = monthly_cost_try - fb["cost"]
                    recommendations.append({
                        "name": fb["name"],
                        "cost": fb["cost"],
                        "type": fb["type"],
                        "badge": fb["badge"],
                        "monthly_savings": round(savings, 2),
                        "annual_savings": round(savings * 12.0, 2),
                        "rationale": fb["rationale"]
                    })

        # Tasarrufa göre en çok kazandıranı başa sırala
        recommendations.sort(key=lambda x: x["monthly_savings"], reverse=True)
        return recommendations


class BundleAdvisor:
    """
    Çapraz Paket (Bundle) & Birleştirme Tasarrufu Motoru (Bundle Optimizer):
    Kullanıcının aktif abonelik sepetini çapraz analiz eder.
    Aynı içeriğe veya avantaja sahip birden fazla servise ayrı ayrı para ödenmesini
    (Örn: Spotify + YouTube Premium çakışması, doğrudan BluTV vs Hepsiburada Premium, vb.)
    tespit ederek konsolidasyon ve birleştirme reçetesi sunar.
    """

    @classmethod
    def analyze_bundles(cls, audit_df: pd.DataFrame) -> List[Dict]:
        """
        Sepetteki abonelikleri tarar ve pazar paket kurallarına göre
        çakışmaları ve konsolidasyon fırsatlarını döner.
        """
        if audit_df is None or audit_df.empty:
            return []

        subs_map = {}
        for _, row in audit_df.iterrows():
            name_clean = str(row["name"]).strip().lower()
            subs_map[name_clean] = row

        opportunities = []

        def find_sub(*keywords):
            for kw in keywords:
                kw_clean = kw.lower()
                for name, row in subs_map.items():
                    if kw_clean in name:
                        return row
            return None

        # -------------------------------------------------------------
        # KURAL 1: Müzik Çakışması (Spotify & YouTube Premium)
        # -------------------------------------------------------------
        spotify_row = find_sub("spotify")
        youtube_row = find_sub("youtube")

        if spotify_row is not None and youtube_row is not None:
            savings = float(spotify_row["monthly_cost"])
            opportunities.append({
                "id": "bundle_spotify_youtube",
                "title": "🎵 Müzik Çakışması: Spotify & YouTube Premium",
                "badge": "MÜZİK KONSOLİDASYONU",
                "action_type": "KONSOLIDE_ET",
                "sub_to_cancel": spotify_row["name"],
                "sub_to_keep": youtube_row["name"],
                "monthly_savings": round(savings, 2),
                "annual_savings": round(savings * 12.0, 2),
                "deal_name": "YouTube Music (YouTube Premium Dahilinde Ücretsiz)",
                "rationale": f"Sepetinizde hem '{spotify_row['name']}' ({savings:.1f} ₺) hem de '{youtube_row['name']}' bulunuyor. YouTube Premium paketine reklamsız YouTube Music zaten dahildir! Spotify'ı iptal ederek aynı müzik arşivini ek ücret ödemeden dinleyebilir ve yılda {savings * 12:,.0f} ₺ tasarruf edebilirsiniz."
            })

        # -------------------------------------------------------------
        # KURAL 2: BluTV / Max & Hepsiburada Premium Entegrasyonu
        # -------------------------------------------------------------
        blutv_row = find_sub("blu", "max")
        hepsiburada_row = find_sub("hepsiburada")

        if blutv_row is not None and hepsiburada_row is None:
            blu_cost = float(blutv_row["monthly_cost"])
            hb_cost = 39.90
            if blu_cost > hb_cost:
                net_savings = blu_cost - hb_cost
                opportunities.append({
                    "id": "bundle_blutv_hepsiburada",
                    "title": "🎬 BluTV / Max ➔ Hepsiburada Premium Geçişi",
                    "badge": "PAZAR AVANTAJ PAKETİ",
                    "action_type": "PAKETE_GEC",
                    "sub_to_cancel": blutv_row["name"],
                    "sub_to_keep": "Hepsiburada Premium",
                    "monthly_savings": round(net_savings, 2),
                    "annual_savings": round(net_savings * 12.0, 2),
                    "deal_name": "Hepsiburada Premium (39.90 ₺/ay — BluTV Hediye)",
                    "rationale": f"'{blutv_row['name']}' servisine doğrudan {blu_cost:.1f} ₺ ödüyorsunuz. Hepsiburada Premium'a (aylık 39.90 ₺) üye olduğunuzda BluTV üyeliği hediye olarak tanımlanır! Doğrudan BluTV faturasını kapatıp HB Premium'a geçerek yılda +{net_savings * 12:,.0f} ₺ tasarruf edebilirsiniz (üstelik kargo bedava ve %3 Hepsipara kazanırsınız)."
                })

        # -------------------------------------------------------------
        # KURAL 3: Çoklu Üretken Yapay Zeka Çakışması (ChatGPT Plus + Claude Pro)
        # -------------------------------------------------------------
        chatgpt_row = find_sub("chatgpt", "openai")
        claude_row = find_sub("claude")

        if chatgpt_row is not None and claude_row is not None:
            gpt_use = float(chatgpt_row.get("total_usage", 0.0))
            claude_use = float(claude_row.get("total_usage", 0.0))

            if gpt_use <= claude_use:
                cancel_target = chatgpt_row
                keep_target = claude_row
            else:
                cancel_target = claude_row
                keep_target = chatgpt_row

            savings = float(cancel_target["monthly_cost"])
            opportunities.append({
                "id": "bundle_dual_ai_conflict",
                "title": "🤖 Çift $20 AI Aracı Çakışması (ChatGPT & Claude)",
                "badge": "YAPAY ZEKA KONSOLİDASYONU",
                "action_type": "KONSOLIDE_ET",
                "sub_to_cancel": cancel_target["name"],
                "sub_to_keep": keep_target["name"],
                "monthly_savings": round(savings, 2),
                "annual_savings": round(savings * 12.0, 2),
                "deal_name": f"{keep_target['name']} + Ücretsiz Web Modelleri",
                "rationale": f"Sepetinizde aynı anda iki premium AI aboneliği ({chatgpt_row['name']} ve {claude_row['name']}) bulunuyor. İki servise birden aylık ~{float(chatgpt_row['monthly_cost']) + float(claude_row['monthly_cost']):,.0f} ₺ ödemek yerine, daha az kullandığınız '{cancel_target['name']}' servisini kapatıp ücretsiz GPT-4o / Claude web sürümüyle destekleyerek yılda {savings * 12:,.0f} ₺ tasarruf edebilirsiniz."
            })

        # -------------------------------------------------------------
        # KURAL 4: Amazon Prime & Video Çakışması
        # -------------------------------------------------------------
        amazon_row = find_sub("amazon", "prime")
        video_services = [r for _, r in audit_df.iterrows() if r["category"] == "streaming" and "prime" not in str(r["name"]).lower()]
        total_video_spend = sum(float(r["monthly_cost"]) for r in video_services)

        if amazon_row is None and total_video_spend >= 350.0:
            opportunities.append({
                "id": "bundle_amazon_prime_value",
                "title": "📦 F/P Devrimi: Amazon Prime Avantaj Paketi",
                "badge": "HEPSİ BİR ARADA PAKET",
                "action_type": "PAKET_ONERISI",
                "sub_to_cancel": "Pahalı Tekil Streaming",
                "sub_to_keep": "Amazon Prime",
                "monthly_savings": 250.0,
                "annual_savings": 3000.0,
                "deal_name": "Amazon Prime (39.00 ₺/ay — Prime Video + Prime Gaming + Kargo)",
                "rationale": f"Streaming için ayda toplam {total_video_spend:.1f} ₺ ödüyorsunuz. Aylık sadece 39 ₺ olan Amazon Prime paketi; Prime Video kütüphanesi, Prime Gaming ücretsiz oyunları ve ücretsiz ertesi gün kargoyu tek faturada sunar. Pahalı bir streaming servisini Prime ile ikame ederek yılda ~3.000 ₺ tasarruf edebilirsiniz."
            })

        # -------------------------------------------------------------
        # KURAL 5: Apple Ekosistemi (Apple Music + iCloud Depolama)
        # -------------------------------------------------------------
        apple_music = find_sub("apple music")
        icloud_row = find_sub("icloud")

        if apple_music is not None and icloud_row is not None:
            apple_music_cost = float(apple_music["monthly_cost"])
            icloud_cost = float(icloud_row["monthly_cost"])
            apple_one_cost = 149.0
            total_current = apple_music_cost + icloud_cost
            if total_current > apple_one_cost:
                net_savings = total_current - apple_one_cost
                opportunities.append({
                    "id": "bundle_apple_one",
                    "title": "🍏 Apple Ekosistem Çakışması: Apple One Paketi",
                    "badge": "APPLE ONE KONSOLİDASYONU",
                    "action_type": "PAKETE_GEC",
                    "sub_to_cancel": f"{apple_music['name']} & {icloud_row['name']}",
                    "sub_to_keep": "Apple One Bireysel",
                    "monthly_savings": round(net_savings, 2),
                    "annual_savings": round(net_savings * 12.0, 2),
                    "deal_name": "Apple One (Apple Music + Apple TV+ + 50GB iCloud + Apple Arcade)",
                    "rationale": f"Ayrı ayrı Apple Music ({apple_music_cost:.1f} ₺) ve iCloud ({icloud_cost:.1f} ₺) ödüyorsunuz (Toplam: {total_current:.1f} ₺). Apple One paketinde tüm bu servisler artı Apple TV+ ve Arcade aylık 149 ₺'ye birleşiyor. Ayda {net_savings:.1f} ₺ tasarruf ederken 2 yeni servise de ücretsiz kavuşursunuz."
                })

        opportunities.sort(key=lambda x: x["monthly_savings"], reverse=True)
        return opportunities

