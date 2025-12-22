"""
Hlavní herní logika pro hru Zrádci
"""
import random
from typing import List
from rich.console import Console
from rich.table import Table
import config
import models
import email_sender


console = Console()


def assign_roles():
    """Náhodné přiřazení rolí hráčům"""
    players = models.get_all_players()

    if len(players) < config.MIN_PLAYERS:
        console.print(f"[red]❌ Nedostatek hráčů! Minimum je {config.MIN_PLAYERS}[/red]")
        return False

    # Výpočet počtu zrádců
    num_traitors = max(2, int(len(players) * config.TRAITOR_RATIO))

    console.print(f"[yellow]🎲 Rozdávám role pro {len(players)} hráčů...[/yellow]")
    console.print(f"[yellow]⚔️  Zrádců: {num_traitors}[/yellow]")
    console.print(f"[yellow]🛡️  Věrných: {len(players) - num_traitors}[/yellow]")

    # Náhodné zamíchání
    random.shuffle(players)

    # Přiřazení rolí
    traitors = []
    for i, player in enumerate(players):
        role = config.ROLE_TRAITOR if i < num_traitors else config.ROLE_FAITHFUL
        models.update_player_role(player['id'], role)
        if role == config.ROLE_TRAITOR:
            traitors.append(player)

    # Odeslání rolí hráčům
    traitors_names = ", ".join([t['name'] for t in traitors])

    for player in players:
        player_data = models.get_player(player['id'])
        if player_data['role'] == config.ROLE_TRAITOR:
            other_traitors = [t['name'] for t in traitors if t['id'] != player['id']]
            message = config.MESSAGES['role_traitor'].format(
                traitors=", ".join(other_traitors) if other_traitors else "Jste jediný zrádce!"
            )
        else:
            message = config.MESSAGES['role_faithful']

        email_sender.send_message(player_data['email'], message)

    models.add_event(1, config.PHASE_INIT, "roles_assigned", f"Role přiřazeny: {num_traitors} zrádců")
    console.print("[green]✅ Role přiřazeny a odeslány hráčům[/green]")
    return True


def start_game():
    """Zahájení hry"""
    console.print("[bold cyan]🎮 SPOUŠTÍM HRU ZRÁDCI[/bold cyan]")

    # Inicializace stavu
    models.init_game_state()

    # Přiřazení rolí
    if not assign_roles():
        return False

    # Odeslání úvodní zprávy všem
    players = models.get_all_players()
    for player in players:
        email_sender.send_message(player['email'], config.MESSAGES['game_start'])

    models.add_event(1, config.PHASE_INIT, "game_started", "Hra zahájena")
    console.print("[green]✅ Hra úspěšně zahájena![/green]")
    console.print("[yellow]💡 Použijte 'python main.py next' pro postup do další fáze[/yellow]")

    return True


def next_phase():
    """Postup do další fáze hry"""
    state = models.get_game_state()

    if not state or not state['started']:
        console.print("[red]❌ Hra ještě nezačala! Použijte 'start'[/red]")
        return

    if state['finished']:
        console.print("[red]❌ Hra již skončila![/red]")
        return

    current_phase = state['phase']
    round_num = state['round_number']

    console.print(f"[cyan]📍 Aktuální fáze: {current_phase}, Kolo: {round_num}[/cyan]")

    # Rozhodování o další fázi
    if current_phase == config.PHASE_INIT:
        _start_night_traitor_chat(round_num)

    elif current_phase == config.PHASE_NIGHT_TRAITOR_CHAT:
        _start_night_vote(round_num)

    elif current_phase == config.PHASE_NIGHT_VOTE:
        _process_night_result(round_num)

    elif current_phase == config.PHASE_NIGHT_REVOTE:
        _process_night_revote_result(round_num)

    elif current_phase == config.PHASE_MORNING_RESULT:
        _start_day_discussion(round_num)

    elif current_phase == config.PHASE_DAY_DISCUSSION:
        _start_day_vote(round_num)

    elif current_phase == config.PHASE_DAY_VOTE:
        _process_day_result(round_num)

    elif current_phase == config.PHASE_DAY_REVOTE:
        _process_day_revote_result(round_num)

    elif current_phase == config.PHASE_DAY_RESULT:
        # Kontrola vítězství
        if check_win_condition():
            return
        # Nové kolo
        models.increment_round()
        _start_night_traitor_chat(round_num + 1)


def _start_night_traitor_chat(round_num: int):
    """Zahájení noční diskuze zrádců"""
    console.print(f"[magenta]🌙 KOLO {round_num} - Noční diskuze zrádců[/magenta]")

    traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)

    for traitor in traitors:
        email_sender.send_message(traitor['email'], config.MESSAGES['night_begins'])

    models.update_game_phase(config.PHASE_NIGHT_TRAITOR_CHAT)
    models.add_event(round_num, config.PHASE_NIGHT_TRAITOR_CHAT, "night_chat", "Noční diskuze zahájena")

    console.print("[yellow]💡 Zrádci se radí... Použijte 'next' pro přechod k hlasování[/yellow]")


def _start_night_vote(round_num: int):
    """Zahájení nočního hlasování zrádců"""
    console.print(f"[magenta]⚔️ KOLO {round_num} - Noční volba oběti[/magenta]")

    traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)
    alive_players = models.get_alive_players()

    # Seznam hráčů k eliminaci (kromě zrádců)
    targets = [p for p in alive_players if p['role'] != config.ROLE_TRAITOR]

    if not targets:
        console.print("[yellow]⚠️  Žádní věrní hráči k eliminaci![/yellow]")
        models.update_game_phase(config.PHASE_NIGHT_VOTE)
        return

    # Vytvoření seznamu pro volbu
    player_list = "\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(targets)])
    message = config.MESSAGES['night_vote_prompt'].format(players=player_list)

    for traitor in traitors:
        email_sender.send_message(traitor['email'], message)

    models.update_game_phase(config.PHASE_NIGHT_VOTE)
    models.add_event(round_num, config.PHASE_NIGHT_VOTE, "night_vote", "Noční hlasování zahájeno")

    console.print(f"[yellow]🗳️  Čekám na hlasy {len(traitors)} zrádců...[/yellow]")
    console.print("[yellow]💡 Použijte 'vote' pro zadání hlasů nebo 'next' pro vyhodnocení[/yellow]")


def _process_night_result(round_num: int):
    """Vyhodnocení nočního hlasování"""
    console.print(f"[magenta]☀️ KOLO {round_num} - Výsledek noci[/magenta]")

    votes = models.count_votes(round_num, config.PHASE_NIGHT_VOTE)

    if not votes:
        console.print("[yellow]⚠️  Žádné hlasy! Noc proběhla klidně.[/yellow]")
        message = config.MESSAGES['morning_result_none']

        # Oznámení všem
        all_players = models.get_all_players()
        for player in all_players:
            email_sender.send_message(player['email'], message)

        models.update_game_phase(config.PHASE_MORNING_RESULT)
        console.print("[yellow]💡 Použijte 'next' pro zahájení denní diskuze[/yellow]")
    else:
        # Kontrola remízy - zrádci se musí shodnout
        max_votes = votes[0][1]
        tied_candidates = [(player_id, count) for player_id, count in votes if count == max_votes]

        if len(tied_candidates) > 1:
            # REMÍZA - zrádci se neshodli, opakované hlasování
            console.print(f"[yellow]⚖️  Zrádci se neshodli! Remíza mezi {len(tied_candidates)} kandidáty.[/yellow]")

            tied_ids = [player_id for player_id, _ in tied_candidates]
            tied_names = []
            for player_id in tied_ids:
                player = models.get_player(player_id)
                tied_names.append(player['name'])
                console.print(f"   - {player['name']} ({max_votes} hlasů)")

            # Zahájit opakované noční hlasování
            _start_night_revote(round_num, tied_ids, tied_names)
        else:
            # Shoda - eliminovat oběť
            victim_id, vote_count = votes[0]
            victim = models.get_player(victim_id)

            console.print(f"[red]💀 Eliminován: {victim['name']} ({vote_count} hlasů)[/red]")

            models.eliminate_player(victim_id, round_num)
            message = config.MESSAGES['morning_result'].format(player=victim['name'])
            models.add_event(round_num, config.PHASE_MORNING_RESULT, "night_elimination", f"{victim['name']} eliminován")

            # Oznámení všem
            all_players = models.get_all_players()
            for player in all_players:
                email_sender.send_message(player['email'], message)

            models.update_game_phase(config.PHASE_MORNING_RESULT)

            console.print("[yellow]💡 Použijte 'next' pro zahájení denní diskuze[/yellow]")


def _start_night_revote(round_num: int, tied_candidate_ids: List[int], tied_names: List[str]):
    """Zahájení opakovaného nočního hlasování při remíze"""
    console.print(f"[magenta]🔄 KOLO {round_num} - Opakované noční hlasování[/magenta]")

    traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)

    if not traitors:
        console.print("[yellow]⚠️  Žádní živí zrádci![/yellow]")
        models.update_game_phase(config.PHASE_MORNING_RESULT)
        return

    tied_players_names = ", ".join(tied_names)
    console.print(f"[yellow]📋 Kandidáti: {tied_players_names}[/yellow]")
    console.print(f"[yellow]⚔️  Zrádci musí hlasovat znovu: {len(traitors)} zrádců[/yellow]")

    # Seznam kandidátů pro hlasování
    candidates_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(tied_names)])

    # Zpráva zrádcům
    vote_message = config.MESSAGES['night_revote_prompt'].format(players=candidates_list)

    for traitor in traitors:
        email_sender.send_message(traitor['email'], vote_message)
        console.print(f"   ⚔️  {traitor['name']} musí hlasovat znovu")

    models.update_game_phase(config.PHASE_NIGHT_REVOTE)
    models.add_event(round_num, config.PHASE_NIGHT_REVOTE, "night_revote", f"Opakované noční hlasování: {tied_players_names}")

    console.print(f"[yellow]🗳️  Čekám na hlasy {len(traitors)} zrádců...[/yellow]")
    console.print("[yellow]💡 Použijte 'vote' pro zadání hlasů nebo 'next' pro vyhodnocení[/yellow]")


def _process_night_revote_result(round_num: int):
    """Vyhodnocení opakovaného nočního hlasování"""
    console.print(f"[magenta]☀️ KOLO {round_num} - Výsledek opakovaného hlasování[/magenta]")

    votes = models.count_votes(round_num, config.PHASE_NIGHT_REVOTE)

    if not votes:
        # Žádné hlasy - noc proběhla klidně
        console.print("[yellow]⚠️  Žádné hlasy v opakovaném hlasování! Noc proběhla klidně.[/yellow]")
        message = config.MESSAGES['morning_result_none']
    else:
        # I v opakovaném hlasování může být remíza
        max_votes = votes[0][1]
        tied_count = sum(1 for _, count in votes if count == max_votes)

        if tied_count > 1:
            # Stále remíza - nikdo není eliminován
            console.print("[yellow]⚖️  Zrádci se stále neshodli! Nikdo není eliminován.[/yellow]")
            message = config.MESSAGES['morning_result_none']
        else:
            # Shoda dosažena - eliminovat oběť
            victim_id, vote_count = votes[0]
            victim = models.get_player(victim_id)

            console.print(f"[red]💀 Eliminován: {victim['name']} ({vote_count} hlasů)[/red]")

            models.eliminate_player(victim_id, round_num)
            message = config.MESSAGES['morning_result'].format(player=victim['name'])
            models.add_event(round_num, config.PHASE_MORNING_RESULT, "night_elimination", f"{victim['name']} eliminován (opakované hlasování)")

    # Oznámení všem
    all_players = models.get_all_players()
    for player in all_players:
        email_sender.send_message(player['email'], message)

    models.update_game_phase(config.PHASE_MORNING_RESULT)

    console.print("[yellow]💡 Použijte 'next' pro zahájení denní diskuze[/yellow]")


def _start_day_discussion(round_num: int):
    """Zahájení denní diskuze"""
    console.print(f"[cyan]💬 KOLO {round_num} - Denní diskuze[/cyan]")

    alive_players = models.get_alive_players()

    for player in alive_players:
        email_sender.send_message(player['email'], config.MESSAGES['day_discussion'])

    models.update_game_phase(config.PHASE_DAY_DISCUSSION)
    models.add_event(round_num, config.PHASE_DAY_DISCUSSION, "day_discussion", "Denní diskuze zahájena")

    console.print("[yellow]💡 Hráči diskutují... Použijte 'next' pro zahájení hlasování[/yellow]")


def _start_day_vote(round_num: int):
    """Zahájení denního hlasování"""
    console.print(f"[cyan]🗳️ KOLO {round_num} - Denní hlasování[/cyan]")

    alive_players = models.get_alive_players()

    # Seznam všech živých hráčů
    player_list = "\n".join([f"{i+1}. {p['name']}" for i, p in enumerate(alive_players)])
    message = config.MESSAGES['day_vote_prompt'].format(players=player_list)

    for player in alive_players:
        email_sender.send_message(player['email'], message)

    models.update_game_phase(config.PHASE_DAY_VOTE)
    models.add_event(round_num, config.PHASE_DAY_VOTE, "day_vote", "Denní hlasování zahájeno")

    console.print(f"[yellow]🗳️  Čekám na hlasy {len(alive_players)} hráčů...[/yellow]")
    console.print("[yellow]💡 Použijte 'vote' pro zadání hlasů nebo 'next' pro vyhodnocení[/yellow]")


def _process_day_result(round_num: int):
    """Vyhodnocení denního hlasování"""
    console.print(f"[cyan]📊 KOLO {round_num} - Výsledek hlasování[/cyan]")

    votes = models.count_votes(round_num, config.PHASE_DAY_VOTE)

    if not votes:
        console.print("[yellow]⚠️  Žádné hlasy! Nikdo není vyloučen.[/yellow]")
        message = config.MESSAGES['day_result_tie']

        # Oznámení všem
        all_players = models.get_all_players()
        for player in all_players:
            email_sender.send_message(player['email'], message)

        models.update_game_phase(config.PHASE_DAY_RESULT)
        console.print("[yellow]💡 Použijte 'next' pro kontrolu vítězství a pokračování[/yellow]")
    else:
        # Kontrola remízy - najdi všechny hráče s nejvyšším počtem hlasů
        max_votes = votes[0][1]
        tied_players = [(player_id, count) for player_id, count in votes if count == max_votes]

        if len(tied_players) > 1:
            # REMÍZA - zahájit opakované hlasování
            console.print(f"[yellow]⚖️  Remíza mezi {len(tied_players)} hráči![/yellow]")

            # Seznam hráčů v remíze
            tied_ids = [player_id for player_id, _ in tied_players]
            tied_names = []
            for player_id in tied_ids:
                player = models.get_player(player_id)
                tied_names.append(player['name'])
                console.print(f"   - {player['name']} ({max_votes} hlasů)")

            # Zahájit opakované hlasování
            _start_day_revote(round_num, tied_ids, tied_names)
        else:
            # Jasný vítěz - vyloučit hráče
            eliminated_id, vote_count = votes[0]
            eliminated = models.get_player(eliminated_id)

            console.print(f"[red]🚫 Vyloučen: {eliminated['name']} - {eliminated['role']} ({vote_count} hlasů)[/red]")

            models.eliminate_player(eliminated_id, round_num)
            message = config.MESSAGES['day_result'].format(
                player=eliminated['name'],
                role="⚔️ ZRÁDCE" if eliminated['role'] == config.ROLE_TRAITOR else "🛡️ VĚRNÝ"
            )
            models.add_event(round_num, config.PHASE_DAY_RESULT, "day_elimination", f"{eliminated['name']} vyloučen")

            # Oznámení všem
            all_players = models.get_all_players()
            for player in all_players:
                email_sender.send_message(player['email'], message)

            models.update_game_phase(config.PHASE_DAY_RESULT)

            console.print("[yellow]💡 Použijte 'next' pro kontrolu vítězství a pokračování[/yellow]")


def _start_day_revote(round_num: int, tied_player_ids: List[int], tied_names: List[str]):
    """Zahájení opakovaného hlasování při remíze"""
    console.print(f"[cyan]🔄 KOLO {round_num} - Opakované hlasování[/cyan]")

    alive_players = models.get_alive_players()

    # Volit mohou pouze ti, kteří NEJSOU v remíze
    eligible_voters = [p for p in alive_players if p['id'] not in tied_player_ids]

    # Hlasovat mohou POUZE pro hráče v remíze
    tied_players_names = ", ".join(tied_names)

    console.print(f"[yellow]📋 Kandidáti: {tied_players_names}[/yellow]")
    console.print(f"[yellow]🗳️  Oprávnění voliči: {len(eligible_voters)} hráčů[/yellow]")

    if not eligible_voters:
        # Pokud všichni živí hráči jsou v remíze, nikdo není vyloučen
        console.print("[yellow]⚠️  Všichni živí hráči jsou v remíze! Nikdo není vyloučen.[/yellow]")
        message = config.MESSAGES['day_result_tie']

        all_players = models.get_all_players()
        for player in all_players:
            email_sender.send_message(player['email'], message)

        models.update_game_phase(config.PHASE_DAY_RESULT)
        console.print("[yellow]💡 Použijte 'next' pro kontrolu vítězství a pokračování[/yellow]")
        return

    # Seznam kandidátů pro hlasování
    candidates_list = "\n".join([f"{i+1}. {name}" for i, name in enumerate(tied_names)])

    # Zpráva oprávněným voličům
    vote_message = config.MESSAGES['day_revote_prompt'].format(
        tied_players=tied_players_names,
        players=candidates_list
    )

    for voter in eligible_voters:
        email_sender.send_message(voter['email'], vote_message)
        console.print(f"   ✉️  {voter['name']} může hlasovat")

    # Zpráva hráčům v remíze (nemohou hlasovat)
    announcement = config.MESSAGES['day_revote_announcement'].format(tied_players=tied_players_names)
    for player_id in tied_player_ids:
        player = models.get_player(player_id)
        email_sender.send_message(player['email'], announcement)
        console.print(f"   🚫 {player['name']} nemůže hlasovat (je v remíze)")

    models.update_game_phase(config.PHASE_DAY_REVOTE)
    models.add_event(round_num, config.PHASE_DAY_REVOTE, "day_revote", f"Opakované hlasování: {tied_players_names}")

    console.print(f"[yellow]🗳️  Čekám na hlasy {len(eligible_voters)} oprávněných voličů...[/yellow]")
    console.print("[yellow]💡 Použijte 'vote' pro zadání hlasů nebo 'next' pro vyhodnocení[/yellow]")


def _process_day_revote_result(round_num: int):
    """Vyhodnocení opakovaného hlasování"""
    console.print(f"[cyan]📊 KOLO {round_num} - Výsledek opakovaného hlasování[/cyan]")

    votes = models.count_votes(round_num, config.PHASE_DAY_REVOTE)

    if not votes:
        console.print("[yellow]⚠️  Žádné hlasy v opakovaném hlasování! Nikdo není vyloučen.[/yellow]")
        message = config.MESSAGES['day_result_tie']
    else:
        # I v opakovaném hlasování může být remíza, ale už to neřešíme - nikdo není vyloučen
        max_votes = votes[0][1]
        tied_count = sum(1 for _, count in votes if count == max_votes)

        if tied_count > 1:
            console.print("[yellow]⚖️  Stále remíza! Nikdo není vyloučen.[/yellow]")
            message = config.MESSAGES['day_result_tie']
        else:
            # Vyloučení hráče
            eliminated_id, vote_count = votes[0]
            eliminated = models.get_player(eliminated_id)

            console.print(f"[red]🚫 Vyloučen: {eliminated['name']} - {eliminated['role']} ({vote_count} hlasů)[/red]")

            models.eliminate_player(eliminated_id, round_num)
            message = config.MESSAGES['day_result'].format(
                player=eliminated['name'],
                role="⚔️ ZRÁDCE" if eliminated['role'] == config.ROLE_TRAITOR else "🛡️ VĚRNÝ"
            )
            models.add_event(round_num, config.PHASE_DAY_RESULT, "day_elimination", f"{eliminated['name']} vyloučen (opakované hlasování)")

    # Oznámení všem
    all_players = models.get_all_players()
    for player in all_players:
        email_sender.send_message(player['email'], message)

    models.update_game_phase(config.PHASE_DAY_RESULT)

    console.print("[yellow]💡 Použijte 'next' pro kontrolu vítězství a pokračování[/yellow]")


def check_win_condition() -> bool:
    """Kontrola podmínek vítězství"""
    traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)
    faithful = models.get_players_by_role(config.ROLE_FAITHFUL, alive_only=True)

    winner = None
    message = None

    # Zrádci vyhráli
    if len(traitors) >= len(faithful):
        winner = "traitors"
        message = config.MESSAGES['traitors_win']
        console.print("[bold red]⚔️ ZRÁDCI VYHRÁLI![/bold red]")

    # Věrní vyhráli
    elif len(traitors) == 0:
        winner = "faithful"
        message = config.MESSAGES['faithful_win']
        console.print("[bold green]🛡️ VĚRNÍ VYHRÁLI![/bold green]")

    if winner and message:
        models.end_game(winner)

        # Oznámení výsledku
        all_players = models.get_all_players()
        for player in all_players:
            email_sender.send_message(player['email'], message)

        models.add_event(
            models.get_game_state()['round_number'],
            config.PHASE_GAME_OVER,
            "game_over",
            f"Výhra: {winner}"
        )

        # Zobrazení finálního stavu
        show_final_results()
        return True

    return False


def show_status():
    """Zobrazení aktuálního stavu hry"""
    state = models.get_game_state()

    if not state or not state['started']:
        console.print("[yellow]⚠️  Hra ještě nezačala[/yellow]")
        return

    alive_players = models.get_alive_players()
    traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)
    faithful = models.get_players_by_role(config.ROLE_FAITHFUL, alive_only=True)

    # Tabulka živých hráčů
    table = Table(title=f"🎮 Hra Zrádci - Kolo {state['round_number']} - Fáze: {state['phase']}")
    table.add_column("ID", style="cyan")
    table.add_column("Jméno", style="white")
    table.add_column("Role", style="yellow")
    table.add_column("Status", style="green")

    for player in models.get_all_players():
        status = "✅ Živý " if player['alive'] else f"💀 Eliminován (kolo {player['eliminated_round']})"
        role = "⚔️ Zrádce" if player['role'] == config.ROLE_TRAITOR else "🛡️ Věrný"
        table.add_row(
            str(player['id']),
            player['name'],
            role,
            status
        )

    console.print(table)

    # Statistiky
    console.print(f"\n[bold]📊 Statistiky:[/bold]")
    console.print(f"👥 Živí hráči: {len(alive_players)}")
    console.print(f"⚔️  Živí zrádci: {len(traitors)}")
    console.print(f"🛡️  Živí věrní: {len(faithful)}")


def show_final_results():
    """Zobrazení finálních výsledků"""
    state = models.get_game_state()

    console.print("\n[bold cyan]═══════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]     📊 FINÁLNÍ VÝSLEDKY HRY      [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════[/bold cyan]\n")

    # Tabulka všech hráčů
    table = Table(title="🎮 Všichni hráči")
    table.add_column("Jméno", style="white")
    table.add_column("Role", style="yellow")
    table.add_column("Osud", style="cyan")

    for player in models.get_all_players():
        role = "⚔️ Zrádce" if player['role'] == config.ROLE_TRAITOR else "🛡️ Věrný"
        fate = "✅ Přežil" if player['alive'] else f"💀 Eliminován v kole {player['eliminated_round']}"
        table.add_row(player['name'], role, fate)

    console.print(table)

    console.print(f"\n[bold]🏆 Vítěz: {state['winner'].upper()}[/bold]")
    console.print(f"[bold]🔄 Celkem kol: {state['round_number']}[/bold]\n")

