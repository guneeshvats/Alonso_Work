# Test Generation Framework

## Overview
The **Test Generation Framework** is a Python-based command-line utility designed to generate natural language test queries for sports statistics, particularly for NCAA football (MFB) and basketball (MBB). The framework interacts with MongoDB to fetch relevant team, player, and statistics data and formats it into structured test queries using predefined templates.

## Features
- Generates test queries based on templates for **players** and **teams**.
- Supports various **query types**, including:
  - Simple queries
  - Qualifier-based queries
  - Min/Max queries
  - Longest to Win (LTW) queries
  - Streak queries
- Allows specifying the **sport code** (MFB, MBB) and **statistical period** (quarter, game, season, career, all).
- Fetches **teams, players, and conferences** from MongoDB for query generation.
- Saves generated queries as JSON files with timestamps.
- Provides a **debug mode** to inspect generated queries.

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.x
- MongoDB
- Required Python packages (install using the command below)

```sh
pip install python-decouple pymongo pandas
```

## Configuration
Before running the script, configure your MongoDB connection details using environment variables.

Create a `.env` file and add the following:

```env
DB_URI=mongodb://your_mongo_host:your_mongo_port
DB_NAME=your_database_name
```

## Usage

### Command-Line Options
Run the script with the following options:

```sh
python testGeneration.py [options]
```

| Option | Description |
|--------|-------------|
| `--num_samples <int>` | Number of test queries to generate (default: 1) |
| `--query_type <type>` | Query type: `simple`, `qualifiers`, `min_max`, `ltw`, `streak` (default: `simple`) |
| `--sport_code <str>` | Sport code: `MFB` (Football), `MBB` (Basketball) (default: `MFB`) |
| `--entity <str>` | Entity type: `team`, `player` (default: `player`) |
| `--stat_period <str>` | Stat period: `all`, `quarter`, `game`, `season`, `career` (default: `all`) |
| `--g_team_id <int>` | Genius team ID for fetching players (default: `33`) |
| `--template_id <int>` | Specific template ID to use |
| `--save-queries` | Save generated queries to a JSON file |
| `--debug` | Enable debug mode to print queries |
| `--help-custom` | Display custom help message |

### Examples

#### Generate a simple player query:
```sh
python testGeneration.py --query_type simple --entity player --num_samples 5
```

#### Generate a qualifier-based team query and save the output:
```sh
python testGeneration.py --query_type qualifiers --entity team --save-queries
```

#### Generate a streak query for NCAA football:
```sh
python testGeneration.py --query_type streak --sport_code MFB --num_samples 3
```

## Output
Generated queries are saved in the `query_outputs` directory as timestamped JSON files:

```
query_outputs/
  simple_player_5_2025-03-18_12-30-45.json
  qualifiers_team_3_2025-03-18_12-45-10.json
```

Each file contains structured queries in the following format:
```json
[
  {
    "entity": "player",
    "query": "Which player has the highest rushing yards?",
    "aql": {
      "query_type": "simple",
      "entity": "player",
      "qualifiers": {},
      "stat_period": "all",
      "conditions": "rushing_yards > 100"
    }
  }
]
```

## Project Structure
```
.
├── testGeneration.py  # Main script
├── templates/         # JSON templates for query generation
├── query_outputs/     # Stores generated query files
├── .env               # Environment variables for MongoDB
└── README.md          # Documentation
```

## Contributors
- **Your Name** *(Developer)*

## License
This project is licensed under the MIT License.

