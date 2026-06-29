# Quraşdırma — Lokal

> Bu fayl SƏNİN əl ilə görəcəyin addımları göstərir.
> Kodun hamısını mən yazıram; aşağıdakılar mühit qurğusudur.

## 0. Tələblər (artıq sistemdə var ✓)
- Python 3.10 ✓
- Node.js 22 ✓
- PostgreSQL 14 (Homebrew) ✓

## 1. Verilənlər bazasını yarat
Terminalda işlət:
```bash
# Postgres işləyirmi yoxla (bu maşında port 5433-dədir)
brew services start postgresql@14

# Baza yarat
createdb -p 5433 nexusiq
```
> Əgər `createdb` istifadəçi xətası verərsə, `.env`-dəki
> `DATABASE_URL` istifadəçi/parol/portunu öz Postgres-inə uyğunlaşdır
> (cari konfiqurasiya: `localhost:5433/nexusiq`).

## 2. Backend qur
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # sonra AI key-ləri Addım 4/7-də əlavə edəcəyik
```

İşə sal:
```bash
uvicorn app.main:app --reload --port 8001
```
Yoxla: http://localhost:8001/docs  və  http://localhost:8001/api/v1/health

## 3. Frontend qur
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Yoxla: http://localhost:3000

## Tək əmrlə işə salma (tövsiyə olunur)
Backend və frontend-i ayrıca başlatmaq əvəzinə bir əmr:
```bash
./scripts/dev.sh      # Postgres + backend (8001) + frontend (3000) — sağlamlığı gözləyir
./scripts/status.sh   # backend/db/frontend sağlamlığı
./scripts/stop.sh     # dayandırmaq üçün
```
`dev.sh` artıq işləyəni təkrar başlatmır və xəbərlər hazır olana qədər gözləyir.
Loglar: `~/Library/Logs/nexusiq/{backend,frontend}.log`.

> Qeyd: reboot-dan sonra `./scripts/dev.sh` yenidən işlət. (Avtomatik auto-start
> macOS-da layihə `~/Desktop`-da olduğu üçün Full Disk Access tələb edərdi — bu isə
> təhlükəsizlik güzəşti olduğundan seçilmədi.) Frontend backend qısa kəsiləndə özü
> sağalır (timeout + avtomatik retry).

## Qeyd
- AI açarları (LLM provayderi) yalnız Addım 4 və 7-də lazımdır.
- O addımlara çatanda səndən açarları istəyəcəm.
