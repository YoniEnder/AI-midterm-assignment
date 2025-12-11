"""
Timeline Event Extractor
Extracts structured timeline events from claim documents for use with ClaimTimelineAnalyticsTool
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from llama_index.core.schema import Document, TextNode
from llama_index.core import VectorStoreIndex
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
import re
import json
from pathlib import Path


def extract_timeline_events_from_index(
    hierarchical_index: VectorStoreIndex, claim_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extract timeline events from the hierarchical index by querying for date/time information
    
    Args:
        hierarchical_index: The hierarchical vector store index
        claim_id: Optional claim ID to filter events
        
    Returns:
        List of timeline events
    """
    events = []
    
    # Query for timeline-related information
    query_engine = hierarchical_index.as_query_engine(
        llm=Settings.llm or OpenAI(temperature=0, model="gpt-4"),
        similarity_top_k=50,  # Get many nodes to find all events
    )
    
    # Query for events and dates
    query = "Extract all events, dates, and timestamps mentioned in the documents. Include claim filing, inspections, payments, and other key milestones."
    
    try:
        response = query_engine.query(query)
        response_text = str(response)
        
        # Use LLM to extract structured events from the response
        extraction_prompt = f"""Extract all timeline events from the following text and return them as a structured JSON list.

Text:
{response_text}

For each event, extract:
- claim_id: Claim identifier (e.g., "01", "02", or "CLM-2025-1001")
- event_type: Type of event (use standard types like FNOL_REPORTED, FIRST_ADJUSTER_CONTACT, INSPECTION_COMPLETED, PHOTO_UPLOAD, POLICE_REPORT_RECEIVED, PAYMENT_ISSUED, SETTLEMENT_COMPLETED)
- timestamp: Date and time in ISO format (YYYY-MM-DDTHH:MM:SS) or just date (YYYY-MM-DD) if time not available
- actor: Who performed the action (e.g., "policyholder", "adjuster", "system")
- metadata: Any additional information

Return ONLY a valid JSON array of events. If no events found, return empty array []."""

        llm = Settings.llm or OpenAI(temperature=0, model="gpt-4")
        extraction_response = llm.complete(extraction_prompt)
        extraction_text = extraction_response.text.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', extraction_text, re.DOTALL)
        if json_match:
            events_json = json.loads(json_match.group(0))
            events.extend(events_json)
        
    except Exception as e:
        print(f"Warning: Could not extract timeline events: {e}")
    
    # Also extract from node metadata
    try:
        retriever = hierarchical_index.as_retriever(similarity_top_k=100)
        nodes = retriever.retrieve("timeline events dates timestamps")
        
        for node in nodes:
            metadata = node.metadata or {}
            claim_id_from_meta = metadata.get("claim_id")
            timestamp_range = metadata.get("timestamp_range")
            
            if claim_id_from_meta and timestamp_range:
                # Try to parse timestamp range
                if " to " in timestamp_range:
                    dates = timestamp_range.split(" to ")
                    if len(dates) == 2:
                        # Create events for start and end
                        events.append({
                            "claim_id": claim_id_from_meta,
                            "event_type": "DOCUMENT_START",
                            "timestamp": dates[0].strip(),
                            "actor": "system",
                            "metadata": {"source": "metadata", "section": metadata.get("section")}
                        })
                        events.append({
                            "claim_id": claim_id_from_meta,
                            "event_type": "DOCUMENT_END",
                            "timestamp": dates[1].strip(),
                            "actor": "system",
                            "metadata": {"source": "metadata", "section": metadata.get("section")}
                        })
                else:
                    # Single date
                    events.append({
                        "claim_id": claim_id_from_meta,
                        "event_type": "DOCUMENT_DATE",
                        "timestamp": timestamp_range.strip(),
                        "actor": "system",
                        "metadata": {"source": "metadata", "section": metadata.get("section")}
                    })
    except Exception as e:
        print(f"Warning: Could not extract events from metadata: {e}")
    
    # Filter by claim_id if provided
    if claim_id:
        events = [e for e in events if e.get("claim_id") == claim_id]
    
    return events


def populate_timeline_from_documents(
    hierarchical_index: VectorStoreIndex,
    timeline_tool,
    claim_ids: Optional[List[str]] = None,
):
    """
    Populate timeline tool with events extracted from documents
    
    Args:
        hierarchical_index: The hierarchical vector store index
        timeline_tool: ClaimTimelineAnalyticsTool instance
        claim_ids: Optional list of claim IDs to process
    """
    print("Extracting timeline events from documents...")
    
    # Extract events from index
    all_events = extract_timeline_events_from_index(hierarchical_index)
    
    # Add events to timeline tool
    for event in all_events:
        timeline_tool.add_event(
            claim_id=event.get("claim_id", "unknown"),
            event_type=event.get("event_type", "UNKNOWN_EVENT"),
            timestamp=event.get("timestamp", ""),
            actor=event.get("actor"),
            metadata=event.get("metadata", {}),
        )
    
    print(f"Added {len(all_events)} timeline events to ClaimTimelineAnalyticsTool")

