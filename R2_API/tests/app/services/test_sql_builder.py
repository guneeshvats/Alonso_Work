import unittest
from unittest.mock import MagicMock, patch
from app.services.sql_builder import SQLBuilder
from app.constants import QueryTypes, SortingFields

class TestSQLBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = SQLBuilder()
        self.mock_table_name = "player_game_statistics"
        self.mock_template = "SELECT {selected_columns} FROM {table_name} {where_clause} LIMIT {limit} OFFSET {offset};"

        # Mocking dependencies
        self.builder.mappings_handler.get_table_name = MagicMock(return_value=self.mock_table_name)
        self.builder.mappings_handler.get_fields_for_query = MagicMock(return_value=["playername", "teamname"])
        self.builder.mappings_handler.load_filter_mappings = MagicMock(return_value={
            "season": ("season", "=")
        })
        self.builder.sql_loader.load_template = MagicMock(return_value=self.mock_template)

    def test_convert_aql_to_sql_basic(self):
        aql_output = {
            "stat_period": "game",
            SortingFields.CONDITIONS.value: "sPoints >= 10",
            SortingFields.QUALIFIERS.value: {"teamname": "Alabama"}
        }

        sql_query, count_query, selected_columns, stat_columns = self.builder.convert_aql_to_sql(
            aql_output, "MFB", "Player", {}, QueryTypes.BASIC.value, "31"
        )

        self.assertIn("SELECT", sql_query)
        self.assertIn("teamname = 'Alabama'", sql_query)
        self.assertIn("sPoints", sql_query)
        self.assertIn("playername", sql_query)
        self.assertEqual("playername" in selected_columns, True)
        self.assertEqual("sPoints" in stat_columns, True)

    def test_build_where_clause_conditions(self):
        where_clause = self.builder._build_where_clause(
            "sPoints >= 5", {"teamname": "Texas"}, {"season": "2023"}, QueryTypes.BASIC.value
        )
        self.assertIn("sPoints >= 5", where_clause)
        self.assertIn("teamname = 'Texas'", where_clause)
        self.assertIn("season = '2023'", where_clause)

    def test_generate_query_sql(self):
        aql_output = {
            "stat_period": "game",
            SortingFields.CONDITIONS.value: "sAssists > 2"
        }
        selected_columns = ["playername", "sAssists"]
        where_clause = "sAssists > 2"
        sql_query, count_query, _, _ = self.builder._generate_query(
            query_type=QueryTypes.BASIC.value,
            table_name=self.mock_table_name,
            selected_columns=selected_columns,
            where_clause=where_clause,
            aql_output=aql_output,
            limit=10,
            offset=0,
            sort_by=None,
            sort_order=None,
            entity="Player",
            team_code="31",
            sport_code="MFB"
        )
        self.assertIn("SELECT", sql_query)
        self.assertIn("FROM player_game_statistics", sql_query)

    def test_invalid_query_type(self):
        aql_output = {"stat_period": "game"}
        with self.assertRaises(ValueError):
            self.builder.convert_aql_to_sql(
                aql_output, "MFB", "Player", {}, "invalid_query", "31"
            )

    def test_missing_stat_field_min_query(self):
        aql_output = {
            "stat_period": "game",
            SortingFields.CONDITIONS.value: ""
        }
        with self.assertRaises(ValueError):
            self.builder.convert_aql_to_sql(
                aql_output, "MFB", "Player", {}, QueryTypes.MIN.value, "31"
            )

if __name__ == "__main__":
    unittest.main()
