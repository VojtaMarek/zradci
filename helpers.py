import models


def add_players_from_list(player_list: list[tuple[str, str]]):

    for name, email in player_list:
        try:
            player_id = models.add_player(name, email)
            print(f"  [green]✅ Přidán (ID: {player_id})[/green]\n")

        except Exception as e:
            print(f"  [red]❌ Chyba: {e}[/red]\n")
