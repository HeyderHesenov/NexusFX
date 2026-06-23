# Radar — Kəşf rejimi (Discovery Mode)

**Tarix:** 2026-06-23
**Status:** Təsdiqlənib (dizayn)

## Kontekst

Mövcud Radar tanınmış majors-ı (BTC, NVDA, Gold...) fürsət balı ilə sıralayır. İstifadəçi əksini istəyir: **bilinməyən, kiçik kapitallı, fundamental perspektivli fürsətlər** — həqiqətən qazanan və gələcəkdə qazana biləcək layihələr/şirkətlər. Majors tamamilə kəşf rejimi ilə əvəzlənir.

3 tab: **Kripto / Səhmlər / Əmtəələr**. Forex çıxarılır (small-cap fürsət anlayışına uyğun deyil). Hər kartda **market cap (MC)** görünür.

## Məqsəd

- Kripto: MC $1M–$50M, **real gəlir qazanan** protokollar (DefiLlama fee/revenue təsdiqi).
- Səhm: MC ≤ $1B small-cap, tematik araşdırma ilə seçilmiş (curated).
- Əmtəə: niş əmtəəni (uran, litium, nadir torpaq, kobalt, mis, qızıl/gümüş junior) istismar edən small-cap şirkətlər.
- Hər tab kateqoriyalaşmış, MC göstərilir, ölü kod yox, SWR ilə optimallaşmış.

## Arxitektura

### Backend — data layer

**`analytics/discovery_crypto.py`** (yeni)
- `_fetch_revenue()` → DefiLlama `GET /overview/fees?...` — protokollar + `geckoId` + `total30d` (30g gəlir). Gəliri həddən yuxarı olanları saxla.
- `_fetch_markets(ids)` → CoinGecko `GET /coins/markets?vs_currency=usd&ids=<gecko_ids>&sparkline=true&price_change_percentage=24h,7d` — MC, qiymət, 7g sparkline, dəyişim (1-2 çağırış, sparkline cavabda gəlir).
- Filtr: MC ∈ [$1M, $50M]. Birləşdir: revenue30d + market data.
- Nəticə item: `{key, label, name, type:"crypto", price, chgPct, spark, mcap, revenue30d, category, githubUrl?}`.

**`analytics/discovery_universe.py`** (yeni) — curated tematik reyestr
- `STOCK_THEMES` və `COMMODITY_THEMES`: `{theme_key: [tickers...]}`.
  - Səhm temaları: AI-power, semis, robotics, nuclear/SMR, cybersecurity, quantum, space və s.
  - Əmtəə temaları: uranium, lithium, rare-earth, copper, cobalt, gold/silver juniors, oil&gas small-cap.
  - Hər tema araşdırılmış real small-cap ticker-lərlə doldurulur (~80–120 ümumi).
- Hər ticker tema ilə teqlənir.

**`analytics/discovery_stocks.py`** (yeni)
- `compute(category)` → universe-dən tema ticker-lərini götür, yfinance ilə toplu qiymət + sparkline (`_registry_overview_sync` patterninə bənzər tək `yf.download`), MC üçün `Ticker.fast_info.market_cap` (fallback `.info["marketCap"]`).
- Filtr: MC ≤ $1B (səhm), əmtəə miner-ləri üçün də uyğun hədd.
- Nəticə item: `{key:ticker, label, type:"stock"|"commodity", price, chgPct, spark, mcap, theme}`.

### Backend — bal (yenilənir)

`analytics/radar.py` yenidən qurulur — yeni `_score`:
- **Kripto:** `momentum` + `revenue` (DefiLlama 30g, log-normallaşmış) + `trend` (7g sparkline). Breakdown: `{momentum, revenue, trend}`.
- **Səhm/Əmtəə:** `momentum` + `trend` + `themeHeat` (temadakı orta momentum). Breakdown: `{momentum, trend, theme}`.
- Hər komponent 0..100, çəkili cəm → `score`. DB xəbər/anomaliya artıq daxil deyil (mikrokaplar üçün uyğunsuz).

### Backend — route

`api/v1/routes/radar.py`:
- `GET /radar?category={crypto|stock|commodity}` → SWR keşli sıralanmış siyahı.
- `GET /radar/{key}/explain?lang=` → on-demand AI izahı (kəşf konteksti).
- `radar.get_radar(category)` SWR ilə uyğun mənbəyə yönləndirir (crypto→discovery_crypto, stock/commodity→discovery_stocks).

### Backend — AI izah

`agents/radar_ai.py` prompt-u kəşf kontekstinə uyğunlaşır: "bu small-cap/mikrokap niyə perspektivlidir" — MC, gəlir/tema əsasında. On-demand, 1 saat keş.

### Backend — keş/performans

- `discovery_crypto`: SWR TTL ~3600s (1 saat). `discovery_stocks`: ~1800s (30 dq).
- `main.py` prewarm-a 3 kateqoriya əlavə.
- Mövcud `swr.py` reuse — bloklamayan stale-while-revalidate.

### Frontend

`app/radar/page.tsx`:
- 3 tab (Kripto / Səhmlər / Əmtəələr).
- Kart: rank + **ScoreRing** (saxlanılır) + label + **MC** + (kripto: gəlir + kateqoriya; səhm/əmtəə: tema teqi) + qiymət/dəyişim + sparkline + breakdown bar-ları + AI izah düyməsi.
- DB xəbər siyahısı çıxır → yerinə tema/gəlir sətri.
- Skeleton/empty saxlanılır.

`lib/api.ts`: `getRadar` saxlanılır (category dəyişir). `types/index.ts`: `RadarItem`-ə `mcap`, `revenue30d?`, `theme?`, `category?` əlavə; breakdown çevik. `RadarCategory` = crypto|stock|commodity. i18n: tema adları + MC/gəlir etiketləri (4 dil). AppNav/RoutePrewarm dəyişmir (link onsuz da var).

## Komponent sərhədləri

- `discovery_crypto` — yalnız CoinGecko+DefiLlama, kripto item qaytarır.
- `discovery_universe` — saf data (tema→ticker xəritəsi), məntiq yox.
- `discovery_stocks` — universe + yfinance, səhm/əmtəə item qaytarır.
- `radar` — orkestr + bal + SWR; mənbələri tanımır, yalnız item alır.
- Hər biri ayrıca test edilə bilər (mock data ilə).

## Xəta idarəsi

- Xarici API xətası (CoinGecko/DefiLlama/yfinance) → boş/köhnə keş qaytar, UI sınmaz (mövcud pattern).
- MC tapılmayan ticker atlanır (filtrdən keçmir).
- AI açarı yoxdursa explain `{ready:false}` qaytarır.

## Verifikasiya

1. `GET /radar?category=crypto` → MC $1-50M aralığında, revenue30d dolu mikrokoinlər.
2. `GET /radar?category=stock` → MC ≤ $1B, tema teqli small-cap-lar.
3. `GET /radar?category=commodity` → niş mədən small-cap-ları.
4. `GET /radar/{key}/explain` yalnız çağırılanda AI işlədir.
5. Frontend `/radar` → 3 tab, MC görünür, breakdown, AI izah; skeleton/empty düzgün; tsc təmiz; ölü kod yox.

## Sayıla bilən risklər / qeydlər

- CoinGecko pulsuz rate-limit → SWR uzun TTL azaldır.
- Curated universe keyfiyyəti manual seçimə bağlıdır (~80-120 ticker, real small-cap, araşdırılmış).
- "Gələcək qazanc" subyektivdir → tema + gəlir + momentum proksi kimi; AI izah tezisi verir.
