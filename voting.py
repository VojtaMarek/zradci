import models
import config


def vote(voter_id: int, target_id: int):
    """🗳️  Zadání hlasu"""
    state = models.get_game_state()

    if not state or not state['started']:
        print("[red]❌ Hra ještě nezačala![/red]")
        return

    if state['finished']:
        print("[red]❌ Hra již skončila![/red]")
        return

    # Ověření hráčů
    voter = models.get_player(voter_id)
    target = models.get_player(target_id)

    if not voter or not target:
        print("[red]❌ Neplatné ID hráče![/red]")
        return

    if not voter['alive']:
        print(f"[red]❌ {voter['name']} je eliminován a nemůže hlasovat![/red]")
        return

    if not target['alive']:
        print(f"[red]❌ {target['name']} je eliminován a nelze na něj hlasovat![/red]")
        return

    # Kontrola typu hlasování podle fáze
    phase = state['phase']
    round_num = state['round_number']

    if phase == config.PHASE_NIGHT_VOTE:
        # Pouze zrádci mohou hlasovat v noci
        if voter['role'] != config.ROLE_TRAITOR:
            print(f"[red]❌ {voter['name']} není zrádce a nemůže hlasovat v noci![/red]")
            return
        # Nemohou hlasovat pro jiného zrádce
        if target['role'] == config.ROLE_TRAITOR:
            print(f"[red]❌ Nelze hlasovat pro spoluzrádce![/red]")
            return

    elif phase == config.PHASE_NIGHT_REVOTE:
        # V opakovaném nočním hlasování mohou hlasovat pouze zrádci
        if voter['role'] != config.ROLE_TRAITOR:
            print(f"[red]❌ {voter['name']} není zrádce a nemůže hlasovat v noci![/red]")
            return

        # Musí hlasovat pouze pro kandidáty z remíze
        previous_votes = models.count_votes(round_num, config.PHASE_NIGHT_VOTE)
        if previous_votes:
            max_votes = previous_votes[0][1]
            tied_candidate_ids = [player_id for player_id, count in previous_votes if count == max_votes]

            # Target musí být v remíze
            if target_id not in tied_candidate_ids:
                tied_names = [models.get_player(pid)['name'] for pid in tied_candidate_ids]
                print(f"[red]❌ Můžete hlasovat pouze pro kandidáty z remíze: {', '.join(tied_names)}[/red]")
                return

        # Stále nemohou hlasovat pro jiného zrádce
        if target['role'] == config.ROLE_TRAITOR:
            print(f"[red]❌ Nelze hlasovat pro spoluzrádce![/red]")
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
                print(f"[red]❌ {voter['name']} je v remíze a nemůže hlasovat![/red]")
                return

            # Target musí být v remíze
            if target_id not in tied_player_ids:
                tied_names = [models.get_player(pid)['name'] for pid in tied_player_ids]
                print(f"[red]❌ Můžete hlasovat pouze pro hráče v remíze: {', '.join(tied_names)}[/red]")
                return

    else:
        print(f"[red]❌ Nyní není fáze hlasování! Aktuální fáze: {phase}[/red]")
        return

    # Zaznamenání hlasu
    models.add_vote(voter_id, target_id, round_num, phase)
    print(f"[green]✅ Hlas zaznamenán: {voter['name']} → {target['name']}[/green]")
