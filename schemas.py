from pydantic import BaseModel
from typing import Optional
import re


class Vote(BaseModel):
    from_email: str
    text: str

    @property
    def for_player_id(self) -> Optional[int]:
        """Extrakce ID hráče z textu emailu - podporuje různé formáty"""
        try:
            first_line = self.text.splitlines()[0].strip()
            # Pokus o přímé číslo
            if first_line.isdigit():
                return int(first_line)
            
            # Hledání čísla v textu (např. "hlasuju pro 3", "player 5")
            match = re.search(r'\b(\d+)\b', first_line)
            if match:
                return int(match.group(1))
            
            return None
        except (IndexError, ValueError, AttributeError) as e:
            print(f"⚠️  Nepodařilo se parsovat hlas z: '{self.text[:50]}...': {e}")
            return None

    @property
    def from_player_id(self) -> Optional[int]:
        """Extrakce ID hráče z emailové adresy - s error handlingem"""
        from models import get_player_by_email

        try:
            # Podporuje různé formáty:
            # "email@domain.com"
            # "Name <email@domain.com>"
            # "\"Name\" <email@domain.com>"
            if "<" in self.from_email and ">" in self.from_email:
                email_only = self.from_email.split("<", 1)[1].split(">", 1)[0].strip()
            else:
                email_only = self.from_email.strip()
            
            player = get_player_by_email(email_only)
            if not player:
                print(f"⚠️  Hráč s emailem '{email_only}' nebyl nalezen v databázi")
                return None
            
            player_id = player.get("id")
            if not player_id:
                print(f"⚠️  Hráč s emailem '{email_only}' nemá ID")
                return None
                
            return player_id
        except (IndexError, AttributeError, TypeError) as e:
            print(f"⚠️  Chyba při parsování emailu '{self.from_email}': {e}")
            return None
