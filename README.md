# Vacation Tracker API

Backend za praćenje godišnjih odmora. Admin uvozi podatke o zaposlenima i njihovim
odmorima (CSV/Excel); zaposleni pregledaju svoje stanje (ukupno/iskorišćeno/preostalo po
godini) i dodaju nove zapise o iskorišćenim danima.

## Tehnološki stek

| Sloj | Tehnologija |
|------|-------------|
| Jezik / Runtime | Python 3.12 |
| Framework | FastAPI |
| Baza | PostgreSQL 16 |
| ORM | SQLAlchemy |
| Migracije šeme | Alembic |
| CSV/Excel import | pandas + openpyxl |
| Autentifikacija | HTTP Basic Auth (bcrypt hash lozinki) |
| Testovi | pytest |
| Kontejnerizacija | Docker + Docker Compose |

## Pokretanje

### Opcija 1 — Docker Compose (preporučeno)

```bash
docker compose up --build
```

Ovo podiže PostgreSQL i aplikaciju, sačeka da baza bude spremna i automatski pusti
Alembic migracije pre starta. Aplikacija je dostupna na `http://localhost:8000`.

Zaustavljanje:
```bash
docker compose down      # čuva podatke
docker compose down -v   # briše i podatke (volume)
```

### Opcija 2 — Lokalno (bez Dockera)

Preduslovi: Python 3.12, pokrenut PostgreSQL.

```bash
createdb vacation-tracker         # ili: psql -c "CREATE DATABASE \"vacation-tracker\";"
                                   # (Alembic pravi tabele, ne i samu bazu)

python -m venv venv
source venv/Scripts/activate      # Windows (git-bash); na Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env              # upiši svoj DATABASE_URL
alembic upgrade head              # kreira tabele

uvicorn app.main:app --reload
```

## Prvi admin nalog i test podaci

CSV import zaposlenih **ne pravi admin naloge** — svi uvezeni nalozi dobijaju rolu
`employee` (CSV nema tu informaciju). Prvi admin nalog se pravi ručno:

```bash
python seed.py
```

Pravi `admin@example.com` / `admin123` (admin) i `employee@example.com` / `employee123`
(employee) — koristi ih za dalje testiranje ili menjaj po potrebi u samom `seed.py`.

Sample fajlovi za import se nalaze u `resources/`. Uvoze se preko Swagger UI-ja
(`/docs`, ulogovan kao admin) ili `curl`-om, tim redom:
1. `employee_profiles.csv` → `POST /admin/employees/import`
2. `vacations_2019.csv`, `vacations_2020.csv`, `vacations_2021.csv` → `POST /admin/vacation-allocations/import`
3. `used_vacation_dates.csv` → `POST /admin/used-vacation-records/import`

Nakon importa, zaposleni se prijavljuju sa email-om i **plain-text lozinkom iz
`employee_profiles.csv`** (npr. `user1@rbt.rs` / `Abc!@#$`) — u bazi se čuva samo bcrypt
hash, pa se originalna lozinka može naći jedino u izvornom CSV fajlu.

## Autentifikacija

Basic Auth na svim endpoint-ima osim `/health` (namerno javan — health-check alati kao
Docker/Kubernetes probe ne mogu da šalju kredencijale). Dve role:

- **admin** — pristupa `/admin/*` (import, pregled svih podataka)
- **employee** — pristupa `/me/*` (samo sopstveni podaci)

## API pregled

Puna interaktivna dokumentacija (probaj zahteve direktno iz browsera): **`http://localhost:8000/docs`**

| Metoda | Ruta | Rola | Opis |
|--------|------|------|------|
| `POST` | `/admin/employees/import` | admin | Import zaposlenih (CSV/Excel) |
| `POST` | `/admin/vacation-allocations/import` | admin | Import ukupnog broja dana po godini |
| `POST` | `/admin/used-vacation-records/import` | admin | Import iskorišćenih dana |
| `GET` | `/admin/employees` | admin | Lista zaposlenih (filter: email, paginacija) |
| `GET` | `/admin/vacation-allocations` | admin | Filter: `employee_id`, `year` |
| `GET` | `/admin/used-vacation-records` | admin | Filter: `employee_id`, `from_date`, `to_date` |
| `GET` | `/me/vacation-summary` | employee | Total/used/available po godini (`year` opciono) |
| `GET` | `/me/used-vacation-records` | employee | Sopstveni zapisi za period |
| `POST` | `/me/used-vacation-records` | employee | Dodavanje novog zapisa |

Import endpoint-i vraćaju izveštaj — validni redovi se upisuju, nevalidni prijavljuju
pojedinačno (jedan loš red ne obara ceo import):
```json
{
  "message": "Vacation days imported successfully",
  "total_records": 56,
  "created": 54,
  "updated": 1,
  "failed": 1,
  "errors": [{ "row": 12, "email": "ghost@rbt.rs", "reason": "Employee not found" }]
}
```

## Testovi

```bash
pytest tests/ -v
```

Zahteva pokrenut PostgreSQL (isti server kao aplikacija — test baza `<ime>-test` se
automatski kreira pri prvom pokretanju, ne dira produkcione podatke).

## Pretpostavke i odluke dizajna

- **Admin nalog van CSV importa** — CSV nema polje za rolu, pa se prvi admin pravi ručno (`seed.py`, vidi gore).
- **"Vacation year,2019" red u `employee_profiles.csv`** — parser traži pravi header red i preskače sve pre njega; import je i idempotentan (proverava da li email već postoji pre unosa).
- **Import nikad ne pada u celini zbog jednog reda** — validacija je po redu (prazan email, nepostojeći employee, duplikat u fajlu su odvojeni razlozi), upis validnih redova je transakcion.
- **Datumi u `used_vacation_dates.csv` su slobodan tekst** (`"Friday, August 30, 2019"`) — parsiraju se po imenu meseca/dana; dodatno se proverava da li se navedeni dan-u-nedelji stvarno poklapa sa datumom (zaštita od greške pri unosu). Ovo očekuje tekstualni format kao u CSV primeru.
- **Vikendi se nikad ne računaju** kao iskorišćeni dan.
- **Period koji prelazi granicu godine** (npr. 28.12–6.1) deli na kraju kalendarske godine — dani se pripisuju svakoj godini posebno, ne ceo period jednoj godini.
- **Total/used/available dani se računaju u trenutku izvršavanja upita** — izbegavaju se dva izvora istine; odabran je pristup normalizacije jer se denormalizacija primenjuje samo kad se po poerformansama izmeri da je neophodno.
- **Pregled podataka od strane admina "For a specific time period" = preklapanje, ne "potpuno unutar opsega"** — period koji delom upada u traženi raspon se i dalje vraća u rezultatu upita (upit za tačno jedan dan tako pronalazi odmor koji u nekom intervalu pokriva i taj dan).
- **Dodavanje novog zapisa od strane zaposlenih** koristi istu overlap proveru kao import, ali dodatno proverava broj raspoloživih dana — po godini pojedinačno, jer period preko granice godine (kraja godine) troši slobodne dane iz naredne godine.
- **Sistem je zamišljen za evidenciju već iskorišćenih dana odmora, ne sistem za rezervaciju** budućeg odsustva, zato je moguće kreirati dane zapis za iskorišćene dane u prošlosti
