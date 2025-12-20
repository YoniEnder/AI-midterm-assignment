"""
Index Setup and Initialization
Creates Summary Index and Hierarchical Index from documents
Implements hierarchical structure: Claim → Document → Section → Chunk
"""

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.core.schema import Document, TextNode
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from src.indexing.document_processor import HierarchicalDocumentProcessor
import chromadb
import os
import json
from pathlib import Path

# ChromaDB configuration - use absolute path for persistence
# Get project root (two levels up from this file: src/indexing/index_setup.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHROMA_DB_PATH = str(PROJECT_ROOT / "chroma_db")

# Ensure the directory exists
Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)

# Centralized ChromaDB client for persistence across sessions
_chroma_client = None


def get_chroma_client():
    """
    Get or create a persistent ChromaDB client.
    This ensures the same client is reused across all operations,
    maintaining persistence between sessions.
    """
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client


def setup_llm_settings():
    """Configure LLM and embedding settings"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    indexing_model = os.getenv("INDEXING_MODEL", "gpt-4o-mini")
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    Settings.llm = OpenAI(temperature=0, model=indexing_model, api_key=api_key)
    # OpenAIEmbedding uses 'model_name' parameter, not 'model'
    Settings.embed_model = OpenAIEmbedding(model_name=embedding_model, api_key=api_key)


def create_hierarchical_index(
    documents: list[Document], collection_name: str = "hierarchical_index"
) -> VectorStoreIndex:
    """
    Create a hierarchical VectorStoreIndex optimized for precise retrieval
    Uses ChromaDB for vector storage
    Implements multi-size chunking with metadata:
    - Small chunks (150-250 tokens): High precision
    - Medium chunks (400-600 tokens): Balanced reasoning
    - Large chunks (800-1200 tokens): High-level context
    """
    # Check if collection already exists and has data (before processing documents)
    chroma_client = get_chroma_client()
    try:
        collection = chroma_client.get_collection(name=collection_name)
        count = collection.count()
        if count > 0:
            print(
                f"  ✓ Using existing ChromaDB collection: {collection_name} ({count} vectors)"
            )
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex([], storage_context=storage_context)
            print("  ✓ Using existing Hierarchical Index from ChromaDB")
            return index
        else:
            print(
                f"  Collection {collection_name} exists but is empty, will recreate..."
            )
            chroma_client.delete_collection(name=collection_name)
    except Exception:
        # Collection doesn't exist, will create it
        pass

    print("  Processing documents with hierarchical structure...")
    processor = HierarchicalDocumentProcessor(llm=Settings.llm)

    # Process documents to extract hierarchy and metadata
    print(f"  Processing {len(documents)} documents...")
    nodes, hierarchy_info = processor.process_documents(documents)

    if not nodes:
        raise ValueError(
            "No chunks were created from documents. Check if documents contain text."
        )

    print(f"  Created {len(nodes)} nodes with multi-size chunking")
    print(
        f"  Hierarchy: {len(hierarchy_info['claims'])} claims, "
        f"{len(hierarchy_info['documents'])} documents, "
        f"{len(hierarchy_info['sections'])} sections"
    )

    # Save hierarchy info to JSON (metadata, not vector data)
    hierarchy_path = Path("./storage") / "hierarchy_info.json"
    hierarchy_path.parent.mkdir(parents=True, exist_ok=True)
    with open(hierarchy_path, "w") as f:
        # Convert sets to lists for JSON serialization
        json_hierarchy = {
            "claims": {
                k: {
                    "documents": v["documents"],
                    "document_types": list(v["document_types"]),
                }
                for k, v in hierarchy_info["claims"].items()
            },
            "documents": hierarchy_info["documents"],
            "sections": hierarchy_info["sections"],
        }
        json.dump(json_hierarchy, f, indent=2)

    # Create new collection
    collection = chroma_client.create_collection(name=collection_name)
    print(f"  Created new ChromaDB collection: {collection_name}")

    # Create ChromaVectorStore
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Create vector store index with ChromaDB
    print(f"  Creating VectorStoreIndex with {len(nodes)} nodes in ChromaDB...")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes, storage_context=storage_context)

    print("  ✓ Hierarchical Index created and stored in ChromaDB")

    return index


def _generate_summary_for_chunks(chunks: list[TextNode], llm) -> str:
    """
    Generate a summary for a group of chunks using LLM
    """
    # Combine all chunk texts
    combined_text = "\n\n".join([chunk.text for chunk in chunks])

    # Get metadata from first chunk (they should all have similar metadata)
    metadata = chunks[0].metadata if chunks else {}
    claim_id = metadata.get("claim_id", "Unknown")
    doc_type = metadata.get("document_type", "Unknown")
    section = metadata.get("section", "Unknown")

    prompt = f"""Summarize the following insurance claim document content. 
Focus on key decisions, outcomes, timeline, and important details.

Claim ID: {claim_id}
Document Type: {doc_type}
Section: {section}

Document Content:
{combined_text}

Provide a comprehensive summary that captures:
- Key decisions and outcomes
- Important timeline information
- Significant details and entities
- Any discrepancies or notable patterns

Summary:"""

    try:
        response = llm.complete(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"    Warning: Summary generation failed: {e}")
        # Fallback: return first 500 chars of combined text
        return (
            combined_text[:500] + "..." if len(combined_text) > 500 else combined_text
        )


def create_summary_index(
    documents: list[Document], collection_name: str = "summary_index"
) -> VectorStoreIndex:
    """
    Create a VectorStoreIndex with pre-computed summary chunks
    Uses ChromaDB for storage with proper persistence
    Generates summaries during indexing for better query performance
    """
    # Check if collection already exists and has data (before processing documents)
    chroma_client = get_chroma_client()
    try:
        collection = chroma_client.get_collection(name=collection_name)
        count = collection.count()
        if count > 0:
            print(
                f"  ✓ Using existing ChromaDB collection: {collection_name} ({count} vectors)"
            )
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = VectorStoreIndex([], storage_context=storage_context)
            print("  ✓ Using existing Summary Index from ChromaDB")
            return index
        else:
            print(
                f"  Collection {collection_name} exists but is empty, will recreate..."
            )
            chroma_client.delete_collection(name=collection_name)
    except Exception:
        # Collection doesn't exist, will create it
        pass

    print("  Processing documents for Summary Index...")
    processor = HierarchicalDocumentProcessor(llm=Settings.llm)

    # Process documents to get nodes with metadata
    print(f"  Processing {len(documents)} documents...")
    nodes, hierarchy_info = processor.process_documents(documents)

    if not nodes:
        raise ValueError(
            "No chunks were created from documents. Check if documents contain text."
        )

    print(f"  Created {len(nodes)} total chunks with multi-size chunking")

    # Use only large chunks for Summary Index (they have enough context for summarization)
    # Small/medium chunks are used in Hierarchical Index for precise queries
    large_nodes = [n for n in nodes if n.metadata.get("chunk_size") == "large"]

    print(f"  Using {len(large_nodes)} large chunks to generate summaries")
    print("    (Small/medium chunks are in Hierarchical Index for precise queries)")
    print(
        f"  Hierarchy: {len(hierarchy_info['claims'])} claims, "
        f"{len(hierarchy_info['documents'])} documents, "
        f"{len(hierarchy_info['sections'])} sections"
    )

    if not large_nodes:
        print("  Warning: No large chunks found, using all chunks for Summary Index")
        large_nodes = nodes

    # Group chunks by document (filename) to create summaries per document
    # This ensures each document gets a summary chunk
    chunks_by_document = {}
    for node in large_nodes:
        filename = node.metadata.get("filename", "unknown")
        if filename not in chunks_by_document:
            chunks_by_document[filename] = []
        chunks_by_document[filename].append(node)

    print(
        f"\n  Generating pre-computed summaries for {len(chunks_by_document)} documents..."
    )

    # Use a summarization model (can be different from indexing model)
    summarization_model = os.getenv("SUMMARIZATION_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    summary_llm = OpenAI(temperature=0.3, model=summarization_model, api_key=api_key)

    summary_nodes = []
    for i, (filename, doc_chunks) in enumerate(chunks_by_document.items(), 1):
        print(f"    Generating summary {i}/{len(chunks_by_document)}: {filename}...")

        # Generate summary for this document's chunks
        summary_text = _generate_summary_for_chunks(doc_chunks, summary_llm)

        # Create a summary node with metadata from the original chunks
        # Use metadata from the first chunk (they should all be from the same document)
        base_metadata = doc_chunks[0].metadata.copy()
        base_metadata["is_summary"] = True
        base_metadata["source_chunks"] = len(doc_chunks)

        summary_node = TextNode(text=summary_text, metadata=base_metadata)
        summary_nodes.append(summary_node)

    print(f"  Generated {len(summary_nodes)} pre-computed summary chunks")

    # Create new collection
    print("  Connecting to ChromaDB...")
    collection = chroma_client.create_collection(name=collection_name)
    print(f"  Created new ChromaDB collection: {collection_name}")

    # Create ChromaVectorStore
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Create VectorStoreIndex with pre-computed summary chunks
    print("\n  Creating Summary Index with pre-computed summaries in ChromaDB...")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(summary_nodes, storage_context=storage_context)

    # Verify that data was persisted to ChromaDB
    final_count = collection.count()
    print(
        f"  ✓ Summary Index created and stored in ChromaDB ({final_count} summary chunks)"
    )
    print("    Summaries are pre-computed and ready for querying")

    return index


def load_or_create_indexes(
    data_path: str = "./data",
) -> tuple[VectorStoreIndex, VectorStoreIndex]:
    """
    Load existing indexes from ChromaDB or create new ones from documents
    Returns: (summary_index, hierarchical_index)
    """
    setup_llm_settings()

    summary_collection_name = "summary_index"
    hierarchical_collection_name = "hierarchical_index"

    # Try to load existing indexes from ChromaDB
    chroma_client = get_chroma_client()

    summary_index = None
    hierarchical_index = None
    need_documents = False

    # Check Summary Index
    try:
        summary_collection = chroma_client.get_collection(name=summary_collection_name)
        summary_count = summary_collection.count()
        if summary_count > 0:
            print(f"✓ Found existing Summary Index with {summary_count} vectors")
            summary_vector_store = ChromaVectorStore(
                chroma_collection=summary_collection
            )
            summary_storage_context = StorageContext.from_defaults(
                vector_store=summary_vector_store
            )
            summary_index = VectorStoreIndex(
                [], storage_context=summary_storage_context
            )
        else:
            print(
                f"Summary Index exists but is empty ({summary_count} vectors), will recreate"
            )
            need_documents = True
            try:
                chroma_client.delete_collection(name=summary_collection_name)
            except Exception:
                pass
    except Exception:
        print("Summary Index doesn't exist, will create")
        need_documents = True

    # Check Hierarchical Index
    try:
        hierarchical_collection = chroma_client.get_collection(
            name=hierarchical_collection_name
        )
        hierarchical_count = hierarchical_collection.count()
        if hierarchical_count > 0:
            print(
                f"✓ Found existing Hierarchical Index with {hierarchical_count} vectors"
            )
            hierarchical_vector_store = ChromaVectorStore(
                chroma_collection=hierarchical_collection
            )
            hierarchical_storage_context = StorageContext.from_defaults(
                vector_store=hierarchical_vector_store
            )
            hierarchical_index = VectorStoreIndex(
                [], storage_context=hierarchical_storage_context
            )
        else:
            print(
                f"Hierarchical Index exists but is empty ({hierarchical_count} vectors), will recreate"
            )
            need_documents = True
            try:
                chroma_client.delete_collection(name=hierarchical_collection_name)
            except Exception:
                pass
    except Exception:
        print("Hierarchical Index doesn't exist, will create")
        need_documents = True

    # If both indexes exist and have data, return them
    if summary_index is not None and hierarchical_index is not None:
        print("\n✓ Loaded both existing indexes from ChromaDB")
        return summary_index, hierarchical_index

    # If we need to create any indexes, load documents
    if need_documents:
        print("\nLoading documents...")
        reader = SimpleDirectoryReader(data_path, recursive=True)
        documents = reader.load_data()

        if not documents:
            raise ValueError(f"No documents found in {data_path}")

        print(f"Loaded {len(documents)} documents")

    # Create missing indexes
    if summary_index is None:
        print("\n" + "=" * 80)
        print("Creating Summary Index with ChromaDB storage...")
        print("=" * 80)
        summary_index = create_summary_index(documents, summary_collection_name)
        print("=" * 80)
        print("✓ Summary Index created and stored in ChromaDB")
    else:
        print("\n✓ Using existing Summary Index (skipping creation)")

    if hierarchical_index is None:
        print("\n" + "=" * 80)
        print("Creating Hierarchical Index with ChromaDB storage...")
        print("=" * 80)
        hierarchical_index = create_hierarchical_index(
            documents, hierarchical_collection_name
        )
        print("=" * 80)
        print("✓ Hierarchical Index created and stored in ChromaDB")
    else:
        print("\n✓ Using existing Hierarchical Index (skipping creation)")

    print("\n" + "=" * 80)
    print("✓ All indexes ready")
    print("=" * 80)
    return summary_index, hierarchical_index
