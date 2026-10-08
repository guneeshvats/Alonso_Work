import pytest
from unittest.mock import MagicMock, patch
from app.services.nlp_processor import NlpProcessor
from app.constants import Qualifiers


@pytest.fixture
def mock_dependencies():
    mock_llm = MagicMock()
    mock_stat_matchers = {"MFB": {"Player": MagicMock()}}
    processor = NlpProcessor(mock_llm, mock_stat_matchers)
    return processor, mock_llm, mock_stat_matchers


@patch("app.services.nlp_processor.db")
@patch("app.services.nlp_processor.Folio")
@patch("app.services.nlp_processor.MappingsHandler")
def test_convert_to_aql_success(mock_mappings, mock_folio, mock_db, mock_dependencies):
    processor, mock_llm, mock_stat_matchers = mock_dependencies
    mock_team = {Qualifiers.TEAM_NAME.value: "Arkansas"}
    mock_db.__getitem__.return_value.find_one.return_value = mock_team

    mock_folio().get_prompt.return_value.text = "Conditions: {{ natural_language_query }} | {{ context.teamName }}"
    mock_stat_matchers["MFB"]["Player"].match.return_value = [{"stat": "sPoints", "description": "Points scored"}]
    mock_mappings().get_query_samples.return_value = ["query sample"]
    mock_mappings().get_pos_mapping.return_value = {"QB": "Quarterback"}

    llm_output = {
        "conditions": "sPoints > 20",
        "stat_period": "game",
        "qualifiers": {}
    }

    mock_llm.generate_response.return_value = str(llm_output).replace("'", '"')
    mock_llm.generate_response.return_value = '{"conditions": "sPoints > 20", "stat_period": "game", "qualifiers": {}}'

    result = processor.convert_to_aql("Who scored more than 20 points?", "MFB", "Player", "31")

    assert "conditions" in result
    assert result["qualifiers"]["teamName"] == "Arkansas"


@patch("app.services.nlp_processor.db")
def test_convert_to_aql_team_not_found(mock_db, mock_dependencies):
    processor, *_ = mock_dependencies
    mock_db.__getitem__.return_value.find_one.return_value = None

    with pytest.raises(ValueError, match="No team found for teamCode"):
        processor.convert_to_aql("test", "MFB", "Player", "99")


@patch("app.services.nlp_processor.db")
@patch("app.services.nlp_processor.Folio")
def test_convert_to_aql_missing_prompt(mock_folio, mock_db, mock_dependencies):
    processor, *_ = mock_dependencies
    mock_db.__getitem__.return_value.find_one.return_value = {"teamName": "Alabama"}
    mock_folio().get_prompt.return_value = None

    with pytest.raises(ValueError, match="Prompt 'nlp_query_conversion' is missing"):
        processor.convert_to_aql("test", "MFB", "Player", "31")


@patch("app.services.nlp_processor.db")
@patch("app.services.nlp_processor.Folio")
def test_convert_to_aql_missing_prompt(mock_folio, mock_db, mock_dependencies):
    processor, mock_llm, *_ = mock_dependencies
    mock_llm.generate_response.return_value = "INVALID_JSON"
    mock_db.__getitem__.return_value.find_one.return_value = {"teamName": "Alabama"}
    mock_folio().get_prompt.return_value.text = "{{ natural_language_query }}"
    mock_llm.generate_response.return_value = "INVALID_JSON"

    with pytest.raises(ValueError, match="Invalid JSON received from LLM"):
        processor.convert_to_aql("query", "MFB", "Player", "31")
