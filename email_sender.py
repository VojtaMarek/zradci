"""
Email integrace pro komunikaci s hráči
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import config
    

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
    if not config.SMTP_SERVER or not config.SMTP_PORT or not config.EMAIL_FROM:
        print(f"⚠️  Email není nakonfigurováno. Zpráva pro {email}:")
        print(f"📧 Předmět: {subject}")
        print(f"📝 {text}")
        print("-" * 50)
        return False

    try:
        # Vytvoření zprávy
        msg = MIMEMultipart()
        msg['From'] = config.EMAIL_FROM
        msg['To'] = email
        msg['Subject'] = subject

        # Přidání těla zprávy
        msg.attach(MIMEText(text, 'plain', 'utf-8'))

        # Připojení k SMTP serveru a odeslání
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            if config.SMTP_USE_TLS:
                server.starttls()

            if config.EMAIL_PASSWORD:
                server.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)

            server.send_message(msg)

        return True
    except Exception as e:
        print(f"❌ Chyba při odesílání emailu na {email}: {e}")
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
    # Testovací odeslání zprávy
    test_email = "test@example.com"
    send_message(test_email, "Ahoj! Toto je testovací zpráva z email integrace.")

