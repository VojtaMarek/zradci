"""
Zrádci - CLI aplikace pro moderování hry
Inspirováno televizní show "The Traitors"
"""
import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from typing import Optional
import random

import models
import game_engine
import config
import narrator
import voting

app = typer.Typer(help="🎮 Aplikace pro moderování hry Zrádci")
console = Console()


@app.command()
def setup():
    """🔧 Inicializace databáze"""
    console.print("[cyan]🔧 Inicializuji databázi...[/cyan]")
    models.init_db()
    console.print("[green]✅ Databáze úspěšně inicializována![/green]")
    console.print("[yellow]💡 Použijte 'add-players' pro přidání hráčů[/yellow]")


@app.command()
def reset():
    """🔄 Reset hry - smazání všech dat"""
    if Confirm.ask("⚠️  Opravdu chcete resetovat celou hru a smazat všechna data?"):
        models.reset_game()
        console.print("[green]✅ Hra byla resetována[/green]")
        console.print("[yellow]💡 Použijte 'setup' pro novou inicializaci[/yellow]")
    else:
        console.print("[yellow]❌ Reset zrušen[/yellow]")


@app.command()
def add_player(name: str, email: str):
    """➕ Přidání jednoho hráče"""
    try:
        player_id = models.add_player(name, email)
        console.print(f"[green]✅ Hráč přidán: {name} (ID: {player_id})[/green]")
    except Exception as e:
        console.print(f"[red]❌ Chyba při přidávání hráče: {e}[/red]")


@app.command()
def add_players():
    """➕ Interaktivní přidání více hráčů"""
    console.print("[cyan]➕ Přidávání hráčů[/cyan]")
    console.print(f"[yellow]Minimum: {config.MIN_PLAYERS}, Maximum: {config.MAX_PLAYERS}[/yellow]\n")

    count = 0
    while True:
        console.print(f"[bold]Hráč #{count + 1}[/bold]")

        name = Prompt.ask("  Jméno (nebo 'q' pro konec)")
        if name.lower() == 'q':
            break

        email = Prompt.ask("  Email")

        try:
            player_id = models.add_player(name, email)
            console.print(f"  [green]✅ Přidán (ID: {player_id})[/green]\n")
            count += 1
        except Exception as e:
            console.print(f"  [red]❌ Chyba: {e}[/red]\n")

    console.print(f"[green]✅ Celkem přidáno hráčů: {count}[/green]")

    if count >= config.MIN_PLAYERS:
        console.print("[yellow]💡 Máte dostatek hráčů! Použijte 'start' pro zahájení hry[/yellow]")
    else:
        console.print(f"[yellow]⚠️  Potřebujete ještě {config.MIN_PLAYERS - count} hráčů[/yellow]")


@app.command()
def list_players():
    """👥 Zobrazení seznamu hráčů"""
    players = models.get_all_players()

    if not players:
        console.print("[yellow]⚠️  Žádní hráči[/yellow]")
        return

    table = Table(title="👥 Seznam hráčů")
    table.add_column("ID", style="cyan")
    table.add_column("Jméno", style="white")
    table.add_column("Email", style="yellow")
    table.add_column("Role", style="magenta")
    table.add_column("Status", style="green")

    for player in players:
        role = player['role'] or "-"
        status = "✅ Živý" if player['alive'] else f"💀 Eliminován"
        table.add_row(
            str(player['id']),
            player['name'],
            player['email'],
            role,
            status
        )

    console.print(table)
    console.print(f"\n[bold]Celkem: {len(players)} hráčů[/bold]")


@app.command()
def start():
    """🎮 Zahájení hry - přiřazení rolí"""
    players = models.get_all_players()

    if len(players) < config.MIN_PLAYERS:
        console.print(f"[red]❌ Nedostatek hráčů! Minimum: {config.MIN_PLAYERS}[/red]")
        return

    if len(players) > config.MAX_PLAYERS:
        console.print(f"[red]❌ Příliš mnoho hráčů! Maximum: {config.MAX_PLAYERS}[/red]")
        return

    state = models.get_game_state()
    if state and state['started']:
        console.print("[yellow]⚠️  Hra již běží! Použijte 'reset' pro restart[/yellow]")
        return

    game_engine.start_game()


@app.command()
def next():
    """⏭️  Postup do další fáze hry"""
    game_engine.next_phase()


@app.command()
def status():
    """📊 Zobrazení aktuálního stavu hry"""
    game_engine.show_status()


@app.command()
def vote(voter_id: int, target_id: int):
    """🗳️  Manuální zadání hlasu"""
    state = models.get_game_state()

    if not state or not state['started']:
        console.print("[red]❌ Hra ještě nezačala![/red]")
        return

    if state['finished']:
        console.print("[red]❌ Hra již skončila![/red]")
        return

    # Ověření hráčů
    voter = models.get_player(voter_id)
    target = models.get_player(target_id)

    if not voter or not target:
        console.print("[red]❌ Neplatné ID hráče![/red]")
        return

    if not voter['alive']:
        console.print(f"[red]❌ {voter['name']} je eliminován a nemůže hlasovat![/red]")
        return

    if not target['alive']:
        console.print(f"[red]❌ {target['name']} je eliminován a nelze na něj hlasovat![/red]")
        return

    # Kontrola typu hlasování podle fáze
    phase = state['phase']
    round_num = state['round_number']

    if phase == config.PHASE_NIGHT_VOTE:
        # Pouze zrádci mohou hlasovat v noci
        if voter['role'] != config.ROLE_TRAITOR:
            console.print(f"[red]❌ {voter['name']} není zrádce a nemůže hlasovat v noci![/red]")
            return
        # Nemohou hlasovat pro jiného zrádce
        if target['role'] == config.ROLE_TRAITOR:
            console.print(f"[red]❌ Nelze hlasovat pro spoluzrádce![/red]")
            return

    elif phase == config.PHASE_NIGHT_REVOTE:
        # V opakovaném nočním hlasování mohou hlasovat pouze zrádci
        if voter['role'] != config.ROLE_TRAITOR:
            console.print(f"[red]❌ {voter['name']} není zrádce a nemůže hlasovat v noci![/red]")
            return

        # Musí hlasovat pouze pro kandidáty z remíze
        previous_votes = models.count_votes(round_num, config.PHASE_NIGHT_VOTE)
        if previous_votes:
            max_votes = previous_votes[0][1]
            tied_candidate_ids = [player_id for player_id, count in previous_votes if count == max_votes]

            # Target musí být v remíze
            if target_id not in tied_candidate_ids:
                tied_names = [models.get_player(pid)['name'] for pid in tied_candidate_ids]
                console.print(f"[red]❌ Můžete hlasovat pouze pro kandidáty z remíze: {', '.join(tied_names)}[/red]")
                return

        # Stále nemohou hlasovat pro jiného zrádce
        if target['role'] == config.ROLE_TRAITOR:
            console.print(f"[red]❌ Nelze hlasovat pro spoluzrádce![/red]")
            return

    elif phase == config.PHASE_DAY_VOTE:
        # Všichni živí mohou hlasovat
        pass

    elif phase == config.PHASE_DAY_REVOTE:
        # V opakovaném hlasování mohou hlasovat pouze ti, kteří NEJSOU v remíze
        # Zjistíme, kdo je v remíze z předchozího hlasování
        previous_votes = models.count_votes(round_num, config.PHASE_DAY_VOTE)
        if previous_votes:
            max_votes = previous_votes[0][1]
            tied_player_ids = [player_id for player_id, count in previous_votes if count == max_votes]

            # Voter nesmí být v remíze
            if voter_id in tied_player_ids:
                console.print(f"[red]❌ {voter['name']} je v remíze a nemůže hlasovat![/red]")
                return

            # Target musí být v remíze
            if target_id not in tied_player_ids:
                tied_names = [models.get_player(pid)['name'] for pid in tied_player_ids]
                console.print(f"[red]❌ Můžete hlasovat pouze pro hráče v remíze: {', '.join(tied_names)}[/red]")
                return

    else:
        console.print(f"[red]❌ Nyní není fáze hlasování! Aktuální fáze: {phase}[/red]")
        return

    # Zaznamenání hlasu
    models.add_vote(voter_id, target_id, round_num, phase)
    console.print(f"[green]✅ Hlas zaznamenán: {voter['name']} → {target['name']}[/green]")


@app.command()
def simulate_vote():
    """🎲 Simulace hlasování (pro testování)"""
    state = models.get_game_state()

    if not state or not state['started']:
        console.print("[red]❌ Hra ještě nezačala![/red]")
        return

    phase = state['phase']
    round_num = state['round_number']

    if phase == config.PHASE_NIGHT_VOTE:
        # Simulace nočního hlasování zrádců
        traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)
        targets = [p for p in models.get_alive_players() if p['role'] != config.ROLE_TRAITOR]

        if not targets:
            console.print("[yellow]⚠️  Žádní cíle k eliminaci![/yellow]")
            return

        console.print(f"[yellow]🎲 Simuluji hlasy {len(traitors)} zrádců...[/yellow]")

        for traitor in traitors:
            target = random.choice(targets)
            models.add_vote(traitor['id'], target['id'], round_num, phase)
            console.print(f"  {traitor['name']} → {target['name']}")

        console.print("[green]✅ Noční hlasování nasimulováno[/green]")

    elif phase == config.PHASE_NIGHT_REVOTE:
        # Simulace opakovaného nočního hlasování
        traitors = models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True)

        # Zjistíme kandidáty z remíze
        previous_votes = models.count_votes(round_num, config.PHASE_NIGHT_VOTE)
        if not previous_votes:
            console.print("[red]❌ Žádné předchozí hlasy nenalezeny![/red]")
            return

        max_votes = previous_votes[0][1]
        tied_candidate_ids = [player_id for player_id, count in previous_votes if count == max_votes]

        # Pouze kandidáti, kteří nejsou zrádci
        all_alive = models.get_alive_players()
        tied_candidates = [p for p in all_alive if p['id'] in tied_candidate_ids and p['role'] != config.ROLE_TRAITOR]

        if not tied_candidates:
            console.print("[yellow]⚠️  Žádní kandidáti pro opakované hlasování![/yellow]")
            return

        console.print(f"[yellow]🎲 Simuluji opakované noční hlasování - {len(traitors)} zrádců...[/yellow]")
        console.print(f"[yellow]   Kandidáti: {', '.join([p['name'] for p in tied_candidates])}[/yellow]")

        for traitor in traitors:
            target = random.choice(tied_candidates)
            models.add_vote(traitor['id'], target['id'], round_num, phase)
            console.print(f"  {traitor['name']} → {target['name']}")

        console.print("[green]✅ Opakované noční hlasování nasimulováno[/green]")

    elif phase == config.PHASE_DAY_VOTE:
        # Simulace denního hlasování
        voters = models.get_alive_players()

        console.print(f"[yellow]🎲 Simuluji hlasy {len(voters)} hráčů...[/yellow]")

        for voter in voters:
            # Každý hráč hlasuje pro někoho jiného
            possible_targets = [p for p in voters if p['id'] != voter['id']]
            if possible_targets:
                target = random.choice(possible_targets)
                models.add_vote(voter['id'], target['id'], round_num, phase)
                console.print(f"  {voter['name']} → {target['name']}")

        console.print("[green]✅ Denní hlasování nasimulováno[/green]")

    elif phase == config.PHASE_DAY_REVOTE:
        # Simulace opakovaného hlasování
        # Zjistíme, kdo je v remíze
        previous_votes = models.count_votes(round_num, config.PHASE_DAY_VOTE)
        if not previous_votes:
            console.print("[red]❌ Žádné předchozí hlasy nenalezeny![/red]")
            return

        max_votes = previous_votes[0][1]
        tied_player_ids = [player_id for player_id, count in previous_votes if count == max_votes]

        # Volit mohou pouze ti, kteří nejsou v remíze
        all_alive = models.get_alive_players()
        eligible_voters = [p for p in all_alive if p['id'] not in tied_player_ids]

        # Hlasovat mohou pouze pro hráče v remíze
        tied_players = [p for p in all_alive if p['id'] in tied_player_ids]

        if not eligible_voters:
            console.print("[yellow]⚠️  Žádní oprávnění voliči![/yellow]")
            return

        console.print(f"[yellow]🎲 Simuluji opakované hlasování - {len(eligible_voters)} oprávněných voličů...[/yellow]")
        console.print(f"[yellow]   Kandidáti: {', '.join([p['name'] for p in tied_players])}[/yellow]")

        for voter in eligible_voters:
            target = random.choice(tied_players)
            models.add_vote(voter['id'], target['id'], round_num, phase)
            console.print(f"  {voter['name']} → {target['name']}")

        console.print("[green]✅ Opakované hlasování nasimulováno[/green]")

    else:
        console.print(f"[red]❌ Nyní není fáze hlasování! Aktuální fáze: {phase}[/red]")


@app.command()
def votes(round_num: Optional[int] = None):
    """📋 Zobrazení hlasů"""
    state = models.get_game_state()

    if not state or not state['started']:
        console.print("[red]❌ Hra ještě nezačala![/red]")
        return

    if round_num is None:
        round_num = state['round_number']

    # Zkusit všechny fáze hlasování
    for phase in [config.PHASE_NIGHT_VOTE, config.PHASE_NIGHT_REVOTE, config.PHASE_DAY_VOTE, config.PHASE_DAY_REVOTE]:
        vote_list = models.get_votes(round_num, phase)

        if vote_list:
            if phase == config.PHASE_NIGHT_VOTE:
                phase_name = "Noční hlasování"
            elif phase == config.PHASE_NIGHT_REVOTE:
                phase_name = "Opakované noční hlasování"
            elif phase == config.PHASE_DAY_VOTE:
                phase_name = "Denní hlasování"
            else:  # PHASE_DAY_REVOTE
                phase_name = "Opakované denní hlasování"

            console.print(f"\n[bold cyan]{phase_name} - Kolo {round_num}[/bold cyan]")

            table = Table()
            table.add_column("Hlasující", style="cyan")
            table.add_column("→", style="white")
            table.add_column("Cíl", style="yellow")
            table.add_column("Čas", style="dim")

            for vote in vote_list:
                voter = models.get_player(vote['voter_id'])
                target = models.get_player(vote['target_id'])
                table.add_row(
                    voter['name'],
                    "→",
                    target['name'],
                    vote['timestamp']
                )

            console.print(table)

            # Souhrn hlasů
            counts = models.count_votes(round_num, phase)
            if counts:
                console.print("\n[bold]📊 Souhrn:[/bold]")
                for target_id, count in counts:
                    target = models.get_player(target_id)
                    console.print(f"  {target['name']}: {count} hlasů")


@app.command()
def events(round_num: Optional[int] = None):
    """📜 Historie událostí"""
    event_list = models.get_events(round_num)

    if not event_list:
        console.print("[yellow]⚠️  Žádné události[/yellow]")
        return

    title = f"📜 Události - Kolo {round_num}" if round_num else "📜 Všechny události"
    table = Table(title=title)
    table.add_column("Kolo", style="cyan")
    table.add_column("Fáze", style="magenta")
    table.add_column("Typ", style="yellow")
    table.add_column("Popis", style="white")
    table.add_column("Čas", style="dim")

    for event in event_list:
        table.add_row(
            str(event['round_number']),
            event['phase'],
            event['event_type'],
            event['description'],
            event['timestamp']
        )

    console.print(table)


@app.command()
def watch(
    interval: float = typer.Option(2.0, "--interval", "-i", help="Interval aktualizace v sekundách"),
):
    """👀 Sledovat stav hry v reálném čase (live dashboard)"""
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    import time
    from datetime import datetime

    # Cachování komentáře mezi refresh cykly
    narrator_commentary = None
    last_generated_state = None

    def generate_dashboard() -> Layout:
        """Vygenerovat aktuální dashboard"""
        nonlocal narrator_commentary, last_generated_state  # Přístup k vnějším proměnným

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        # Header
        state = models.get_game_state()
        if not state or not state['started']:
            layout["header"].update(Panel("❌ Hra nezahájena", style="red bold"))
            layout["main"].update(Panel(
                "[yellow]Použijte 'zradci start' pro zahájení hry[/yellow]",
                title="💡 Nápověda"
            ))
            layout["footer"].update(Panel(
                f"🔄 Aktualizace každých {interval}s | Stiskněte Ctrl+C pro ukončení",
                style="dim"
            ))
            return layout

        # Header s aktuálním stavem
        phase_emoji = {
            config.PHASE_INIT: "🎬",
            config.PHASE_NIGHT_TRAITOR_CHAT: "💬",
            config.PHASE_NIGHT_VOTE: "🗳️",
            config.PHASE_NIGHT_REVOTE: "🔄",
            config.PHASE_MORNING_RESULT: "☀️",
            config.PHASE_DAY_DISCUSSION: "💭",
            config.PHASE_DAY_VOTE: "🗳️",
            config.PHASE_DAY_REVOTE: "🔄",
            config.PHASE_DAY_RESULT: "📊",
            config.PHASE_GAME_OVER: "🏁"
        }

        phase_names = {
            config.PHASE_INIT: "INICIALIZACE",
            config.PHASE_NIGHT_TRAITOR_CHAT: "NOČNÍ DISKUZE ZRÁDCŮ",
            config.PHASE_NIGHT_VOTE: "NOČNÍ HLASOVÁNÍ",
            config.PHASE_NIGHT_REVOTE: "OPAKOVANÉ NOČNÍ HLASOVÁNÍ",
            config.PHASE_MORNING_RESULT: "RANNÍ VÝSLEDEK",
            config.PHASE_DAY_DISCUSSION: "DENNÍ DISKUZE",
            config.PHASE_DAY_VOTE: "DENNÍ HLASOVÁNÍ",
            config.PHASE_DAY_REVOTE: "OPAKOVANÉ DENNÍ HLASOVÁNÍ",
            config.PHASE_DAY_RESULT: "DENNÍ VÝSLEDEK",
            config.PHASE_GAME_OVER: "KONEC HRY"
        }

        emoji = phase_emoji.get(state['phase'], "🎮")
        phase_display = phase_names.get(state['phase'], state['phase'].upper())
        header_style = "red bold" if state['finished'] else "cyan bold"
        header_text = f"{emoji} KOLO {state['round_number']} | FÁZE: {phase_display}"
        if state['finished']:
            print(state['winner'])
            winner_emoji = "⚔️" if state['winner'] == "traitors" else "🛡️"
            header_text = f"🏁 HRA SKONČILA | VÍTĚZ: {winner_emoji} {state['winner'].upper()}"

        layout["header"].update(Panel(header_text, style=header_style))

        # Main content
        layout["main"].split_column(
            Layout(name="narrator", size=7),
            Layout(name="content")
        )

        # Sekce s LLM komentářem moderátora, generuje pouze při změně fáze
        narrator_commentary = models.get_latest_moderator_commentary()
        
        if narrator_commentary:
            narrator_panel = Panel(
                narrator_commentary,
                title="🎙️ Moderátor",
                border_style="yellow",
                style="italic"
            )
        else:
            narrator_panel = Panel(
                "[dim]Komentář moderátora není k dispozici[/dim]",
                title="🎙️ Moderátor",
                border_style="dim",
                style="dim"
            )
        layout["narrator"].update(narrator_panel)

        # Content area
        layout["content"].split_row(
            Layout(name="players", ratio=2),
            Layout(name="stats", ratio=1)
        )

        # Players table
        players_table = Table(
            title="👥 Hráči",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan"
        )
        players_table.add_column("ID", style="dim", width=4)
        players_table.add_column("Jméno", style="bold")
        players_table.add_column("Status", justify="center", width=8)
        players_table.add_column("Role", justify="center", width=8)

        players = models.get_all_players()
        alive_count = sum(1 for p in players if p['alive'])

        for p in players:
            status = "✅ Živý" if p['alive'] else "💀 Mrtvý"

            # Zobraz roli pouze pokud je hráč mrtvý nebo hra skončila
            if not p['alive'] or state['finished']:
                role = "⚔️ Zrádce" if p['role'] == config.ROLE_TRAITOR else "🛡️ Věrný"
            else:
                role = "❓"

            style = "" if p['alive'] else "dim"
            players_table.add_row(
                str(p['id']),
                p['name'],
                status,
                role,
                style=style
            )

        layout["players"].update(players_table)

        # Stats panel
        alive_traitors = len([p for p in players if p['alive'] and p['role'] == config.ROLE_TRAITOR])
        alive_faithful = len([p for p in players if p['alive'] and p['role'] == config.ROLE_FAITHFUL])
        dead_count = len([p for p in players if not p['alive']])

        stats_text = f"""[bold]📊 Statistiky[/bold]

🛡️  Věrných (živých): [green]{alive_faithful}[/green]
⚔️  Zrádců (živých): [red]{alive_traitors}[/red]
💀 Eliminováno: [yellow]{dead_count}[/yellow]
👥 Celkem: [cyan]{len(players)}[/cyan]

"""

        # Aktuální hlasy
        if state['phase'] in [config.PHASE_NIGHT_VOTE, config.PHASE_NIGHT_REVOTE]:
            total_voters = len(models.get_players_by_role(config.ROLE_TRAITOR, alive_only=True))
            voter_turnout = get_current_voter_turnout_count(state, total_voters)
            stats_text += f"🗳️  Odhlasováno tajně: [cyan]{voter_turnout}[/cyan]\n\n"

        if state['phase'] in [config.PHASE_DAY_VOTE, config.PHASE_DAY_REVOTE]:
            total_alive = len(models.get_alive_players())
            voter_turnout = get_current_voter_turnout_count(state, total_alive)
            votes_text = get_current_votes_text(state) 
            
            vote_title = "🗳️  Aktuální hlasy:"
            if state['phase'] == config.PHASE_DAY_REVOTE:
                vote_title = "🔄 Opakované denní hlasování:"
            vote_title += f" [cyan]{voter_turnout}[/cyan]" if voter_turnout != "0 (0%)" else ""
            stats_text += f"[bold]{vote_title}[/bold]\n{votes_text}\n"

            votes_list = models.get_votes(state['round_number'], state['phase'])
            stats_text += "\n"
            for v in votes_list:
                voter = models.get_player(v['voter_id'])
                target = models.get_player(v['target_id'])
                stats_text += f"  {voter['name']} → {target['name']}\n"


        else:
            # Poslední událost
            recent_events = models.get_events()
            if recent_events:
                last_events = recent_events[-10:]
                stats_text += f"\n[bold]📜 Poslední události[/bold]\n[dim]{"\n".join(e['description'] for e in last_events)}[/dim]"

        layout["stats"].update(Panel(stats_text, title="📊 Info", border_style="green"))

        # Footer
        current_time = datetime.now().strftime("%H:%M:%S")
        layout["footer"].update(Panel(
            f"🕐 {current_time} | 🔄 Aktualizace každých {interval}s | Stiskněte Ctrl+C pro ukončení",
            style="dim"
        ))

        return layout


    def get_current_voter_turnout_count(state, max_voters) -> str:
        """získej text s počtem hlasujících a procentem"""
        votes_list = models.get_votes(state['round_number'], state['phase'])
        
        if not votes_list:
            return "0 (0%)"
        
        vote_count = len(set(vote['voter_id'] for vote in votes_list))
        percentage = (vote_count / max_voters) * 100 if max_voters > 0 else 0
        return f"{vote_count} ({percentage:.1f}%)"


    def get_current_votes_text(state) -> str:
        """Získat text aktuálních hlasů"""
        votes_list = models.get_votes(state['round_number'], state['phase'])

        if not votes_list:
            return "[dim]Zatím žádné hlasy[/dim]"

        # Spočítej hlasy pro každého
        vote_counts = {}
        for vote in votes_list:
            target = models.get_player(vote['target_id'])
            target_name = target['name']
            vote_counts[target_name] = vote_counts.get(target_name, 0) + 1

        # Seřaď podle počtu hlasů
        sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)

        result = ""
        for name, count in sorted_votes:
            bars = "█" * count
            result += f"{name}: [yellow]{bars}[/yellow] {count}\n"

        return result.strip()

    console.print("[cyan]🔄 Spouštím live dashboard...[/cyan]\n")

    try:
        with Live(generate_dashboard(), refresh_per_second=1, console=console, screen=True) as live:
            while True:
                time.sleep(interval)
                live.update(generate_dashboard())
    except KeyboardInterrupt:
        console.print("\n[green]✅ Dashboard ukončen[/green]")


@app.command()
def info():
    """ℹ️  Informace o aplikaci"""
    console.print("\n[bold cyan]🎮 Zrádci - Aplikace pro moderování hry[/bold cyan]")
    console.print("Inspirováno televizní show 'The Traitors'\n")

    console.print("[bold]⚙️  Nastavení:[/bold]")
    console.print(f"  Minimální počet hráčů: {config.MIN_PLAYERS}")
    console.print(f"  Maximální počet hráčů: {config.MAX_PLAYERS}")
    console.print(f"  Poměr zrádců: {config.TRAITOR_RATIO * 100}%")
    console.print(f"  Databáze: {config.DATABASE_PATH}")

    console.print("\n[bold]📧 Email:[/bold]")
    if config.EMAIL_FROM and config.EMAIL_PASSWORD:
        console.print("  [green]✅ Nakonfigurováno[/green]")
    else:
        console.print("  [yellow]⚠️  Není nakonfigurováno (zprávy se vypisují do konzole)[/yellow]")

    console.print("\n[bold]📚 Příkazy:[/bold]")
    console.print("  setup          - Inicializace databáze")
    console.print("  add-players    - Interaktivní přidání hráčů")
    console.print("  list-players   - Seznam hráčů")
    console.print("  start          - Zahájení hry")
    console.print("  next           - Další fáze")
    console.print("  status         - Stav hry")
    console.print("  watch          - Live dashboard stavu hry")
    console.print("  vote           - Zaznamenání hlasu")
    console.print("  simulate-vote  - Simulace hlasování")
    console.print("  votes          - Zobrazení hlasů")
    console.print("  events         - Historie událostí")
    console.print("  reset          - Reset hry")
    console.print()


if __name__ == "__main__":
    app()
