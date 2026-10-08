import pytest
from unittest.mock import MagicMock, patch
from app.services.stat_matcher import StatMatcher, StatIndex  
import numpy as np


@pytest.fixture
def mock_stat_index():
    index = MagicMock(spec=StatIndex)

    model = MagicMock()
    model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
    # Ensure first dimension (rows) matches len(corpus_embeddings)
    model.similarity.return_value = np.array([
        [0.99, 0.01],  # sPoints match high
        [0.20, 0.10],  # sYards match low
    ])
    index.model = model

    # Make sure this matches the row count in similarity
    index.corpus_embeddings = np.array([[0.1, 0.2], [0.3, 0.4]])

    # Mapping should match corpus_embeddings order
    index.stat_mapping = [
        {"stat": "sPoints", "description": "Points scored"},
        {"stat": "sYards", "description": "Yards gained"},
    ]
    index.ind2stat = ["sPoints", "sYards"]
    index.stat2ind = {"sPoints": 0, "sYards": 1}

    return index


def test_stat_matcher_match_returns_top_k(mock_stat_index):
    matcher = StatMatcher(mock_stat_index)
    results = matcher.match("Points and Yards", top_k=2)

    assert isinstance(results, list)
    assert len(results) > 0
    assert all("stat" in item for item in results)
    assert any(item["stat"] in ["sPoints", "sYards"] for item in results)



@patch("app.services.stat_matcher.StatIndex")
def test_stat_matcher_from_sport_and_entity(mock_stat_index_class):
    mock_index = MagicMock()
    mock_index.load = MagicMock()
    mock_stat_index_class.return_value = mock_index

    with patch("app.services.stat_matcher.INDEX_MAP", {"MFB": {"Player": "mock_path"}}):
        matcher = StatMatcher.from_sport_and_entity("MFB", "Player")
        assert isinstance(matcher, StatMatcher)
        mock_index.load.assert_called_once_with("mock_path")


@patch("app.services.stat_matcher.StatMatcher.from_sport_and_entity")
def test_stat_matcher_get_all_stat_matchers(mock_from_sport_and_entity):
    dummy_matcher = MagicMock()
    mock_from_sport_and_entity.side_effect = lambda s, e: dummy_matcher

    with patch("app.services.stat_matcher.INDEX_MAP", {
        "MFB": {"Player": "path1"},
        "MBB": {"Team": "path2"}
    }):
        matchers = StatMatcher.get_all_stat_matchers()

    assert isinstance(matchers, dict)
    assert matchers["MFB"]["Player"] == dummy_matcher
    assert matchers["MBB"]["Team"] == dummy_matcher
