
import re

from pydantic import BaseModel, ConfigDict, Field

from emergency_response.models.emergency import EmergencyType


class ParsedEmergencyReport(BaseModel):
    """Structured information extracted from an emergency report."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=3, max_length=2000)
    emergency_type: EmergencyType = EmergencyType.OTHER
    people_affected: int = Field(default=1, ge=1)
    location_hint: str | None = None


class EmergencyReportParser:
    """Rule-based emergency parser for English and Hindi reports."""

    TYPE_KEYWORDS = {
        EmergencyType.FIRE: (
            "fire", "burning", "smoke",
            "आग", "आग लगी", "जल रहा", "जल रही", "धुआँ", "धुआं",
        ),
        EmergencyType.ACCIDENT: (
            "accident", "crash", "collision", "road accident",
            "दुर्घटना", "एक्सीडेंट", "टक्कर", "सड़क हादसा",
        ),
        EmergencyType.MEDICAL: (
            "medical", "injured", "injury", "unconscious",
            "bleeding", "heart attack", "sick",
            "घायल", "बेहोश", "खून बह", "दिल का दौरा",
            "तबीयत", "बीमार", "चोट",
        ),
        EmergencyType.SECURITY: (
            "theft", "robbery", "fight", "violence", "intruder",
            "suspicious person",
            "चोरी", "लूट", "लड़ाई", "मारपीट", "हिंसा",
            "संदिग्ध व्यक्ति",
        ),
    }

    NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5,
        "पांच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9,
        "दस": 10,
    }

    LOCATION_PATTERN = re.compile(
        r"\b(?:near|at|outside|inside|beside)\s+"
        r"(.+?)(?=[,.!?;]|$)",
        re.IGNORECASE,
    )

    HINDI_LOCATION_PATTERN = re.compile(
        r"(?:के पास|के नज़दीक|के नजदीक|बाहर|अंदर|के सामने|में)\s*"
        r"(.+?)(?=[,.!?;]|$)"
    )

    def parse(self, text: str) -> ParsedEmergencyReport:
        """Extract and validate basic emergency details."""

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

        return ParsedEmergencyReport(
            description=description,
            emergency_type=self._detect_emergency_type(normalized),
            people_affected=self._detect_people_count(normalized),
            location_hint=self._detect_location(description),
        )

    def _detect_emergency_type(self, text: str) -> EmergencyType:
        """Identify a category using configured keywords."""

        # Prefer more specific accident clues over general injury clues.
        for emergency_type in (
            EmergencyType.FIRE,
            EmergencyType.ACCIDENT,
            EmergencyType.SECURITY,
            EmergencyType.MEDICAL,
        ):
            if any(
                keyword.casefold() in text
                for keyword in self.TYPE_KEYWORDS[emergency_type]
            ):
                return emergency_type

        return EmergencyType.OTHER

    def _detect_people_count(self, text: str) -> int:
        """Extract an explicit count of affected people."""

        words = "|".join(
            re.escape(word)
            for word in sorted(self.NUMBER_WORDS, key=len, reverse=True)
        )
        number = rf"(?:\d+|{words})"

        patterns = (
            rf"\b({number})\s+"
            r"(?:people|persons|person|victims|victim|students|workers)\b",
            rf"({number})\s*"
            r"(?:लोग|व्यक्ति|छात्र|छात्रों|घायल)",
        )

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if not match:
                continue

            token = match.group(1).casefold()
            count = (
                int(token)
                if token.isdigit()
                else self.NUMBER_WORDS[token]
            )

            # Ignore unreasonable values rather than trusting a typo.
            if 1 <= count <= 1000:
                return count

        return 1


  
    def _detect_location(self, text: str) -> str | None:
        """Extract a location clue from English or Hindi text."""

        # English: "near the main gate", "at the library"
        match = self.LOCATION_PATTERN.search(text)
        if match:
            return match.group(1).strip()

        # Hindi: the location normally comes BEFORE "के पास",
        # "के सामने", "के नज़दीक", etc.
        hindi_pattern = re.compile(
            r"(.+?)\s+(?:के पास|के नज़दीक|के नजदीक|के सामने)"
            r"(?=\s|[,.!?।]|$)"
        )
        match = hindi_pattern.search(text)

        if match:
            location = match.group(1).strip()

            # If the sentence begins with a common introductory phrase,
            # keep the location portion after it.
            prefixes = (
                "घटना ",
                "आपातकाल ",
                "कृपया ",
            )
            for prefix in prefixes:
                if location.startswith(prefix):
                    location = location[len(prefix):].strip()

            return location or None

        # Hindi: "लाइब्रेरी में आग लगी है"
        hindi_in_pattern = re.compile(
            r"(.+?)\s+में\s+(?="
            r"आग|दुर्घटना|एक्सीडेंट|हादसा|चोरी|लड़ाई|"
            r"बेहोश|घायल|धुआँ|धुआं"
            r")"
        )
        match = hindi_in_pattern.search(text)

        if match:
            return match.group(1).strip()

        return None
