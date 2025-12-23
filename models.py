"""
Databázové modely a operace pro hru Zrádci
"""
import sqlite3
from typing import List, Optional, Tuple
from contextlib import contextmanager
import config


@contextmanager
def get_db():
    """Context manager pro databázové připojení"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Inicializace databáze"""
    with get_db() as conn:
        cur = conn.cursor()

        # Tabulka hráčů
        cur.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                role TEXT,
                alive INTEGER DEFAULT 1,
                eliminated_round INTEGER
            )
        """)

        # Tabulka hlasů
        cur.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voter_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                phase TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (voter_id) REFERENCES players (id),
                FOREIGN KEY (target_id) REFERENCES players (id)
            )
        """)

        # Tabulka stavu hry
        cur.execute("""
            CREATE TABLE IF NOT EXISTS game_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                round_number INTEGER DEFAULT 1,
                phase TEXT DEFAULT 'inicializace',
                started INTEGER DEFAULT 0,
                finished INTEGER DEFAULT 0,
                winner TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabulka zpráv/událostí
        cur.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_number INTEGER,
                phase TEXT,
                event_type TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


def reset_game():
    """Resetování hry - smazání všech dat"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM players")
        cur.execute("DELETE FROM sqlite_sequence WHERE name='players'")
        cur.execute("DELETE FROM votes")
        cur.execute("DELETE FROM game_state")
        cur.execute("DELETE FROM events")
        conn.commit()


# === HRÁČI ===

def add_player(name: str, email: str) -> int:
    """Přidání hráče"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO players (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        return cur.lastrowid


def get_player(player_id: int) -> Optional[dict]:
    """Získání hráče podle ID"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_player_by_email(email: str) -> Optional[dict]:
    """Získání hráče podle emailové adresy"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_players() -> List[dict]:
    """Získání všech hráčů"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players ORDER BY id")
        return [dict(row) for row in cur.fetchall()]


def get_alive_players() -> List[dict]:
    """Získání živých hráčů"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE alive = 1 ORDER BY id")
        return [dict(row) for row in cur.fetchall()]


def get_players_by_role(role: str, alive_only: bool = True) -> List[dict]:
    """Získání hráčů podle role"""
    with get_db() as conn:
        cur = conn.cursor()
        query = "SELECT * FROM players WHERE role = ?"
        params = [role]
        if alive_only:
            query += " AND alive = 1"
        query += " ORDER BY id"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def update_player_role(player_id: int, role: str):
    """Nastavení role hráče"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE players SET role = ? WHERE id = ?", (role, player_id))
        conn.commit()


def eliminate_player(player_id: int, round_number: int):
    """Eliminace hráče"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE players SET alive = 0, eliminated_round = ? WHERE id = ?",
            (round_number, player_id)
        )
        conn.commit()


# === HERNÍ STAV ===

def init_game_state():
    """Inicializace herního stavu"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO game_state (id, round_number, phase, started) VALUES (1, 1, ?, 1)",
            (config.PHASE_INIT,)
        )
        conn.commit()


def get_game_state() -> Optional[dict]:
    """Získání aktuálního stavu hry"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM game_state WHERE id = 1")
        row = cur.fetchone()
        return dict(row) if row else None


def update_game_phase(phase: str):
    """Aktualizace fáze hry"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE game_state SET phase = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (phase,)
        )
        conn.commit()


def increment_round():
    """Zvýšení čísla kola"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE game_state SET round_number = round_number + 1, updated_at = CURRENT_TIMESTAMP WHERE id = 1"
        )
        conn.commit()


def end_game(winner: str):
    """Ukončení hry"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE game_state SET finished = 1, winner = ?, phase = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (winner, config.PHASE_GAME_OVER)
        )
        conn.commit()


# === HLASOVÁNÍ ===

def add_vote(voter_id: int, target_id: int, round_number: int, phase: str):
    """Přidání hlasu"""
    with get_db() as conn:
        cur = conn.cursor()
        # Nejdřív smazat předchozí hlas tohoto hráče v tomto kole a fázi
        cur.execute(
            "DELETE FROM votes WHERE voter_id = ? AND round_number = ? AND phase = ?",
            (voter_id, round_number, phase)
        )
        # Přidat nový hlas
        cur.execute(
            "INSERT INTO votes (voter_id, target_id, round_number, phase) VALUES (?, ?, ?, ?)",
            (voter_id, target_id, round_number, phase)
        )
        conn.commit()


def get_votes(round_number: int, phase: str) -> List[dict]:
    """Získání hlasů pro dané kolo a fázi"""
    from email_receiver import count_email_votes
    from voting import vote as validate_and_vote
    import time

    # Zpracování emailových hlasů s plnou validací
    email_votes = count_email_votes()
    for v in email_votes:
        if v.from_player_id and v.for_player_id:
            # Volání vote() z voting.py, které provede všechny validace a přidá hlas
            validate_and_vote(voter_id=v.from_player_id, target_id=v.for_player_id)
    time.sleep(0.1)

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM votes WHERE round_number = ? AND phase = ? ORDER BY timestamp",
            (round_number, phase)
        )
        return [dict(row) for row in cur.fetchall()]


def count_votes(round_number: int, phase: str) -> List[Tuple[int, int]]:
    """Spočítání hlasů - vrací [(target_id, count), ...]"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT target_id, COUNT(*) as count 
            FROM votes 
            WHERE round_number = ? AND phase = ? 
            GROUP BY target_id 
            ORDER BY count DESC
            """,
            (round_number, phase)
        )
        return [(row['target_id'], row['count']) for row in cur.fetchall()]


# === UDÁLOSTI ===

def add_event(round_number: int, phase: str, event_type: str, description: str):
    """Přidání události do logu"""
    with get_db() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (round_number, phase, event_type, description) VALUES (?, ?, ?, ?)",
            (round_number, phase, event_type, description)
        )
        conn.commit()


def get_events(round_number: Optional[int] = None) -> List[dict]:
    """Získání událostí"""
    with get_db() as conn:
        cur = conn.cursor()
        if round_number:
            cur.execute("SELECT * FROM events WHERE round_number = ? ORDER BY timestamp", (round_number,))
        else:
            cur.execute("SELECT * FROM events ORDER BY timestamp")
        return [dict(row) for row in cur.fetchall()]

if __name__ == "__main__":
    r=get_votes(1, ".")