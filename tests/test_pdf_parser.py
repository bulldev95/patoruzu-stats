from unittest.mock import MagicMock, patch

from utils.pdf_parser import parse_team_sheet
from tests.conftest import SAMPLE_PDF_TEXT, SAMPLE_PDF_TEXT_LOCAL


def make_pdf_mock(text):
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    return mock_pdf


@patch("utils.pdf_parser.pdfplumber")
def test_parse_date(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    assert result["date"] == "2026-08-15"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_venue(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    assert result["venue"] == "DRAIG GOCH - Chubut"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_competition(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    assert result["competition"] == "Torneo Austral 2026 (Primera División)"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_rival_visitante_sheet(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    assert result["rival"] == "DRAIG GOCH - Chubut"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_rival_local_sheet(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT_LOCAL)
    result = parse_team_sheet("fake.pdf")
    assert result["rival"] == "OTRO CLUB - Chubut"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_player_count(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    assert len(result["players"]) == 23


@patch("utils.pdf_parser.pdfplumber")
def test_parse_first_player(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    first = result["players"][0]
    assert first["number"] == 1
    assert first["name"] == "Roldan, Denis"
    assert first["personal_id"] == "38797877"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_last_player(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    last = result["players"][-1]
    assert last["number"] == 23
    assert last["personal_id"] == "32801274"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_player_numbers_sequential(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    numbers = [p["number"] for p in result["players"]]
    assert numbers == list(range(1, 24))


@patch("utils.pdf_parser.pdfplumber")
def test_parse_multiword_name(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    murillo = next(p for p in result["players"] if p["number"] == 6)
    assert murillo["name"] == "Murillo Del Prado, Tomas"


@patch("utils.pdf_parser.pdfplumber")
def test_parse_ffi_ligature_fixed(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    griffiths = next(p for p in result["players"] if p["number"] == 21)
    assert griffiths["name"] == "Griffiths, Tomas"
    assert "`" not in griffiths["name"]


@patch("utils.pdf_parser.pdfplumber")
def test_parse_personal_ids_are_strings(mock_pdfplumber):
    mock_pdfplumber.open.return_value = make_pdf_mock(SAMPLE_PDF_TEXT)
    result = parse_team_sheet("fake.pdf")
    for player in result["players"]:
        assert isinstance(player["personal_id"], str)
        assert player["personal_id"].isdigit()
