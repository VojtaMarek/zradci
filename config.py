"""
Konfigurační soubor pro aplikaci Zrádci
"""
import os
from dotenv import load_dotenv

load_dotenv(override=False)

# Email konfigurace
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.seznam.cz")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.seznam.cz")
UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", 2.0))

# OpenAI API konfigurace
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Databáze
DATABASE_PATH = "storage.db"

# Herní nastavení
MIN_PLAYERS = 6
MAX_PLAYERS = 20
TRAITOR_RATIO = 0.25  # 25% hráčů jsou zrádci (minimálně 2)

# # Časové limity (v sekundách)
# NIGHT_VOTE_TIMEOUT = 120  # 2 minuty pro noční volbu
# DAY_VOTE_TIMEOUT = 300    # 5 minut pro denní hlasování
# TRAITOR_CHAT_TIMEOUT = 180  # 3 minuty pro diskuzi zrádců

# Herní fáze, možné orientační časy začátku fází
PHASE_INIT = "inicializace"
PHASE_NIGHT_TRAITOR_CHAT = "nocni_diskuze_zradcu" # 22:00
PHASE_NIGHT_VOTE = "nocni_hlasovani"  # 23:00
PHASE_NIGHT_REVOTE = "nocni_opakovane_hlasovani"  # Opakované noční hlasování při remíze
PHASE_MORNING_RESULT = "rano_vysledek"  # 6:00
PHASE_DAY_DISCUSSION = "denni_diskuze"  # 8:00
PHASE_DAY_VOTE = "denni_hlasovani"  # 18:00
PHASE_DAY_REVOTE = "denni_opakovane_hlasovani"  # Opakované denní hlasování při remíze
PHASE_DAY_RESULT = "den_vysledek"  # 20:00
PHASE_GAME_OVER = "konec_hry"

# Role
ROLE_TRAITOR = "zrádce"
ROLE_FAITHFUL = "věrný"

# Zprávy
MESSAGES = {
    "game_start": "🎮 Hra Zrádci začíná! Obdržíte svou roli v soukromé zprávě.",
    "role_traitor": "⚔️ Jste ZRÁDCE! Vaším cílem je eliminovat věrné hráče.\n\nDalší zrádci: {traitors}",
    "role_faithful": "🛡️ Jste VĚRNÝ hráč! Odhalte zrádce dřív, než vás eliminují.",
    "night_begins": "🌙 Noc padá... Zrádci se schází.",
    "night_vote_prompt": "⚔️ Zrádci, vyberte hráče k eliminaci:\n\n{players}\n\nOdpovězte číslem hráče.",
    "night_revote_prompt": "🔄 OPAKOVANÉ HLASOVÁNÍ! Musíte se shodnout (poslední šance).\n\nVyberte:\n\n{players}\n\nOdpovězte číslem hráče.",
    "morning_result": "☀️ Svítání... Během noci byl eliminován: {player}",
    "morning_result_none": "☀️ Svítání... Noc proběhla klidně, nikdo nebyl eliminován.",
    "day_discussion": "💬 Denní diskuze začíná. Promluvte si mezi sebou a hlasujte.",
    "day_vote_prompt": "🗳️ Hlasování! Vyberte hráče k vyloučení:\n\n{players}\n\nOdpovězte číslem hráče.",
    "day_revote_prompt": "🔄 OPAKOVANÉ HLASOVÁNÍ! Remíza mezi: {tied_players}\n\nHlasovat můžou pouze ti, kteří NEJSOU v remíze.\n\nVyberte:\n\n{players}\n\nOdpovězte číslem hráče.",
    "day_revote_announcement": "⚖️ Remíza! Opakované hlasování. Kandidáti: {tied_players}\n\nHlasovat můžou pouze hráči, kteří nejsou v remíze.",
    "day_result": "📊 Výsledek hlasování: {player} byl vyloučen. Role: {role}",
    "day_result_tie": "📊 Hlasování skončilo nerozhodně. Nikdo není vyloučen.",
    "traitors_win": "⚔️ ZRÁDCI ZVÍTĚZILI! 🎉",
    "faithful_win": "🛡️ VĚRNÍ HRÁČI ZVÍTĚZILI! 🎉",
    "status_update": "📊 Status:\n👥 Živí hráči: {alive}\n⚔️ Zrádci: {traitors}\n🛡️ Věrní: {faithful}\n🔄 Kolo: {round}"
}

