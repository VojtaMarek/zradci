"""
Generátor LLM komentářů moderátora pro hru Zrádci
"""
import config
import models


def generate_narrator_commentary() -> str:
    """
    Vygeneruje LLM komentář moderátora na základě aktuálního stavu hry.
    Komentář NIKDY neprozradí role hráčů!
    """
    # Pokud není nakonfigurován OpenAI klíč, vrátí prázdný komentář
    if not config.OPENAI_API_KEY:
        return ""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.OPENAI_API_KEY)

        # Získat aktuální stav hry
        state = models.get_game_state()
        if not state or not state['started']:
            return ""

        players = models.get_all_players()
        events = models.get_events()

        # Připravit kontext pro LLM (BEZ rolí!)
        context = _prepare_context(state, players, events)

        # Generovat komentář
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """Jsi charismatický moderátor reality show "Zrádci" (The Traitors). 
Tvým úkolem je komentovat aktuální stav hry dramaticky a vtipně, jako by to bylo pro televizi.

DŮLEŽITÁ PRAVIDLA:
1. NIKDY neprozraď role žádného hráče! Neříkej kdo je zrádce a kdo je věrný!
2. Můžeš spekulovat o tom, co se možná stalo, ale NIKDY neříkej s jistotou role
3. Komentuj napětí, vztahy mezi hráči, strategii, ale vždy NEURÁLNĚ
4. Jmenuj konkrétní hráče, ale pouze v souvislosti s tím, co je veřejně známé
5. Buď dramatický, vtipný a napínavý jako dobrý moderátor
6. Piš v češtině, krátce (2-4 věty)
7. Začni uvedením aktuální fáze hry

Příklady DOBRÝCH komentářů:
- "🌙 Právě padá noc a zrádci se schází k úvahám. Napětí je cítit ve vzduchu - kdo z hráčů si dnes nepospí?"
- "☀️ Svítání přináší šokující zprávu - Marie byla eliminována! Ostatní hráči vypadají zděšeně. Může to znamenat, že zrádci hrají chytře?"
- "🗳️ Denní hlasování právě začalo. Petr a Jana si vyměňují podezřívavé pohledy. Bude tohle kolo rozhodující?"

Příklady ŠPATNÝCH komentářů (NIKDY NEDĚLEJ):
- "Jan je zrádce a..."
- "Věrní hráči by měli..."
- "Doporučuji eliminovat Marii, protože..."
"""
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            temperature=0.8,
            max_tokens=200
        )

        commentary = response.choices[0].message.content.strip()
        return commentary

    except Exception as e:
        # Tiché selhání - pokud LLM nefunguje, prostě neukážeme komentář
        return ""


def _prepare_context(state: dict, players: list, events: list) -> str:
    """Připraví kontext pro LLM (BEZ informací o rolích!)"""

    # Fáze
    phase_names = {
        config.PHASE_INIT: "inicializace hry",
        config.PHASE_NIGHT_TRAITOR_CHAT: "noční diskuze zrádců",
        config.PHASE_NIGHT_VOTE: "noční hlasování",
        config.PHASE_NIGHT_REVOTE: "opakované noční hlasování",
        config.PHASE_MORNING_RESULT: "ranní oznámení výsledků",
        config.PHASE_DAY_DISCUSSION: "denní diskuze všech hráčů",
        config.PHASE_DAY_VOTE: "denní hlasování",
        config.PHASE_DAY_REVOTE: "opakované denní hlasování",
        config.PHASE_DAY_RESULT: "večerní oznámení výsledků",
        config.PHASE_GAME_OVER: "konec hry"
    }

    phase = phase_names.get(state['phase'], state['phase'])
    round_num = state['round_number']

    # Statistiky (BEZ rozlišení rolí!)
    alive_players = [p for p in players if p['alive']]
    dead_players = [p for p in players if not p['alive']]

    alive_names = ", ".join([p['name'] for p in alive_players])
    dead_names = ", ".join([p['name'] for p in dead_players]) if dead_players else "zatím nikdo"

    # Poslední události (filtrovat citlivé informace)
    recent_events = []
    for event in events[-5:]:  # Posledních 5 událostí
        # Přeskočit události které prozrazují role
        if event['event_type'] not in ['roles_assigned', 'traitor_vote']:
            recent_events.append(event['description'])

    events_text = "\n".join(recent_events[-3:]) if recent_events else "Žádné významné události"

    # Aktuální hlasy (pokud je hlasovací fáze)
    votes_text = ""
    if state['phase'] in [config.PHASE_NIGHT_VOTE, config.PHASE_NIGHT_REVOTE,
                          config.PHASE_DAY_VOTE, config.PHASE_DAY_REVOTE]:
        votes_list = models.get_votes(round_num, state['phase'])
        if votes_list:
            vote_counts = {}
            for vote in votes_list:
                target = models.get_player(vote['target_id'])
                target_name = target['name']
                vote_counts[target_name] = vote_counts.get(target_name, 0) + 1

            votes_summary = [f"{name} ({count} hlasů)" for name, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)]
            votes_text = f"\nAktuální hlasy: {', '.join(votes_summary)}"

    context = f"""
Aktuální stav hry:

FÁZE: {phase}
KOLO: {round_num}

Živí hráči ({len(alive_players)}): {alive_names}
Eliminovaní hráči: {dead_names}

Nedávné události:
{events_text}
{votes_text}

Vygeneruj krátký, dramatický komentář moderátora o aktuální situaci (2-4 věty).
Pamatuj: NIKDY neprozraď role! Můžeš spekulovat, ale neurčitě.
"""

    return context

