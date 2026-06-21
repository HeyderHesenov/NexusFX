# NexusIQ Anomaliya Aşkarlama — Dizayn

Tarix: 2026-06-22

## Məqsəd

Bütün izlənən aktivlərdə (80+) qeyri-adi qiymət + həcm hərəkətlərini avtomatik
aşkarlamaq. Tam pulsuz (mövcud yfinance + Binance datası, sırf hesablama).

## Detection metodu

- Hər aktiv üçün 90 günlük gündəlik tarixçə: close + volume (yfinance).
- Gündəlik gəlir (return) = pct_change(close).
- **Robust Z-score** — median + MAD (Median Absolute Deviation), fat-tail davamlı:
  - `z = 0.6745 * (x - median) / MAD`
  - MAD = 0 olarsa std-ə fallback; std də 0 olarsa aktivi atla.
- `price_z` = sonuncu return-un z-balı.
- `volume_z` = sonuncu həcmin z-balı (həcm seriyası üzərində).
- **Anomaliya şərti**: `|price_z| >= 3` VƏ `volume_z >= 2` (həcm təsdiqi).
- **Şiddət** (price_z mütləq qiymətinə görə):
  - 3–4 → `medium`
  - 4–5 → `high`
  - >=5 → `extreme`

## Komponentlər

- `backend/app/analytics/anomaly.py` — core:
  - `_robust_z(series) -> float` — sonuncu nöqtənin robust z-balı.
  - `scan_asset(key) -> dict | None` — bir aktivi yoxla, anomaliya varsa qaytar.
  - `scan_all() -> list[dict]` — bütün reyestri yoxla, anomaliyaları qaytar.
  - Nəticə 5 dəqiqə keşlənir (digər analytics kimi).
- API: `GET /api/v1/anomalies` → cari anomaliyalar (keşdən).
- Scheduler: `ingest_cycle` sonunda `scan_all()`; yeni `extreme` → web push.
  - Dedup: `set` ilə (tarix + aktiv key) — eyni anomaliya iki dəfə push olmasın.
- Frontend: `/anomalies` səhifəsi — kart/cədvəl, şiddət rəngi, sparkline.

## Data axını

1. Scheduler saatlıq → `scan_all()`.
2. Hər aktiv: 90g tarixçə → price_z, volume_z → şərt yoxla.
3. Anomaliyalar keşə yazılır; pushed-set ilə müqayisə.
4. Yeni extreme → `push_service` ilə bildiriş.
5. Frontend `/anomalies` → JSON çəkir → render.

## Anomaliya obyekti (JSON)

```json
{
  "key": "gold", "label": "Gold", "type": "metal",
  "price_z": 4.2, "volume_z": 3.1, "change_pct": 5.8,
  "severity": "high", "last": 2410.5, "asof": "2026-06-22"
}
```

## Xəta idarəsi

- Aktiv başına yfinance xətası → o aktivi atla, skan dayanmasın.
- Boş/qısa tarixçə (< 30 nöqtə) → atla.
- Push xətası → log, skan davam etsin.
- Son uğurlu keş saxlanır.

## Test

- `_robust_z`: sintetik seriya, bilinən outlier → gözlənilən z.
- MAD = 0 halı → std fallback işləsin.
- std = 0 halı → 0/None, anomaliya yox.
- `scan_asset`: mock tarixçə ilə şərt/şiddət sərhədləri.

## Pulsuzluq

API xərci YOXDUR. AI izah daxil edilmir (1B qərarı). Push pulsuzdur.
