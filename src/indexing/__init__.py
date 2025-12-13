"""
Indexing System
Document processing and index creation/loading
"""

from src.indexing.index_setup import (
    setup_llm_settings,
    create_hierarchical_index,
    create_summary_index,
    load_or_create_indexes,
)
from src.indexing.document_processor import (
    HierarchicalDocumentProcessor,
    ClaimMetadata,
)

__all__ = [
    "setup_llm_settings",
    "create_hierarchical_index",
    "create_summary_index",
    "load_or_create_indexes",
    "HierarchicalDocumentProcessor",
    "ClaimMetadata",
]
