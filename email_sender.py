"""
Email integrace pro komunikaci s hráči
"""
import smtplib
from email.message import EmailMessage
from typing import Optional
import ssl
import config
from email_validator import EmailNotValidError, validate_email


def is_valid_email(email: str) -> bool:
    try:
        r = validate_email(email)
        return True if r else False
    except Exception:
        return False


def send_message(email: str, text: str, subject: str = "Hra Zrádci") -> bool:
    """
    Odeslání emailové zprávy

    Args:
        email: Email adresa příjemce
        text: Text zprávy
        subject: Předmět emailu

    Returns:
        True pokud byla zpráva úspěšně odeslána
    """
    if not is_valid_email(email):
        print(f"❌ Chyba při odesílání emailu na '{email}': email není platný")
        return False

    if not config.SMTP_SERVER or not config.SMTP_PORT or not config.EMAIL_FROM:
        print(f"⚠️  Email není nakonfigurováno. Zpráva pro {email}:")
        print(f"📧 Předmět: {subject}")
        print(f"📝 {text}")
        print("-" * 50)
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = config.EMAIL_FROM
        msg['To'] = email
        msg.set_content(text)

        context = ssl.create_default_context() # Vytvoří bezpečný SSL kontext
        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, context=context) as server:
            server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
            server.send_message(msg)

        print("Email úspěšně odeslán!")
        return True
    except Exception as e:
        print(f"❌ Chyba při odesílání emailu na '{email}': {e}")
        return False


def send_message_to_multiple(emails: list[str], text: str, subject: str = "Hra Zrádci"):
    """
    Odeslání zprávy více příjemcům

    Args:
        emails: Seznam emailových adres
        text: Text zprávy
        subject: Předmět emailu
    """
    for email in emails:
        send_message(email, text, subject)


def validate_email(email: str) -> bool:
    """
    Jednoduchá validace emailové adresy

    Args:
        email: Emailová adresa k ověření

    Returns:
        True pokud má email validní formát
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


# Simulace příchozích zpráv pro testování
_pending_messages = {}

def simulate_incoming_message(email: str, text: str):
    """Pro testování - simuluje příchozí zprávu"""
    _pending_messages[email] = text


def get_simulated_message(email: str) -> Optional[str]:
    """Získání simulované zprávy"""
    return _pending_messages.pop(email, None)


if __name__ == "__main__":
    from dotenv import load_dotenv
    from models import get_all_players

    load_dotenv()

    send_message("fakeemail", "hoho")

    # Testovací odeslání zpráv všem hráčům
    #emails = [p.get("email") for p in get_all_players()]
    #send_message_to_multiple(emails, "Ahoj! Toto je testovací zpráva z email integrace.")

