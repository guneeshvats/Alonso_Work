import argparse
import json
import os
import random
from decouple import config
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
import pandas as pd
from copy import deepcopy
# Get MongoDB connection string from environment variables
mongo_uri = config('DB_URI')
db_name = config('DB_NAME')

# Connect to MongoDB using PyMongo
client = MongoClient(mongo_uri)
db = client[db_name]
playergame_collection = db['PlayerGameStatistics']
statmapping_collection = db['stat_mapping']
roster_collection = db['ActiveRoster']
team_collection = db['teams']
conference_collection = db['conferences']

# Define output folder
OUTPUT_FOLDER = "query_outputs"


# Natural language templates
def load_templates(base_path="templates"):
    templates = {}
    for root_fol in ["player", "team"]:
        templates[root_fol] = {}
        fol_path = os.path.join(base_path, root_fol)
        for filename in os.listdir(fol_path):
            if filename.endswith(".json"):
                fkey = filename.split(".")[0]
                templates[root_fol][fkey] = json.loads(open(os.path.join(fol_path, filename)).read())
    return templates


templates = load_templates()


def generate_query(query_type="simple",
                   num_samples=1,
                   sport_code="MFB",
                   entity="player",
                   g_team_id=33,
                   stat_period="all",
                   generate_all=False,
                   generate_aliases = False,
                   template_id=None):
    """Generates test queries based on given configurations."""
    queries = []
    stat_mappings = get_stat_mapping(sport_code,entity)
    teams = get_teams()
    conferences = get_conferences()
    player_classes = get_player_classes()
    player_classes_sg = get_player_classes(mode="sg")
    players = get_players(g_team_id)
    player_positions = get_player_positions(sport_code)
    seasons = [2014 + i for i in range(11)]

    selected_templates = templates[entity][query_type]

    if generate_all:
        print(f"You choose enumeration, so changing num_samples to {len(stat_mappings)}")
        num_samples = len(stat_mappings)



    if stat_period != "all":
        selected_templates = [x for x in selected_templates if x["stat_period"] == stat_period]

    for sample_idx in range(num_samples):
        if template_id is not None:
            # template = selected_templates[template_id - 1]
            template = next((t for t in selected_templates if t["id"] == template_id), None)
            if template is None:
                raise ValueError(f"Template with id={template_id} not found for query_type={query_type}, entity={entity}, stat_period={stat_period}")

            #print(f"Generating query for template {template_id} = {json.dumps(template, indent=4)}")
        else:
            template = random.choice(selected_templates)

        num_stats = template["num_stats"]
        # if not generate_all:
        #     selected_stats = random.sample(stat_mappings, num_stats)
        # else:
        #     selected_stats = [stat_mappings[sample_idx]]
        if not generate_all:
            selected_stats = random.sample(stat_mappings, num_stats)
        else:
            # Safe: always get exactly num_stats items, even if it means cycling
            selected_stats = [stat_mappings[(sample_idx + i) % len(stat_mappings)] for i in range(num_stats)]


        aliases = [selected_stats]
        # if generate_aliases:
        #     for alias in stat_mappings[sample_idx]["aliases"]:
        #         new_stat = deepcopy(selected_stats[0])
        #         new_stat["name"] = alias
        #         aliases += [[new_stat]]
        if generate_aliases:
            alias_combinations = []

            # Build alias variants for each stat in selected_stats
            for i, stat in enumerate(selected_stats):
                stat_aliases = stat.get("aliases", [stat["name"]])
                alias_combinations.append([
                    {**stat, "name": alias} for alias in stat_aliases
                ])

            # Generate all combinations of aliases (one from each stat)
            from itertools import product
            for combo in product(*alias_combinations):
                aliases.append(list(combo))


        for alias in aliases:
            selected_stats = alias
            #print(selected_stats)
            #selected_stats = stat_mappings.sample(num_stats).to_dict("records")
            values = [random.randint(50, 200) for _ in selected_stats]

            # Generate labels for query (can be any of the three)
            stat_labels = {f"stat{i + 1}": stat["name"].lower() for i, stat in enumerate(selected_stats)}

            # Generate labels for conditions (always use AthlyteLabel)
            stat_labels_conditions = {f"stat{i + 1}_label": stat["stat"] for i, stat in enumerate(selected_stats)}

            # Generate random values
            stat_values = {f"value{i + 1}": values[i] for i in range(len(values))}

            streak_len = random.randint(2, 50)

            # Handle qualifiers if query type is 'qualifier'
            qualifiers = {}
            if query_type != "simple":
                for key, value in template.get("qualifiers", {}).items():
                    if value.startswith("{") and value.endswith("}"):
                        if key == "teamName" and teams:
                            qualifiers[key] = random.choice(teams)
                        elif key == "teamConferenceName" and conferences:
                            qualifiers[key] = random.choice(conferences)
                        elif key == "playerName" and players:
                            qualifiers[key] = random.choice(players)
                        elif key == "opponentTeamName" and teams:
                            qualifiers[key] = random.choice(teams)
                            # qualifiers["opponent_type"] = "Team"
                        elif key == "opponentConferenceName" and conferences:
                            qualifiers[key] = random.choice(conferences)
                        elif key == "season" and conferences:
                            qualifiers[key] = random.choice(seasons)
                        elif key == "isHomeGame" and conferences:
                            qualifiers[key] = random.choice([True, False])
                        # qualifiers["opponent_type"] = "Conference"
                        elif key == "playerClass":
                            r = random.randrange(len(player_classes_sg))
                            qualifiers[key] = player_classes[r]
                        elif key == "position":
                            selected_key = random.choice(list(player_positions[sport_code].keys()))
                            qualifiers[key] = selected_key
                    else:
                        qualifiers[key] = value
                #print(template, stat_labels, stat_labels_conditions, stat_values, streak_len, qualifiers)
                query_str = template["nlp_query"].format(**stat_labels, **stat_values, **qualifiers, streak_len=streak_len)
                if "playerClass" in qualifiers:
                    qualifiers["playerClass"] = player_classes_sg[qualifiers["playerClass"]]
                if "position" in qualifiers:
                    # qualifiers["position"] = player_positions[qualifiers["position"]]
                    key = qualifiers["position"]
                    qualifiers["position"] = player_positions[sport_code][key]
                conditions = template["expected_output"].format(**stat_labels_conditions, **stat_values)
            else:
                query_str = template["nlp_query"].format(**stat_labels, **stat_values)
                conditions = template["expected_output"].format(**stat_labels_conditions, **stat_values)

            structured_output = {
                "entity": entity,
                "query": query_str,
                "aql": {
                    "query_type": template["query_type"],
                    "entity": entity,
                    "qualifiers": qualifiers,
                    "stat_period": template["stat_period"],
                    "conditions": conditions,
                    "streak_len" : streak_len if query_type == "streak" else None,
                }
            }

            queries.append(structured_output)

    return queries


def save_queries_to_file(queries, query_type, entity, num_samples):
    """Saves generated queries to a JSON file with timestamped filename."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # Generate filename with date
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{OUTPUT_FOLDER}/{query_type}_{entity}_{num_samples}_{timestamp}.json"

    # Save queries to file
    with open(filename, "w") as f:
        json.dump(queries, f, indent=4)

    print(f"Queries saved to {filename}")


def get_stat_mapping(sport_code,entity):
    stat_mappings_dir = "stat_mapping"
    stat_mapping_file = os.path.join(stat_mappings_dir, sport_code, entity.title() + ".json")
    return json.loads(open(stat_mapping_file).read())

    # stat_mappings = list(statmapping_collection.find({"entity": entity.lower(), "R1": True}))
    # return stat_mappings


def get_teams():
    teams = [team['teamName'] for team in team_collection.find({})]
    return teams


def get_players(g_team_id):
    players = [x['playerName'] for x in roster_collection.find({"gTeamId": g_team_id})]
    return players


def get_conferences():
    confs = [conf['conferenceName'] for conf in conference_collection.find({})]
    return confs


def get_player_classes(mode="pl"):
    if mode == "pl":
        return ["freshmen", "sophomores", "juniors", "seniors"]
    else:
        return {"freshmen": "freshman",
                "sophomores": "sophomore",
                "juniors": "junior",
                "seniors": "senior"}


def get_player_positions(sport_code:str = "MFB"):

    position_map = {
        "MFB": {
            "Cornerbacks": "CB",
            "Defensive Backs": "DB",
            "Defensive Ends": "DE",
            "Defensive Linemans": "DL",
            "Defensive Tackles": "DT",
            "Fullbacks": "FB",
            "Kickers": "K",
            "Linebackers": "LB",
            "Long Snappers": "LS",
            "Offensive Centers": "OC",
            "Offensive Guards": "OG",
            "Offensive Linemans": "OL",
            "Offensive Tackles": "OT",
            "Punters": "P",
            "Quarterbacks": "QB",
            "Running Backs": "RB",
            "Safeties": "S",
            "Tight Ends": "TE",
            "Wide Receivers": "WR",
            "Offensive Players": "OFF",
            "Defensive Players": "DEF",
            "Special Teams Players": "STP"
        },
        "MBB": {
            "Center" : "C",
            "Forward" : "F",
            "Guard" : "G"
        }

    }

    return position_map


def add_arguments(parser):
    """
    Adds command-line arguments to the argument parser.
    """
    parser.add_argument("--num_samples", type=int, default=1, help="Number of test queries to generate")
    parser.add_argument("--query_type", type=str, choices=["simple", "qualifiers", "min_max", "ltw", "streak"], default="simple",
                        help="Type of query to generate")
    parser.add_argument("--sport_code", type=str, choices=["MFB", "MBB"], default="MFB",
                        help="Entity to generate queries for")
    parser.add_argument("--entity", type=str, choices=["team", "player"], default="player",
                        help="Entity to generate queries for")
    parser.add_argument("--stat_period", type=str, choices=["all", "quarter", "game", "season", "career"], default="all",
                        help="Only generate queries for specified stat period")
    parser.add_argument("--g_team_id", default=33, type=int, help="Genius team id for players list")
    parser.add_argument("--template_id", type=int, help="Genius team id for players list")
    parser.add_argument("--generate_all", default=False, action="store_true", help="Enumerates all possibilities")
    parser.add_argument("--aliases", default=False, action="store_true", help="Enumerates all aliases as well")
    parser.add_argument("--help-custom", action="store_true", help="Show custom help message")
    parser.add_argument("--save-queries", action="store_true", help="Save queries to file")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    return parser


def display_help():
    """
    Displays a help message for using the Test Generation Framework.
    """
    print("Test Generation Framework - Command-Line Utility")
    print("Usage: python testGeneration.py [options]")
    print("\nOptions:")
    print("  --num_samples <int>    Number of test queries to generate (default: 1)")
    print("  --query_type <type>    Type of query to generate (choices: simple, qualifiers) (default: simple)")
    print("  --entity <entity>      Entity to generate queries for (choices: team, player) (default: player)")
    print("  --help-custom          Show this custom help message")


def main():
    parser = argparse.ArgumentParser(description="Test Generation Framework")
    parser = add_arguments(parser)
    args = parser.parse_args()

    if args.help_custom:
        display_help()
        return

    results = generate_query(sport_code=args.sport_code,
                             query_type=args.query_type,
                             entity=args.entity,
                             template_id = args.template_id,
                             num_samples=args.num_samples,
                             stat_period=args.stat_period,
                             generate_all=args.generate_all,
                             generate_aliases=args.aliases,
                             g_team_id=args.g_team_id)
    if args.debug:
        print(json.dumps(results, indent=4))
    if args.save_queries:
        save_queries_to_file(results, args.query_type, args.entity, args.num_samples)


if __name__ == "__main__":
    main()
