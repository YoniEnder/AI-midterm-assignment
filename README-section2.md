# README --- Section 2: Data Management & Indexing

## 1. Hierarchical Data Structure

The dataset is structured as:

    Claim → Document → Section → Chunk

This ensures: - Structured navigation - Preservation of relationships
between events, notes, and decisions - Support for both broad and narrow
retrieval

------------------------------------------------------------------------

## 2. Chunking Strategy

### Small Chunks (150--250 tokens)

-   High precision
-   Extract specific facts or "needle" details

### Medium Chunks (400--600 tokens)

-   Balanced reasoning
-   Capture multiple related events

### Large Chunks (800--1200 tokens)

-   High-level context
-   Useful for timeline reconstruction or summarization

### Overlap Strategy

Chunks include **15--20% overlap** to prevent loss of important details
and improve recall.

------------------------------------------------------------------------

## 3. Metadata Schema

Each chunk carries metadata such as: - `claim_id` - `document_type` -
`section` - `chunk_size` - `timestamp_range` - Optional page numbers or
entity tags

This enables targeted retrieval and higher accuracy.

------------------------------------------------------------------------

## 4. Summary Index (MapReduce Summarization)

### Map Phase

Each chunk is summarized individually.

### Reduce Phase

Summaries are merged into: - Section summaries - Document summaries -
Claim-level summaries

### Stored Elements

-   Timelines\
-   Entities\
-   Key decisions\
-   High-level reasoning

The Summary Index enables fast, efficient responses without loading full
documents.

------------------------------------------------------------------------

## 5. How Segmentation Improves Recall

-   Multi-size chunks allow precise → contextual → broad retrieval\
-   Overlap prevents detail loss\
-   Hierarchy maintains relationships between events\
-   Summary Index accelerates high-level queries

This design supports both high-precision fact retrieval and
large-context reasoning.
