# Zrádci - Aplikace pro moderování hry

> 🎮 Backend aplikace pro moderování hry inspirované TV show "The Traitors". Komunikace s hráči přes **email**, plná autonomie bez lidského moderátora.

![ilustrativní obrázek, zradci watch](imgs/Snímek%20obrazovky%202025-12-26%20v 19.34.11.png)

## 📋 Přehled

Aplikace funguje jako **automatický moderátor** hry Zrádci:
- ✅ Náhodně přiřadí role (zrádci vs. věrní)
- ✅ Řídí noční a denní fáze
- ✅ Komunikuje s hráči přes **email**
- ✅ Zpracovává hlasování
- ✅ Ukládá průběh hry do SQLite
- ✅ Vyhodnocuje výsledky
- ✅ 🎙️ **LLM komentáře moderátora** - dramatické komentování hry v reálném čase

## 🏗️ Architektura

```
zradci/
├── main.py           # CLI rozhraní (Typer)
├── game_engine.py    # Herní logika a fáze
├── models.py         # SQLite databáze
├── email_sender.py   # Email komunikace
├── narrator.py       # LLM komentáře moderátora
├── config.py         # Konfigurace
├── storage.db        # Databáze (vytvoří se automaticky)
└── .env              # Env proměnné (email, LLM klíč a model)
```

## 🚀 Instalace

### 1. Naklonování a prostředí

```bash
cd zradci
```

> **Poznámka**: Projekt používá `uv` package manager. Pokud ho nemáte nainstalovaný, viz [uv dokumentace](https://github.com/astral-sh/uv).

### 2. Instalace závislostí

```bash
# Synchronizace závislostí
uv sync

# Instalace v editable mode
uv pip install -e .
```

### 3. Konfigurace

Zkopírujte `.env.example` do `.env` a vyplňte:

```bash
cp .env.example .env
```

V `.env`:
```
# Email konfigurace (povinné pro odesílání zpráv)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=vas-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=vas-email@gmail.com
UPDATE_INTERVAL=5.0

# LLM komentáře moderátora (volitelné)
OPENAI_API_KEY=sk-váš_openai_api_klíč
OPENAI_MODEL=gpt-4o-mini
```

> **Poznámka**: Pro testování není email nutný - aplikace funguje i bez něj a zprávy se vypisují do konzole.
> LLM komentáře jsou také volitelné - bez OpenAI klíče dashboard funguje normálně, pouze bez komentářů moderátora.

## 🎮 Použití

> **Tip**: Můžete používat buď `uv run main.py` nebo přímo `zradci` (po instalaci s `uv pip install -e .`)

### Základní workflow

```bash
# 1. Inicializace databáze
zradci setup

# 2. Přidání hráčů (interaktivně)
zradci add-players
# Nebo jednotlivě:
zradci add-player "Jan Novák" "jan.novak@email.cz"

# 3. Zobrazení hráčů
zradci list-players

# 4. Zahájení hry
zradci start

# 5. Postup hrou (opakujte pro každou fázi)
zradci next

# 6. Zobrazení stavu
zradci status

# 7. Live monitoring (automatická aktualizace)
zradci watch
# nebo s vlastním intervalem:
zradci watch --interval 1

# 8. Zadání hlasu (manuálně)
zradci vote <voter_id> <target_id>

# 9. Simulace hlasování (testování)
zradci simulate-vote

# 10. Zobrazení hlasů
zradci votes

# 11. Historie událostí
zradci events

# Reset hry
zradci reset
```

### Všechny příkazy

| Příkaz | Popis |
|--------|-------|
| `setup` | Inicializace databáze |
| `reset` | Smazání všech dat a reset hry |
| `add-player NAME PHONE` | Přidání jednoho hráče |
| `add-players` | Interaktivní přidání více hráčů |
| `list-players` | Zobrazení seznamu hráčů |
| `start` | Zahájení hry (přiřazení rolí) |
| `next` | Postup do další fáze |
| `status` | Aktuální stav hry |
| `watch` | Live dashboard s automatickou aktualizací |
| `vote VOTER_ID TARGET_ID` | Manuální zadání hlasu |
| `votes` | Zobrazení aktuálních hlasů |
| `simulate-vote` | Simulace hlasování (testování) |
| `events [ROUND]` | Historie událostí |
| `info` | Informace o aplikaci |

### 👀 Live Monitoring

Příkaz `watch` poskytuje real-time dashboard s automatickou aktualizací stavu hry:

```bash
# Základní použití (aktualizace každých 5 sekund)
zradci watch

# Rychlejší aktualizace
zradci watch --interval 2

# Pomalejší aktualizace
zradci watch -i 10
```

**Dashboard zobrazuje:**
- 🎙️ **LLM komentáře moderátora** - dramatické komentáře o průběhu hry (s OpenAI klíčem)
- 🎮 Aktuální kolo a fázi hry
- 👥 Seznam všech hráčů se statusem (živý/mrtvý)
- 🔍 Role (zobrazí se po smrti hráče nebo konci hry)
- 📊 Statistiky (počet živých věrných/zrádců)
- 🗳️ Live hlasování (během fází hlasování)
- 📜 Poslední události
- 🕐 Čas poslední aktualizace

**Ukončení:** Stiskněte `Ctrl+C`

## 🎯 Herní fáze

Hra probíhá v cyklech NOC → DEN:

### 🌙 Noční fáze
1. **night_traitor_chat** - Zrádci dostanou čas na diskuzi
2. **night_vote** - Zrádci hlasují, koho eliminovat
3. **night_revote** - Opakované hlasování, pokud se zrádci neshodli (volitelné)
4. **morning_result** - Oznámení oběti všem hráčům

### 🔄 Opakované noční hlasování
Pokud zrádci nedosáhnou shody (více kandidátů se stejným nejvyšším počtem hlasů):
- Zahájí se **opakované noční hlasování** (fáze `night_revote`)
- Hlasovat mohou opět **všichni zrádci**
- Hlasuje se **pouze pro kandidáty z remíze**
- Pokud je stále remíza → nikdo není eliminován a hra pokračuje

### ☀️ Denní fáze
5. **day_discussion** - Všichni hráči diskutují
6. **day_vote** - Všichni hlasují, koho vyloučit
7. **day_revote** - Opakované hlasování při remíze (volitelné)
8. **day_result** - Vyhodnocení a odhalení role vyloučeného

### 🔄 Opakované hlasování při remíze
Pokud denní hlasování skončí nerozhodně (více hráčů se stejným nejvyšším počtem hlasů):
- Zahájí se **opakované hlasování** (fáze `day_revote`)
- Hlasovat mohou **pouze hráči, kteří NEJSOU v remíze**
- Hlasuje se **pouze pro hráče v remíze**
- Pokud je stále remíza → nikdo není vyloučen a hra pokračuje

### Podmínky vítězství
- ⚔️ **Zrádci vyhrávají**, pokud je jich stejně nebo více než věrných
- 🛡️ **Věrní vyhrávají**, pokud eliminují všechny zrádce

## ⚙️ Konfigurace

V `config.py` můžete upravit:

```python
MIN_PLAYERS = 6          # Minimální počet hráčů
MAX_PLAYERS = 20         # Maximální počet hráčů
TRAITOR_RATIO = 0.25     # 25% hráčů jsou zrádci
```

## 📊 Databázový model

### Tabulky

#### `players`
```sql
id, name, email, role, alive, eliminated_round
```

#### `votes`
```sql
id, voter_id, target_id, round_number, phase, timestamp
```

#### `game_state`
```sql
id, round_number, phase, started, finished, winner, created_at, updated_at
```

#### `events`
```sql
id, round_number, phase, event_type, description, moderator_note, timestamp
```

## 📧 Email komunikace

Aplikace odesílá emailové zprávy hráčům v klíčových momentech hry:

- 🎭 **Přiřazení role** - na začátku hry
- 🌙 **Noční události** - zrádcům po eliminaci
- ☀️ **Denní události** - všem hráčům (výsledky hlasování)
- 🏆 **Konec hry** - výsledky a odhalení všech rolí

### Bez emailu (testování)

Aplikace funguje i bez email konfigurace! Zprávy se jen vypíší do konzole:

```
⚠️  Email není nakonfigurován. Zpráva pro jan.novak@email.cz:
📧 🛡️ Jste VĚRNÝ hráč! Odhalte zrádce dřív, než vás eliminují.
--------------------------------------------------
```

## 🧪 Příklad testovacího průchodu

```bash
# 1. Setup
zradci setup

# 2. Přidání 8 hráčů
zradci add-player "Alice" "alice@example.com"
zradci add-player "Bob" "bob@example.com"
zradci add-player "Charlie" "charlie@example.com"
zradci add-player "Diana" "diana@example.com"
zradci add-player "Eva" "eva@example.com"
zradci add-player "Frank" "frank@example.com"
zradci add-player "Grace" "grace@example.com"
zradci add-player "Henry" "henry@example.com"

# 3. Start
zradci start

# 4. Status
zradci status

# 5. Průchod fázemi s simulací
zradci next                # -> night_traitor_chat
zradci next                # -> night_vote
zradci simulate-vote       # Simulace hlasů zrádců
zradci votes               # Kontrola
zradci next                # -> morning_result
zradci next                # -> day_discussion
zradci next                # -> day_vote
zradci simulate-vote       # Simulace denního hlasování
zradci next                # -> day_result
zradci next                # -> nové kolo nebo game_over

# 6. Kontrola událostí
zradci events
```

## 🔮 Možná rozšíření

- 📊 **Web dashboard** - realtime sledování stavu hry
- 💬 **Chat integrace** - WhatsApp, Telegram, Discord pro diskuze
- 🎥 **Video hovory** - integrace s videokonferencemi pro diskuze
- 🎲 **Speciální role** - guardian, detective, jester
- 📈 **Statistiky** - tracking výkonu hráčů napříč hrami
- 🎨 **Customizace** - JSON konfigurace rolí a pravidel
- 💾 **Export** - PDF reporty z her

## 🛠️ Technologie

- **Python 3.12+**
- **Typer** - CLI framework
- **Rich** - krásný terminálový output
- **SQLite** - databáze
- **SMTP** - email komunikace
- **OpenAI** - LLM komentáře moderátora
- **APScheduler** - plánování úloh (připraveno)
- **python-dotenv** - env proměnné

## 📝 Licence

MIT

## 🤝 Přispívání

Návrhy a pull requesty vítány!

---

Vytvořeno pro jedno silvestrovské setkání na chatě.

