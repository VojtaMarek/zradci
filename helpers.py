import models


def add_players_from_list(player_list: list[tuple[str, str]]):

    for name, email in player_list:
        try:
            player_id = models.add_player(name, email)
            print(f"  [green]✅ Přidán (ID: {player_id})[/green]\n")

        except Exception as e:
            print(f"  [red]❌ Chyba: {e}[/red]\n")



if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    print("[bold blue]🎮 Přidání hráčů do databáze Zrádců[/bold blue]\n")

    sample_players = [
        ("Vojta", "vojtama@gmail.com"),
        ("Lucka", "lucieHrubka@gmail.com"),
        ("Kuba", "@gmail.com"),
        ("Barča", "@gmail.com_"),
        ("Eli", "@gmail.com__"),
        ("Michal", "@gmail.com___"),
    ]
    add_players_from_list(sample_players)