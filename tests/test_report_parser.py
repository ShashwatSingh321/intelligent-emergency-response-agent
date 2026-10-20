
import pytest

from emergency_response.ai.report_parser import EmergencyReportParser
from emergency_response.models.emergency import EmergencyType


@pytest.fixture
def parser():
    return EmergencyReportParser()


def test_parses_accident_report(parser):
    result = parser.parse(
        "There has been a bike accident near the main gate. "
        "Two people are injured."
    )

    assert result.emergency_type == EmergencyType.ACCIDENT
    assert result.people_affected == 2
    assert result.location_hint == "the main gate"


def test_parses_fire_report(parser):
    result = parser.parse("There is a fire inside the laboratory.")

    assert result.emergency_type == EmergencyType.FIRE
    assert result.location_hint == "the laboratory"


def test_parses_medical_report(parser):
    result = parser.parse("One student is unconscious at the library.")

    assert result.emergency_type == EmergencyType.MEDICAL
    assert result.people_affected == 1
    assert result.location_hint == "the library"


def test_parses_security_report(parser):
    result = parser.parse("There has been a theft near the hostel.")

    assert result.emergency_type == EmergencyType.SECURITY
    assert result.location_hint == "the hostel"


def test_parses_real_hindi_fire_report(parser):
    result = parser.parse("लाइब्रेरी के पास आग लगी है।")

    assert result.emergency_type == EmergencyType.FIRE
    assert result.location_hint == "लाइब्रेरी"


def test_parses_real_hindi_accident_and_people_count(parser):
    result = parser.parse("मुख्य द्वार के पास दुर्घटना हुई। दो लोग घायल हैं।")

    assert result.emergency_type == EmergencyType.ACCIDENT
    assert result.people_affected == 2
    assert result.location_hint == "मुख्य द्वार"


def test_parses_hindi_medical_report(parser):
    result = parser.parse("एक छात्र लाइब्रेरी में बेहोश है।")

    assert result.emergency_type == EmergencyType.MEDICAL
    assert result.people_affected == 1


def test_unknown_emergency_defaults_to_other(parser):
    result = parser.parse("Something unusual has happened.")

    assert result.emergency_type == EmergencyType.OTHER
    assert result.people_affected == 1


@pytest.mark.parametrize("text", ["", "  ", "ab"])
def test_rejects_too_short_report(parser, text):
    with pytest.raises(ValueError):
        parser.parse(text)


def test_rejects_report_over_2000_characters(parser):
    with pytest.raises(ValueError):
        parser.parse("a" * 2001)


def test_trims_report_whitespace(parser):
    result = parser.parse("  Fire near the main gate.  ")

    assert result.description == "Fire near the main gate."
