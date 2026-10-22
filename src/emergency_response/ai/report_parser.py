
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
    """Rule-based parser for English, Hindi, and Hinglish reports."""

    TYPE_KEYWORDS = {
        EmergencyType.FIRE: (
            "fire", "burning", "smoke", "flames",
            "aag", "aag lagi", "aag lag gayi", "aag lagyi",
            "dhua", "dhuan", "dhuaan", "आग", "आग लगी",
            "धुआं", "धुआँ",
        ),
        EmergencyType.ACCIDENT: (
            "accident", "crash", "collision", "road accident",
            "takra", "takra gaya", "gaadi takra", "car crash",
            "दुर्घटना", "टक्कर", "एक्सीडेंट",
        ),
        EmergencyType.SECURITY: (
            "theft", "robbery", "fight", "violence", "intruder",
            "suspicious person", "chori", "chor", "loot",
            "maar-peet", "marpeet", "ladayi", "ladai",
            "झगड़ा", "चोरी", "लड़ाई", "मारपीट", "लूट",
        ),
        EmergencyType.MEDICAL: (
            "medical emergency", "medical", "injured", "injury",
            "unconscious", "unresponsive", "bleeding", "heart attack",
            "sick", "hurt", "wound", "ambulance",
            "chot", "chot lagi", "chot lagyi", "chot lag gayi",
            "ghayal", "behosh", "behush", "khoon beh",
            "saans nahi", "tabiyat kharab", "dard",
            "चोट", "घायल", "बेहोश", "खून", "दिल का दौरा",
        ),
    }

    NUMBER_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "ek": 1, "aik": 1, "do": 2, "teen": 3, "tin": 3,
        "char": 4, "chaar": 4, "paanch": 5, "panch": 5,
        "cheh": 6, "chhe": 6, "saat": 7, "aath": 8,
        "nau": 9, "das": 10,
        "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5,
        "पाँच": 5, "छह": 6, "छः": 6, "सात": 7,
        "आठ": 8, "नौ": 9, "दस": 10,
    }

    # Known campus names and aliases. Longer names are checked first.
    LOCATION_ALIASES = (
        "vishveshvaraya building",
        "vishveshwarya building",
        "vishveshvaraya",
        "vishveshwarya",
        "vishwakarma building",
        "vivekananda building",
        "chanakya building",
        "central library",
        "medical center",
        "medical centre",
        "health center",
        "health centre",
        "playground behind boys hostel",
        "second parking area",
        "first parking area",
        "girls hostel",
        "girl hostel",
        "boys hostel",
        "boys playground",
        "vedanta building",
        "musing building",
        "auditorium",
        "central garden",
        "central lawn",
        "sports ground",
        "sports field",
        "student hostel",
        "main entrance",
        "main gate",
        "first parking",
        "second parking",
        "playground",
        "library",
        "vedanta",
        "musing",
        "chanakya",
        "vivekananda",
        "vishwakarma",
        "garden",
        "lawn",
        "hostel",
        "gate",
        "मेडिकल सेंटर",
        "चिकित्सा केंद्र",
        "मुख्य द्वार",
        "पुस्तकालय",
        "खेल का मैदान",
        "लड़कियों का हॉस्टल",
        "लड़कों का हॉस्टल",
        "छात्रावास",
        "वेदांता",
        "चाणक्य",
        "विवेकानंद",
        "विश्वकर्मा",
        "गार्डन",
        "लाइब्रेरी",
        "हॉस्टल",
    )

    LOCATION_PATTERN = re.compile(
        r"\b(?:near|at|outside|inside|beside|opposite)\s+"
        r"(.+?)(?=[,.!?;]|$)",
        re.IGNORECASE,
    )

    HINGLISH_LOCATION_PATTERN = re.compile(
        r"(.+?)\s+(?:ke paas|ke pass|ke samne|ke saamne|"
        r"ke peeche|ke andar|mein|me|par)\b",
        re.IGNORECASE,
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
        """Identify the emergency category from keywords."""

        # An explicit accident or fire takes precedence over injury symptoms.
        for emergency_type in (
            EmergencyType.FIRE,
            EmergencyType.ACCIDENT,
            EmergencyType.SECURITY,
            EmergencyType.MEDICAL,
        ):
            for keyword in self.TYPE_KEYWORDS[emergency_type]:
                if keyword.casefold() in text:
                    return emergency_type

        return EmergencyType.OTHER

    def _detect_people_count(self, text: str) -> int:
        """Extract the number of affected people when stated."""

        number_words = "|".join(
            re.escape(word)
            for word in sorted(self.NUMBER_WORDS, key=len, reverse=True)
        )
        number = rf"(?:\d{{1,4}}|{number_words})"

        people_terms = (
            r"people|persons?|victims?|students?|workers?|"
            r"children|child|kids?|boys?|girls?|patients?|"
            r"baache|bacche|bachche|bachcha|bacha|"
            r"log|aadmi|aurat|vyakti|"
            r"बच्चे|बच्चों|बच्चा|बच्ची|लोग|व्यक्ति|छात्र|छात्रों"
        )

        patterns = (
            rf"(?<!\w)({number})\s+"
            rf"(?:of\s+)?(?:the\s+)?(?:injured\s+|affected\s+)?"
            rf"(?:{people_terms})(?!\w)",
            rf"(?<!\w)({number})\s+"
            rf"(?:injured|affected|hurt)\s+"
            rf"(?:people|persons?|students?|children|workers?)(?!\w)",
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

            if 1 <= count <= 1000:
                return count

        return 1


    def _detect_location(self, text: str) -> str | None:
        """Find a campus location while preserving useful location context."""

        normalized = text.casefold()

        # Preserve the existing API's expected wording for English reports.
        match = self.LOCATION_PATTERN.search(text)
        if match:
            return match.group(1).strip(" .,!?:;")

        # Recognize multiple explicitly named locations. Returning the full
        # phrase lets the repository reject ambiguous location descriptions.
        location_matches = []

        for alias in self.LOCATION_ALIASES:
            pattern = (
                r"(?<!\w)"
                + re.escape(alias.casefold())
                + r"(?!\w)"
            )
            for found in re.finditer(pattern, normalized):
                location_matches.append((found.start(), found.end(), alias))

        location_matches.sort(key=lambda item: item[0])

        # Deduplicate overlapping aliases such as "gate" and "main gate".
        distinct_locations = []
        for start, end, alias in location_matches:
            if any(
                start >= old_start and end <= old_end
                for old_start, old_end, _ in distinct_locations
            ):
                continue

            distinct_locations.append((start, end, alias))

        if len(distinct_locations) > 1:
            first = distinct_locations[0][0]
            last = distinct_locations[-1][1]
            return text[first:last].strip(" .,!?:;")

        if distinct_locations:
            start, end, alias = distinct_locations[0]
            original_phrase = text[start:end]

            # Keep articles where they occur in the user's report.
            prefix = text[:start]
            article = re.search(r"\b(the|a|an)\s+$", prefix, re.IGNORECASE)

            if article:
                return article.group(0) + original_phrase

            return original_phrase

        # Hinglish fallback: e.g. "Library ke paas accident hua".
        match = self.HINGLISH_LOCATION_PATTERN.search(text)
        if match:
            return match.group(1).strip(" .,!?:;")

        return None

