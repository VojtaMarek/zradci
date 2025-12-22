# Zrádci - Aplikace pro moderování hry

> 🎮 Backend aplikace pro moderování hry inspirované TV show "The Traitors". Komunikace s hráči přes WhatsApp, plná autonomie bez lidského moderátora.

## 📋 Přehled

Aplikace funguje jako **automatický moderátor** hry Zrádci:
- ✅ Náhodně přiřadí role (zrádci vs. věrní)
- ✅ Řídí noční a denní fáze
- ✅ Komunikuje s hráči přes WhatsApp
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
├── whatsapp.py       # WhatsApp Cloud API
├── narrator.py       # LLM komentáře moderátora
├── config.py         # Konfigurace
├── storage.db        # Databáze (vytvoří se automaticky)
└── .env              # Env proměnné (WhatsApp tokeny)
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

### 3. Konfigurace WhatsApp (volitelné)

Zkopírujte `.env.example` do `.env` a vyplňte:

```bash
cp .env.example .env
```

V `.env`:
```
WHATSAPP_TOKEN=váš_token_z_meta_for_developers
WHATSAPP_PHONE_ID=váš_phone_number_id
WHATSAPP_VERIFY_TOKEN=zradci_verify_2024

# LLM komentáře moderátora (volitelné)
OPENAI_API_KEY=sk-váš_openai_api_klíč
OPENAI_MODEL=gpt-4o-mini
```

> **Poznámka**: Pro testování není WhatsApp nutný - aplikace funguje i bez něj a zprávy se vypisují do konzole.
> LLM komentáře jsou také volitelné - bez OpenAI klíče dashboard funguje normálně, pouze bez komentářů moderátora.

## 🎮 Použití

> **Tip**: Můžete používat buď `zradci` nebo přímo `zradci` (po instalaci s `uv pip install -e .`)

### Základní workflow

```bash
# 1. Inicializace databáze
zradci setup
# nebo: zradci setup

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
# Základní použití (aktualizace každé 2 sekundy)
zradci watch

# Rychlejší aktualizace
zradci watch --interval 1

# Pomalejší aktualizace
zradci watch -i 5
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

> **Nová funkce:** Dashboard obsahuje LLM generované komentáře moderátora! 
> Více informací: [LLM_NARRATOR.md](docs/LLM_NARRATOR.md)

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

> 📖 **Podrobnosti:** Viz [REVOTE_FEATURE.md](docs/REVOTE_FEATURE.md)

### Podmínky vítězství
- ⚔️ **Zrádci vyhrávají**, pokud je jich stejně nebo více než věrných
- 🛡️ **Věrní vyhrávají**, pokud eliminují všechny zrádce

## ⚙️ Konfigurace

V `config.py` můžete upravit:

```python
MIN_PLAYERS = 6          # Minimální počet hráčů
MAX_PLAYERS = 20         # Maximální počet hráčů
TRAITOR_RATIO = 0.25     # 25% hráčů jsou zrádci

NIGHT_VOTE_TIMEOUT = 120     # 2 minuty na noční hlasování
DAY_VOTE_TIMEOUT = 300       # 5 minut na denní hlasování
TRAITOR_CHAT_TIMEOUT = 180   # 3 minuty na diskuzi zrádců
```

## 📊 Databázový model

### Tabulky

#### `players`
```sql
id, name, phone, role, alive, eliminated_round
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
id, round_number, phase, event_type, description, timestamp
```

## 📱 WhatsApp integrace

### Nastavení WhatsApp Cloud API

1. Jděte na [Meta for Developers](https://developers.facebook.com/)
2. Vytvořte aplikaci a aktivujte WhatsApp Cloud API
3. Získejte:
   - **Access Token** (dlouhodobý token)
   - **Phone Number ID** (ID vašeho testovacího čísla)
4. Nastavte webhook pro příjem zpráv (volitelné)

### Bez WhatsApp (testování)

Aplikace funguje i bez WhatsApp! Zprávy se jen vypíší do konzole:

```
⚠️  WhatsApp není nakonfigurováno. Zpráva pro 420777123456:
📱 🛡️ Jste VĚRNÝ hráč! Odhalte zrádce dřív, než vás eliminují.
--------------------------------------------------
```

## 🧪 Příklad testovacího průchodu

```bash
# 1. Setup
zradci setup

# 2. Přidání 8 hráčů
zradci add-player "Alice" "420111111111"
zradci add-player "Bob" "420222222222"
zradci add-player "Charlie" "420333333333"
zradci add-player "Diana" "420444444444"
zradci add-player "Eva" "420555555555"
zradci add-player "Frank" "420666666666"
zradci add-player "Grace" "420777777777"
zradci add-player "Henry" "420888888888"

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

- ✅ **LLM moderátor** - dramatické komentáře v reálném čase ([LLM_NARRATOR.md](docs/LLM_NARRATOR.md))
- 📊 **Web dashboard** - realtime sledování stavu hry
- 🎥 **Video hovory** - integrace s videokonferencemi pro diskuze
- 🎲 **Speciální role** - guardian, detective, jester
- 📈 **Statistiky** - tracking výkonu hráčů napříč hrami
- 🌐 **Multi-platform** - kromě WhatsApp také Telegram, Discord
- 🎨 **Customizace** - JSON konfigurace rolí a pravidel
- 💾 **Export** - PDF reporty z her

## 🛠️ Technologie

- **Python 3.12+**
- **Typer** - CLI framework
- **Rich** - krásný terminálový output
- **SQLite** - databáze
- **Requests** - HTTP komunikace
- **OpenAI** - LLM komentáře moderátora
- **APScheduler** - plánování úloh (připraveno)
- **python-dotenv** - env proměnné

## 📝 Licence

MIT

## 🤝 Přispívání

Návrhy a pull requesty vítány!

---

Vytvořeno s ❤️ pro hru Zrádci

