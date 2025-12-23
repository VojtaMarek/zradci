"""
Email integrace – příjem zpráv od hráčů
"""
import imaplib
import email
from email.message import Message
from email.header import decode_header
from typing import List, Dict, Optional
from schemas import Vote
import ssl
import config


def _decode_header(value: Optional[str]) -> str:
    if not value:
        return ''
    parts = decode_header(value)
    decoded = []
    for text, encoding in parts:
        if isinstance(text, bytes):
            decoded.append(text.decode(encoding or 'utf-8', errors='replace'))
        else:
            decoded.append(text)
    return ''.join(decoded)


def _extract_text(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = part.get('Content-Disposition', '')
            if content_type == 'text/plain' and 'attachment' not in disposition:
                charset = part.get_content_charset() or 'utf-8'
                return part.get_payload(decode=True).decode(charset, errors='replace')
    else:
        charset = msg.get_content_charset() or 'utf-8'
        return msg.get_payload(decode=True).decode(charset, errors='replace')

    return ''


def fetch_unread_messages(mark_as_read: bool = True) -> List[Dict[str, str]]:
    """
    Načtení nepřečtených emailů

    Args:
        mark_as_read: zda se mají zprávy označit jako přečtené

    Returns:
        List slovníků: {from, subject, text}
    """
    if not config.IMAP_SERVER or not config.EMAIL_FROM or not config.EMAIL_PASSWORD:
        print("⚠️  IMAP není nakonfigurováno")
        return []

    messages: List[Dict[str, str]] = []

    try:
        context = ssl.create_default_context()
        with imaplib.IMAP4_SSL(config.IMAP_SERVER) as imap:
            imap.login(config.EMAIL_FROM, config.EMAIL_PASSWORD)
            imap.select('INBOX')

            status, data = imap.search(None, 'UNSEEN')
            if status != 'OK':
                return []

            for msg_id in data[0].split():
                _, msg_data = imap.fetch(msg_id, '(RFC822)')
                raw_email = msg_data[0][1]

                msg = email.message_from_bytes(raw_email)

                sender = _decode_header(msg.get('From'))
                subject = _decode_header(msg.get('Subject'))
                text = _extract_text(msg)

                messages.append({
                    'from': sender,
                    'subject': subject,
                    'text': text.strip(),
                })

                if mark_as_read:
                    imap.store(msg_id, '+FLAGS', '\\Seen')

        return messages

    except Exception as e:
        print(f"❌ Chyba při příjmu emailů: {e}")
        return []


def count_email_votes() -> list[Vote]:
    """Načtení a parsování hlasů z emailů s logováním"""
    msgs = fetch_unread_messages()
    votes = []
    
    print(f"📧 Nalezeno {len(msgs)} nepřečtených emailů")
    
    for msg in msgs:
        vote = Vote(
            from_email=msg['from'],
            text=msg['text']
        )
        
        # Logování pro debug
        if vote.from_player_id and vote.for_player_id:
            print(f"✅ Platný hlas: hráč ID {vote.from_player_id} → cíl ID {vote.for_player_id}")
        else:
            print(f"❌ Neplatný hlas z '{msg['from'][:30]}...' (hráč: {vote.from_player_id}, cíl: {vote.for_player_id})")
        
        votes.append(vote)
    
    return votes
