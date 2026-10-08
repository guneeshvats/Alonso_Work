# tests/app/data_config/test_mappings_handler.py

import pytest
import builtins
from unittest.mock import patch, mock_open
from app.data_config.mappings.mappings_handler import MappingsHandler



@pytest.fixture
def mock_handler():
    with patch("builtins.open", mock_open(read_data='{"key": "value"}')), \
         patch("os.path.exists", return_value=True), \
         patch("json.load", return_value={"query_samples": ["sample query"]}):
        yield MappingsHandler()


@patch("builtins.open", new_callable=mock_open, read_data='{"MFB": {"Player": {"game": "player_game_table"}}}')
@patch("json.load", return_value={"MFB": {"Player": {"game": "player_game_table"}}})
def test_get_table_name(mock_json, mock_file):
    handler = MappingsHandler()
    assert handler.get_table_name("MFB", "Player", "game") == "player_game_table"


@patch("builtins.open", new_callable=mock_open, read_data='{"MFB": {"Player": {"game": {"basic": ["stat1", "stat2"]}}}}')
@patch("json.load", return_value={"MFB": {"Player": {"game": {"basic": ["stat1", "stat2"]}}}})
def test_get_fields_for_query(mock_json, mock_file):
    handler = MappingsHandler()
    fields = handler.get_fields_for_query("MFB", "Player", "game", "basic")
    assert fields == ["stat1", "stat2"]


def test_load_filter_mappings(mock_handler):
    result = mock_handler.load_filter_mappings()
    assert isinstance(result, dict)


@patch("builtins.open", new_callable=mock_open, read_data='[{"stat": "s1", "label": "Stat One"}]')
@patch("json.load", return_value=[{"stat": "s1", "label": "Stat One"}])
def test_get_stat_mapping(mock_json, mock_file):
    handler = MappingsHandler()
    mapping = handler.get_stat_mapping("MFB", "Player")
    assert isinstance(mapping, list)


@patch("builtins.open", new_callable=mock_open, read_data='{"query_samples": ["sample1"]}')
@patch("json.load", return_value={"query_samples": ["sample1"]})
def test_get_query_samples_dict(mock_json, mock_file):
    handler = MappingsHandler()
    samples = handler.get_query_samples("MFB", "Player")
    assert samples == ["sample1"]


@patch("builtins.open", new_callable=mock_open, read_data='["sample1", "sample2"]')
@patch("json.load", return_value=["sample1", "sample2"])
def test_get_query_samples_list(mock_json, mock_file):
    handler = MappingsHandler()
    samples = handler.get_query_samples("MFB", "Player")
    assert "sample1" in samples


def test_get_pos_mapping(mock_handler):
    result = mock_handler.get_pos_mapping("MFB")
    assert isinstance(result, dict)


def test_get_metadata_mapping(mock_handler):
    result = mock_handler.get_metadata_mapping()
    assert isinstance(result, dict)
