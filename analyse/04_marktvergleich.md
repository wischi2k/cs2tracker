# Marktvergleich — CS2 Tracker vs. kommerzielle Anbieter

Stand: 2026-07-31 · Quellen: Websites der Anbieter (siehe Links), Stand Juli 2026

## 1. Die relevanten Vergleichsprodukte

| Anbieter | Typ | Kernangebot |
|---|---|---|
| [Pricempire](https://pricempire.com/) | Web-Plattform (Freemium) | Preisvergleich über 40+ Marktplätze, [Portfolio-Tracking](https://pricempire.com/portfolio) mit Live-Wert, G/V-Analyse, 24h/7d/30d/1y-Charts, Preisalarme, [Markt-Indizes](https://pricempire.com/indexes), API |
| [CSGOSKINS.GG](https://csgoskins.gg/) | Web-Plattform (Freemium) | Preisdaten & Marktstatistiken für jeden Skin über Dutzende Märkte, Portfolio, [Pricing-API](https://csgoskins.gg/api) |
| [Skinpock](https://www.skinpock.com/cs2-portfolio-tracker) | Web-Tool | Einfacher Portfolio-Tracker: Profit/Loss, Inventarwert |
| [CSGAIN](https://csgain.com/) | Web-Tool | Portfolio-Tracker + Inventory-Manager, Steam-Inventar-Anbindung |
| [SteamWebAPI](https://www.steamwebapi.com/) / [cs2.sh](https://cs2.sh/steam-api) / [Skinstrack](https://github.com/SKINSTRACK/CS2-Price-API) | API-Anbieter | Gecachte/aggregierte Preis- und Inventar-APIs als Ersatz für die rate-limitierte Steam-API; cs2.sh u. a. mit OHLC-Historie und 10+ Jahren Steam-Verkaufshistorie |

Dazu Marktplätze mit eigenen Tracking-Funktionen (CSFloat, Skinport, cs.money) — die sind aber primär Handelsplätze, kein fairer Feature-Vergleich.

## 2. Feature-Matrix

| Feature | CS2 Tracker (dieses Projekt) | Pricempire | CSGOSKINS.GG | Skinpock/CSGAIN |
|---|---|---|---|---|
| Preisquellen | 1 (Steam) | 40+ | Dutzende | mehrere |
| Portfolio-Wert live | ✅ (KPI-Streifen) | ✅ | ✅ | ✅ |
| Portfolio-Verlaufschart | ❌ | ✅ | ✅ | ✅ |
| G/V unrealisiert | ✅ (brutto + netto nach Fee) | ✅ | ✅ | ✅ |
| G/V realisiert (Verkäufe) | ❌ | ✅ | ✅ | teils |
| Stückzahlen | ❌ (1 Zeile = 1 Stück) | ✅ | ✅ | ✅ |
| Steam-Inventar-Import | ❌ | ✅ | ✅ | ✅ |
| Preisalarme | ✅ (Telegram, ≤/≥) | ✅ (Web/Discord) | ✅ | teils |
| Periodischer Report | ✅ (Telegram-Summary) | teils (Mail) | ❌ | ❌ |
| Watchlist getrennt vom Bestand | ✅ (Tracking-Typ) | ✅ | ✅ | teils |
| Float/Pattern/Sticker-Werte | ❌ | ✅ | ✅ | teils |
| Mobile-tauglich | ❌ | ✅ | ✅ | ✅ |
| Werbefrei / ohne Account | ✅ | ❌ | ❌ | ❌ |
| Datenhoheit (self-hosted) | ✅ | ❌ | ❌ | ❌ |
| Kosten | 0 € | Freemium/Premium | Freemium | frei/Freemium |

## 3. Einordnung

### Wo die Kommerziellen uneinholbar vorne sind

**Datenbreite und -tiefe.** 40+ Marktplätze, jahrelange Historie, Float-/Pattern-Bewertung, Liquiditätsdaten — das ist ein Infrastruktur-Geschäft mit bezahlten API-Verträgen. Diese Lücke zu schließen ist weder realistisch noch nötig.

### Wo dieses Projekt tatsächlich besser ist

1. **Datenhoheit & Privatsphäre** — kein Account, kein Tracking, keine Verknüpfung des Portfolios mit einer kommerziellen Plattform. Portfoliodaten sind Finanzdaten.
2. **Telegram-first** — der periodische Summary-Report (Top-Gewinner/-Verlierer, Beobachtungsliste) als Push ist in dieser Form bei den Großen kein Standard-Feature; dort muss man die Seite aktiv besuchen.
3. **Netto-Fokus** — die konsequente Anzeige „Netto nach 15 % Steam-Fee" als Hauptsignal ist ehrlicher als der Brutto-Marktwert, den die meisten Plattformen prominent zeigen.
4. **Keine Interessenkonflikte** — kommerzielle Tracker verdienen an Affiliate-Links zu Marktplätzen; ihre „Kauf-Empfehlungen" sind nie neutral.

### Was die Feature-Matrix als dringendste Lücken markiert

Die vier Zeilen, in denen *alle* Kommerziellen ✅ haben und dieses Projekt ❌ — genau das erwartet ein Nutzer heute als Grundausstattung eines Portfolio-Trackers:

1. **Stückzahlen** (bei Kisten-Investments unverzichtbar)
2. **Portfolio-Verlaufschart** (das emotionale Kern-Feature: „mein Depot wächst")
3. **Realisierter Gewinn / Verkaufshistorie**
4. **Mobile-Layout**

Alle vier sind in der [Feature-Roadmap](03_feature_roadmap.md) als Stufe 1 + Mobile eingeplant und ohne externe Abhängigkeiten umsetzbar.

### Lehre aus den API-Anbietern

Dass ein ganzes Ökosystem (SteamWebAPI, cs2.sh, Skinstrack) allein davon lebt, die Rate-Limits der Steam-API wegzucachen, bestätigt die eigene Erfahrung des Projekts (429-Fix, 3s-Delay). Konsequenz für dieses Projekt: Requests minimieren (Quantity-Feature reduziert Duplikat-Fetches), Backoff einbauen, und falls je eine Zweitquelle kommt: Skinport (offene API, ein Request für alle Preise) statt weiterer Steam-Scraping-Endpunkte.

## 4. Fazit-Positionierung

> **„Selbst gehosteter, privater CS2-Portfolio-Tracker mit Telegram-Reports"** — in dieser Nische hat das Projekt keinen direkten Wettbewerber. Es sollte nicht versuchen, Pricempire zu werden, sondern die vier Grundausstattungs-Lücken schließen und die Stärken (Privatsphäre, Push-Reports, Netto-Ehrlichkeit) ausbauen.

## Quellen

- [Pricempire](https://pricempire.com/) · [Portfolio](https://pricempire.com/portfolio) · [Portfolio-Guide](https://pricempire.com/guides/portfolio-guide) · [Indexes](https://pricempire.com/indexes) · [API](https://pricempire.com/api)
- [CSGOSKINS.GG](https://csgoskins.gg/) · [API](https://csgoskins.gg/api)
- [Skinpock CS2 Portfolio Tracker](https://www.skinpock.com/cs2-portfolio-tracker)
- [CSGAIN](https://csgain.com/)
- [SteamWebAPI](https://www.steamwebapi.com/) · [Vergleich CS2-Preis-APIs](https://www.steamwebapi.com/resources/best-cs2-skin-price-apis)
- [cs2.sh Steam-API](https://cs2.sh/steam-api)
- [Skinstrack CS2-Price-API (GitHub)](https://github.com/SKINSTRACK/CS2-Price-API)
