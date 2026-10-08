# tests/app/db/test_pgsql_adapter.py

import pytest
from unittest.mock import MagicMock, patch
from app.db.pgsql_adapter import PGSQLAdapter


@pytest.fixture
def mock_pgsql_adapter():
    with patch("app.db.pgsql_adapter.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        adapter = PGSQLAdapter()
        adapter.conn = mock_conn
        adapter.cursor = mock_cursor
        yield adapter


@patch("app.db.pgsql_adapter.MappingsHandler")
def test_execute_query_success(mock_mappings, mock_pgsql_adapter):
    # Setup mock values
    mock_pgsql_adapter.cursor.fetchall.return_value = [
        (1, "John", "TeamX", "QB", "2022-10-01", "TeamY", "W", 120, 2)
    ]
    mock_pgsql_adapter.cursor.description = [
        ("id",), ("playername",), ("teamname",), ("position",), ("gamedate",),
        ("opponentteamname",), ("gameresult",), ("rushing_yards",), ("touchdowns",)
    ]
    mock_pgsql_adapter.cursor.fetchone.return_value = [1]

    mock_mappings().get_metadata_mapping.return_value = {
        "playername": "PLAYER", "teamname": "TEAM", "position": "POS"
    }

    # Patch stat_mapping
    mock_pgsql_adapter.fetch_stat_mapping = MagicMock(return_value={
        "rushing_yards": "RUSH_YDS", "touchdowns": "TDS"
    })

    sql = "SELECT * FROM table;"
    count_sql = "SELECT COUNT(*) FROM table;"
    selected_cols = ["playername", "teamname"]
    stat_cols = ["rushing_yards", "touchdowns"]

    results, count = mock_pgsql_adapter.execute_query(
        sql, count_sql, selected_cols, "MFB", "Player", stat_cols
    )

    assert count == 1
    assert isinstance(results, list)
    assert "metadata" in results[0]
    assert "stats" in results[0]
    assert results[0]["stats"]["RUSH_YDS"] == 120
    assert results[0]["stats"]["TDS"] == 2


def test_execute_query_aql_only(mock_pgsql_adapter):
    results, count = mock_pgsql_adapter.execute_query(
        "SQL", "COUNT", [], "MFB", "Player", [], aql_only=True
    )
    assert results == []
    assert count == 0


@patch("app.db.pgsql_adapter.os.path.exists", return_value=False)
def test_fetch_stat_mapping_file_not_found(_, mock_pgsql_adapter):
    result = mock_pgsql_adapter.fetch_stat_mapping("MFB", "Player")
    assert result == {}
