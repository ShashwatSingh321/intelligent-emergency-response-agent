
import re
from pydantic import BaseModel, ConfigDict, Field

from emergency_response.models.emergency import EmergencyType


class ParsedEmergencyReport(BaseModel):
    """Structured information extracted from a natural-language report."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=3, max_length=2000)
    emergency_type: EmergencyType = EmergencyType.OTHER
    people_affected: int = Field(default=1, ge=1)
    location_hint: str | None = None


class EmergencyReportParser:
    """Extract basic emergency information from English and Hindi text."""

    TYPE_KEYWORDS = {
        EmergencyType.FIRE: (
            "fire", "burning", "smoke", "आग", "जल रहा", "जल रही",
            "धुआं", "धुआँ",
        ),
        EmergencyType.ACCIDENT: (
            "accident", "crash", "collision", "road accident",
            "दुर्घटना", "टक्कर", "एक्सीडेंट",
        ),
        EmergencyType.MEDICAL: (
            "medical", "injured", "injury", "unconscious", "bleeding",
            "heart attack", "sick", "घायल", "बेहोश", "खून बह",
            "चोट", "बीमार", "चिकित्सा",
        ),
        EmergencyType.SECURITY: (
            "theft", "robbery", "fight", "violence", "intruder",
            "suspicious person", "चोरी", "लड़ाई", "मारपीट",
            "संदिग्ध व्यक्ति",
        ),
    }

    NUMBER_WORDS = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "एक": 1,
        "दो": 2,
        "तीन": 3,
        "चार": 4,
        "पांच": 5,
        "पाँच": 5,
        "छह": 6,
        "सात": 7,
        "आठ": 8,
        "नौ": 9,
        "दस": 10,
    }

    LOCATION_PATTERN = re.compile(
        r"\b(?:near|at|outside|inside|beside)\s+"
        r"(.+?)(?=[,.!?;]|$)",
        re.IGNORECASE,
    )

    HINDI_LOCATION_PATTERN = re.compile(
        r"(?:के पास|के नज़दीक|के नजदीक|बाहर|अंदर)\s*"
        r"(.+?)(?=[,.!?;]|$)"
    )

    def parse(self, text: str) -> ParsedEmergencyReport:
        """Convert a free-text report into validated structured information."""

        if not isinstance(text, str):
            raise TypeError("Emergency report must be a string.")

        description = text.strip()

        if len(description) < 3:
            raise ValueError(
                "Emergency report must contain at least 3 characters."
            )

        if len(description) > 2000:
            raise ValueError(
                "Emergency report cannot exceed 2000 characters."
            )

        normalized = description.casefold()

        emergency_type = self._detect_emergency_type(normalized)
        people_affected = self._detect_people_count(normalized)
        location_hint = self._detect_location(description)

        return ParsedEmergencyReport(
            description=description,
            emergency_type=emergency_type,
            people_affected=people_affected,
            location_hint=location_hint,
        )

    def _detect_emergency_type(self, text: str) -> EmergencyType:
        """Identify the first matching emergency category."""

        for emergency_type, keywords in self.TYPE_KEYWORDS.items():
            if any(keyword.casefold() in text for keyword in keywords):
                return emergency_type

        return EmergencyType.OTHER

    def _detect_people_count(self, text: str) -> int:
        """Extract a simple count when the report explicitly mentions people."""

        number_pattern = "|".join(
            sorted(
                (
                    *self.NUMBER_WORDS.keys(),
                    r"\d+",
                ),
                key=len,
                reverse=True,
            )
        )

        patterns = (
            rf"\b({number_pattern})\s+"
            r"(?:people|persons|person|victims|victim|students|workers)\b",
            rf"\b({number_pattern})\s+"
            r"(?:लोग|व्यक्ति|व्यक्तियों|पीड़ित|पीड़ित)\b",
        )

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                token = match.group(1).casefold()

                if token.isdigit():
                    count = int(token)
                else:
                    count = self.NUMBER_WORDS[token]

                # Avoid accepting an implausibly large count from a typo.
                if count >= 1:
                    return count

        return 1

    def _detect_location(self, text: str) -> str | None:
        """Extract a simple location clue; this does not verify campus locations."""

        match = self.LOCATION_PATTERN.search(text)

        if match:
            return match.group(1).strip()

        match = self.HINDI_LOCATION_PATTERN.search(text)

        if match:
            return match.group(1).strip()

        return None
