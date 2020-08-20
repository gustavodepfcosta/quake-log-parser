
import re
import json


_world_id_ = '1022'


def split_logs_into_separated_games(filename):
    all_games = []

    try:
        with open(filename, "r") as f:
            single_game = []
            game_in_progress = False

            for line in f:
                # marcando o que deve ser particionado
                if "InitGame:" in line:
                    game_in_progress = True
                    single_game.append(line.strip())

                elif "ShutdownGame:" in line:
                    all_games.append(single_game)
                    single_game.append(line.strip())
                    single_game = []
                    game_in_progress = False

                # particionando o que foi marcado
                elif game_in_progress:
                    single_game.append(line.strip())

            if len(single_game) != 0:
                all_games.append(single_game)
                
    except FileNotFoundError:
        print(f'{filename} não foi encontrado. Tem certeza de que está no diretório correto?')
        exit()

    return all_games


def processing_start_end_time(log, game_id):
    # 1:47 InitGame: |||| 12:13 ShutdownGame:
    start_time_pattern = re.compile(r"(?P<starting_time>\d{1,3}:\d\d)\sInitGame:")
    end_time_pattern = re.compile(r"(?P<ending_time>\d{1,3}:\d\d)\sShutdownGame:")

    def create_game(start, end, game_id):
        return {
            "game_id": game_id,
            "start_time": start,
            "end_time": end,
            "status": {}
        }

    for line in log:
        start_time_match = start_time_pattern.match(line)
        end_time_match = end_time_pattern.match(line)

        if start_time_match is not None:
            start_time = start_time_match.group(1)

        if end_time_match is not None:
            end_time = end_time_match.group(1)

    return create_game(start_time, end_time, game_id)


def processing_total_kills(log, game_report):
    # 21:07 Kill: 
    kill_pattern = re.compile(r"\d{1,3}:\d\d\s(?P<kill>Kill:)")
    kill_counter = 0

    for line in log:
        kill_match = kill_pattern.match(line)
        if kill_match is not None:
            kill_counter += 1

    game_report["status"]["total_kills"] = kill_counter
    return game_report


def processing_players(log):
    # 21:51 ClientUserinfoChanged: 3 n\Dono da Bola\
    player_info_pattern = re.compile(r'\d{1,3}:\d\d\sClientUserinfoChanged:\s(?P<player_id>\d)\sn\\(?P<player_name>[\w\d\s]+)?\\')
    
    def create_player(player_id, player_name):
        return {
            "player_id": player_id,
            "name": player_name,
            "kills": 0,
            "old_names": [],
        }

    players = {}

    for line in log:
        player_info_match = player_info_pattern.match(line)

        if player_info_match is not None:
            player_id, player_name = player_info_match.group(1, 2)

            if players.get(player_id) is None:
                players[player_id] = create_player(player_id, player_name)

            if players[player_id]["name"] != player_name:
                players[player_id]["old_names"].append(players[player_id]["name"])
                players[player_id]["name"] = player_name

    return players


def processing_each_kill(log, players_info):
    # 21:42 Kill: 1022 2 22
    killer_victim_pattern = re.compile(r"\d{1,3}:\d\d\sKill:\s(?P<killer>\d+)\s(?P<victim>\d+)\s\d+:")

    for line in log:
        killer_victim_matches = killer_victim_pattern.match(line)

        if killer_victim_matches is not None:
            killer_id, victim_id = killer_victim_matches.group(1, 2)

            if killer_id == _world_id_:
                players_info[victim_id]["kills"] -= 1

            elif killer_id != victim_id:
                players_info[killer_id]["kills"] += 1

            elif killer_id == victim_id:
                players_info[killer_id]["kills"] -= 1
    
    return players_info


def synthetizing_all_data(game_report, players_info):

    game_report["status"]["players"] = list()

    for values in players_info.values():
        game_report["status"]["players"].append(values)


def main():
    json_report = []

    all_games = split_logs_into_separated_games("Quake.txt")

    for game_id, single_game in enumerate(all_games):
        game_report = processing_start_end_time(single_game, game_id + 1)
        processing_total_kills(single_game, game_report)
        player_info = processing_players(single_game)
        player_info = processing_each_kill(single_game, player_info)
        synthetizing_all_data(game_report, player_info)

        json_report.append(game_report)


    with open("json_report.json", "w") as f:
        json.dump(json_report, f, indent=4)


if __name__ == '__main__':
    main()
