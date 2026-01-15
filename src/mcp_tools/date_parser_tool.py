"""
DateParserTool - MCP Tool for Date Parsing and Normalization
Uses python-dateutil to parse dates from various formats found in insurance claim documents
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import re
from dateutil import parser as date_parser


class DateParserTool:
    """
    MCP Tool that parses and normalizes dates from various formats.
    Uses python-dateutil's parser to handle multiple date formats automatically.
    """

    def __init__(self):
        """Initialize the date parser tool"""
        # Tracks whether this tool instance was used during the current query.
        # Callers should reset via `reset_usage()` at the start of each query.
        self.used: bool = False

    def reset_usage(self) -> None:
        """Reset usage tracking (should be called once per user query)."""
        self.used = False

    def _mark_used(self) -> None:
        """Mark this tool as used."""
        self.used = True

    def parse_date(self, date_string: str) -> Optional[datetime]:
        """
        Parse a date string into a datetime object

        Args:
            date_string: Date string in any format (e.g., "2024-01-15", "January 15, 2024", "15/01/2024")

        Returns:
            datetime object if parsing successful, None otherwise
        """
        self._mark_used()
        if not date_string or not date_string.strip():
            return None

        try:
            # Use dateutil's parser which handles many formats automatically
            parsed_date = date_parser.parse(date_string, fuzzy=False)
            return parsed_date
        except (ValueError, TypeError, OverflowError) as e:
            print(f"Warning: Could not parse date '{date_string}': {e}")
            return None

    def normalize_date(
        self, date_string: str, output_format: str = "iso"
    ) -> Optional[str]:
        """
        Normalize a date string to a standard format

        Args:
            date_string: Date string in any format
            output_format: Output format ("iso", "us", "european", "readable")
                - "iso": ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
                - "us": US format (MM/DD/YYYY)
                - "european": European format (DD/MM/YYYY)
                - "readable": Human-readable (January 15, 2024)

        Returns:
            Normalized date string, or None if parsing failed
        """
        self._mark_used()
        parsed_date = self.parse_date(date_string)
        if not parsed_date:
            return None

        if output_format == "iso":
            return parsed_date.isoformat()
        elif output_format == "us":
            return parsed_date.strftime("%m/%d/%Y")
        elif output_format == "european":
            return parsed_date.strftime("%d/%m/%Y")
        elif output_format == "readable":
            return parsed_date.strftime("%B %d, %Y")
        else:
            # Default to ISO
            return parsed_date.isoformat()

    def extract_dates_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all date-like strings from text

        Args:
            text: Text to search for dates

        Returns:
            List of dictionaries with parsed date information:
            [
                {"original": "Jan 15, 2024", "parsed": datetime(2024, 1, 15), "normalized": "2024-01-15T00:00:00"},
                ...
            ]
        """
        self._mark_used()
        if not text:
            return []

        dates_found = []

        # Common date patterns to look for
        date_patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # MM/DD/YYYY or DD/MM/YYYY
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",  # YYYY-MM-DD
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",  # January 15, 2024
            r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b",  # 15 January 2024
            r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",  # Monday, January 15, 2024
        ]

        # Find all potential date strings
        potential_dates = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                potential_dates.append(match.group(0))

        # Also try fuzzy parsing on the entire text (dateutil can find dates in context)
        try:
            # dateutil's fuzzy parsing can find dates in text
            parsed_info = date_parser.parse(
                text, fuzzy=True, default=datetime(1900, 1, 1)
            )
            if parsed_info:
                # Extract the date part from the parsed result
                date_str = parsed_info.strftime("%Y-%m-%d")
                if date_str not in [d.get("normalized", "")[:10] for d in dates_found]:
                    dates_found.append(
                        {
                            "original": text[:50] + "..." if len(text) > 50 else text,
                            "parsed": parsed_info,
                            "normalized": parsed_info.isoformat(),
                        }
                    )
        except (ValueError, TypeError):
            pass

        # Parse each found date string
        for date_str in potential_dates:
            parsed_date = self.parse_date(date_str)
            if parsed_date:
                # Check if we already have this date
                normalized = parsed_date.isoformat()
                if not any(d.get("normalized") == normalized for d in dates_found):
                    dates_found.append(
                        {
                            "original": date_str,
                            "parsed": parsed_date,
                            "normalized": normalized,
                        }
                    )

        return dates_found

    def format_date(self, date_obj: datetime, format: str = "iso") -> str:
        """
        Format a datetime object to a string

        Args:
            date_obj: datetime object to format
            format: Output format ("iso", "us", "european", "readable")

        Returns:
            Formatted date string
        """
        self._mark_used()
        if not isinstance(date_obj, datetime):
            return str(date_obj)

        if format == "iso":
            return date_obj.isoformat()
        elif format == "us":
            return date_obj.strftime("%m/%d/%Y")
        elif format == "european":
            return date_obj.strftime("%d/%m/%Y")
        elif format == "readable":
            return date_obj.strftime("%B %d, %Y")
        else:
            return date_obj.isoformat()

    def calculate_date_difference(
        self, date1_str: str, date2_str: str, unit: str = "days"
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate the difference between two dates

        Args:
            date1_str: First date string
            date2_str: Second date string
            unit: Unit for difference ("days", "hours", "minutes", "seconds")

        Returns:
            Dictionary with difference information, or None if parsing failed
        """
        self._mark_used()
        date1 = self.parse_date(date1_str)
        date2 = self.parse_date(date2_str)

        if not date1 or not date2:
            return None

        diff = date2 - date1
        total_seconds = int(diff.total_seconds())

        result = {
            "date1": date1.isoformat(),
            "date2": date2.isoformat(),
            "difference_seconds": total_seconds,
            "difference_days": diff.days,
            "difference_hours": round(total_seconds / 3600, 2),
            "difference_minutes": round(total_seconds / 60, 2),
        }

        # Add human-readable format
        if diff.days > 0:
            result["human_readable"] = f"{diff.days} day{'s' if diff.days != 1 else ''}"
        elif total_seconds >= 3600:
            hours = total_seconds // 3600
            result["human_readable"] = f"{hours} hour{'s' if hours != 1 else ''}"
        elif total_seconds >= 60:
            minutes = total_seconds // 60
            result["human_readable"] = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            result["human_readable"] = (
                f"{total_seconds} second{'s' if total_seconds != 1 else ''}"
            )

        return result
