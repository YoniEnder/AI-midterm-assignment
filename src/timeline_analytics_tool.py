"""
ClaimTimelineAnalyticsTool - MCP Tool for Timeline Analytics
Performs numerical and logical analysis over claim timelines
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import re


class ClaimTimelineAnalyticsTool:
    """
    MCP Tool that performs numerical and logical analysis over claim timelines.
    Provides functions for time differences, SLA checks, and timeline statistics.
    """

    def __init__(self, timeline_data_path: Optional[str] = None):
        """
        Initialize the timeline analytics tool
        
        Args:
            timeline_data_path: Path to JSON file containing timeline events.
                                If None, will try to load from default location or create empty.
        """
        self.timeline_data_path = timeline_data_path or "./storage/timeline_events.json"
        self.events = self._load_timeline_data()

    def _load_timeline_data(self) -> List[Dict[str, Any]]:
        """Load timeline events from JSON file"""
        timeline_path = Path(self.timeline_data_path)
        
        if timeline_path.exists():
            try:
                with open(timeline_path, "r") as f:
                    data = json.load(f)
                    return data.get("events", [])
            except Exception as e:
                print(f"Warning: Could not load timeline data: {e}")
                return []
        else:
            # Return empty list - events will be populated from document metadata
            return []

    def _save_timeline_data(self):
        """Save timeline events to JSON file"""
        timeline_path = Path(self.timeline_data_path)
        timeline_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(timeline_path, "w") as f:
            json.dump({"events": self.events}, f, indent=2, default=str)

    def _normalize_event_type(self, event_type: str) -> str:
        """Normalize event type to standard format"""
        # Map common variations to standard event types
        event_mapping = {
            "fnol": "FNOL_REPORTED",
            "first notice of loss": "FNOL_REPORTED",
            "claim filed": "FNOL_REPORTED",
            "claim reported": "FNOL_REPORTED",
            "adjuster contact": "FIRST_ADJUSTER_CONTACT",
            "adjuster inspection": "FIRST_ADJUSTER_CONTACT",
            "inspection": "INSPECTION_COMPLETED",
            "photos uploaded": "PHOTO_UPLOAD",
            "police report": "POLICE_REPORT_RECEIVED",
            "payment": "PAYMENT_ISSUED",
            "settlement": "SETTLEMENT_COMPLETED",
            "claim closed": "SETTLEMENT_COMPLETED",
        }
        
        event_lower = event_type.lower().strip()
        for key, value in event_mapping.items():
            if key in event_lower:
                return value
        
        # Return uppercase version if no mapping found
        return event_type.upper().replace(" ", "_")

    def _find_event(
        self, claim_id: str, event_type: str, occurrence: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Find a specific event by claim_id and event_type
        
        Args:
            claim_id: Claim identifier
            event_type: Type of event (will be normalized)
            occurrence: Which occurrence (0 = first, 1 = second, etc.)
        """
        normalized_type = self._normalize_event_type(event_type)
        
        matching_events = [
            e
            for e in self.events
            if e.get("claim_id") == claim_id
            and e.get("event_type") == normalized_type
        ]
        
        if occurrence < len(matching_events):
            return matching_events[occurrence]
        return None

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        # Try various formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        return None

    def _format_timedelta(self, delta: timedelta) -> str:
        """Format timedelta to human-readable string"""
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 and hours == 0:  # Only show seconds if less than an hour
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        return " ".join(parts) if parts else "0 seconds"

    def time_diff(
        self,
        claim_id: str,
        from_event_type: str,
        to_event_type: str,
        from_occurrence: int = 0,
        to_occurrence: int = 0,
    ) -> Dict[str, Any]:
        """
        Calculate time difference between two events
        
        Args:
            claim_id: Claim identifier
            from_event_type: Starting event type (e.g., "FNOL_REPORTED")
            to_event_type: Ending event type (e.g., "FIRST_ADJUSTER_CONTACT")
            from_occurrence: Which occurrence of from_event (default: 0 = first)
            to_occurrence: Which occurrence of to_event (default: 0 = first)
            
        Returns:
            Dictionary with time difference information
        """
        from_event = self._find_event(claim_id, from_event_type, from_occurrence)
        to_event = self._find_event(claim_id, to_event_type, to_occurrence)
        
        if not from_event:
            return {
                "error": f"Event '{from_event_type}' not found for claim {claim_id}",
                "from_event_ts": None,
                "to_event_ts": None,
                "diff_seconds": None,
                "diff_human_readable": None,
            }
        
        if not to_event:
            return {
                "error": f"Event '{to_event_type}' not found for claim {claim_id}",
                "from_event_ts": from_event.get("timestamp"),
                "to_event_ts": None,
                "diff_seconds": None,
                "diff_human_readable": None,
            }
        
        from_ts = self._parse_timestamp(from_event.get("timestamp", ""))
        to_ts = self._parse_timestamp(to_event.get("timestamp", ""))
        
        if not from_ts or not to_ts:
            return {
                "error": "Could not parse timestamps",
                "from_event_ts": from_event.get("timestamp"),
                "to_event_ts": to_event.get("timestamp"),
                "diff_seconds": None,
                "diff_human_readable": None,
            }
        
        diff = to_ts - from_ts
        diff_seconds = int(diff.total_seconds())
        
        return {
            "from_event_ts": from_event.get("timestamp"),
            "to_event_ts": to_event.get("timestamp"),
            "diff_seconds": diff_seconds,
            "diff_hours": round(diff_seconds / 3600, 2),
            "diff_human_readable": self._format_timedelta(diff),
        }

    def sla_check(
        self,
        claim_id: str,
        sla_hours: float,
        from_event_type: str,
        to_event_type: str,
    ) -> Dict[str, Any]:
        """
        Check if SLA was violated between two events
        
        Args:
            claim_id: Claim identifier
            sla_hours: SLA threshold in hours
            from_event_type: Starting event type
            to_event_type: Ending event type
            
        Returns:
            Dictionary with SLA check results
        """
        time_diff_result = self.time_diff(claim_id, from_event_type, to_event_type)
        
        if "error" in time_diff_result:
            return {
                **time_diff_result,
                "breach": None,
                "allowed_hours": sla_hours,
                "actual_hours": None,
            }
        
        actual_hours = time_diff_result.get("diff_hours", 0)
        breach = actual_hours > sla_hours
        
        details = ""
        if breach:
            excess_hours = actual_hours - sla_hours
            details = f"{to_event_type} happened {excess_hours:.1f} hours after SLA."
        else:
            remaining_hours = sla_hours - actual_hours
            details = f"{to_event_type} happened {remaining_hours:.1f} hours before SLA deadline."
        
        return {
            "breach": breach,
            "allowed_hours": sla_hours,
            "actual_hours": round(actual_hours, 2),
            "details": details,
            "from_event_ts": time_diff_result.get("from_event_ts"),
            "to_event_ts": time_diff_result.get("to_event_ts"),
        }

    def timeline_summary_stats(self, claim_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a claim timeline
        
        Args:
            claim_id: Claim identifier
            
        Returns:
            Dictionary with timeline statistics
        """
        claim_events = [
            e for e in self.events if e.get("claim_id") == claim_id
        ]
        
        if not claim_events:
            return {
                "error": f"No events found for claim {claim_id}",
                "total_duration_hours": None,
                "num_events": 0,
                "average_gap_hours": None,
                "longest_gap": None,
            }
        
        # Sort events by timestamp
        sorted_events = sorted(
            claim_events,
            key=lambda e: self._parse_timestamp(e.get("timestamp", "")) or datetime.min,
        )
        
        # Calculate gaps between consecutive events
        gaps = []
        for i in range(len(sorted_events) - 1):
            from_ts = self._parse_timestamp(sorted_events[i].get("timestamp", ""))
            to_ts = self._parse_timestamp(sorted_events[i + 1].get("timestamp", ""))
            
            if from_ts and to_ts:
                gap = (to_ts - from_ts).total_seconds() / 3600  # Convert to hours
                gaps.append(gap)
        
        # Calculate statistics
        total_duration_hours = None
        if len(sorted_events) >= 2:
            first_ts = self._parse_timestamp(sorted_events[0].get("timestamp", ""))
            last_ts = self._parse_timestamp(sorted_events[-1].get("timestamp", ""))
            if first_ts and last_ts:
                total_duration = (last_ts - first_ts).total_seconds() / 3600
                total_duration_hours = round(total_duration, 2)
        
        average_gap_hours = (
            round(sum(gaps) / len(gaps), 2) if gaps else None
        )
        
        # Find longest gap
        longest_gap = None
        if gaps:
            max_gap_idx = gaps.index(max(gaps))
            longest_gap = {
                "from_event": sorted_events[max_gap_idx].get("event_type"),
                "to_event": sorted_events[max_gap_idx + 1].get("event_type"),
                "gap_hours": round(gaps[max_gap_idx], 2),
            }
        
        return {
            "total_duration_hours": total_duration_hours,
            "num_events": len(claim_events),
            "average_gap_hours": average_gap_hours,
            "longest_gap": longest_gap,
        }

    def events_in_range(
        self,
        claim_id: str,
        from_timestamp: Optional[str] = None,
        to_timestamp: Optional[str] = None,
        from_event_type: Optional[str] = None,
        to_event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all events within a time range or between two event types
        
        Args:
            claim_id: Claim identifier
            from_timestamp: Start timestamp (ISO format)
            to_timestamp: End timestamp (ISO format)
            from_event_type: Start event type (alternative to from_timestamp)
            to_event_type: End event type (alternative to to_timestamp)
            
        Returns:
            List of events in the specified range
        """
        claim_events = [
            e for e in self.events if e.get("claim_id") == claim_id
        ]
        
        if not claim_events:
            return []
        
        # If event types are provided, find their timestamps
        if from_event_type:
            from_event = self._find_event(claim_id, from_event_type)
            if from_event:
                from_timestamp = from_event.get("timestamp")
        
        if to_event_type:
            to_event = self._find_event(claim_id, to_event_type)
            if to_event:
                to_timestamp = to_event.get("timestamp")
        
        # Filter events by timestamp range
        filtered_events = []
        for event in claim_events:
            event_ts = self._parse_timestamp(event.get("timestamp", ""))
            if not event_ts:
                continue
            
            if from_timestamp:
                from_ts = self._parse_timestamp(from_timestamp)
                if from_ts and event_ts < from_ts:
                    continue
            
            if to_timestamp:
                to_ts = self._parse_timestamp(to_timestamp)
                if to_ts and event_ts > to_ts:
                    continue
            
            filtered_events.append(event)
        
        # Sort by timestamp
        filtered_events.sort(
            key=lambda e: self._parse_timestamp(e.get("timestamp", "")) or datetime.min
        )
        
        return filtered_events

    def add_event(
        self,
        claim_id: str,
        event_type: str,
        timestamp: str,
        actor: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add a new event to the timeline
        
        Args:
            claim_id: Claim identifier
            event_type: Type of event
            timestamp: Event timestamp (ISO format)
            actor: Who performed the action (optional)
            metadata: Additional metadata (optional)
        """
        normalized_type = self._normalize_event_type(event_type)
        
        event = {
            "claim_id": claim_id,
            "event_id": f"E{len(self.events) + 1}",
            "event_type": normalized_type,
            "timestamp": timestamp,
            "actor": actor,
            "metadata": metadata or {},
        }
        
        self.events.append(event)
        self._save_timeline_data()

