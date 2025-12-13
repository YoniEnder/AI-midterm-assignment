"""
Index Setup and Initialization
Creates Summary Index and Hierarchical Index from documents
Implements hierarchical structure: Claim → Document → Section → Chunk
"""

from llama_index.core import (
    VectorStoreIndex,
    SummaryIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.core.schema import Document
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from src.indexing.document_processor import HierarchicalDocumentProcessor
import chromadb
import os
import json
from pathlib import Path

# ChromaDB configuration
CHROMA_DB_PATH = "./chroma_db"


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
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        collection = chroma_client.get_collection(name=collection_name)
        if collection.count() > 0:
            print(
                f"  ✓ Using existing ChromaDB collection: {collection_name} ({collection.count()} vectors)"
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


def create_summary_index(
    documents: list[Document], collection_name: str = "summary_index"
) -> SummaryIndex:
    """
    Create a SummaryIndex using LlamaIndex's built-in summarization
    Uses ChromaDB for storage
    Uses large chunks with hierarchical metadata - summarization happens on-the-fly during queries
    """
    # Check if collection already exists and has data (before processing documents)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    try:
        collection = chroma_client.get_collection(name=collection_name)
        if collection.count() > 0:
            print(
                f"  ✓ Using existing ChromaDB collection: {collection_name} ({collection.count()} vectors)"
            )
            vector_store = ChromaVectorStore(chroma_collection=collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            index = SummaryIndex([], storage_context=storage_context)
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

    print(f"  Using {len(large_nodes)} large chunks for Summary Index")
    print("    (Small/medium chunks are in Hierarchical Index for precise queries)")
    print(
        f"  Hierarchy: {len(hierarchy_info['claims'])} claims, "
        f"{len(hierarchy_info['documents'])} documents, "
        f"{len(hierarchy_info['sections'])} sections"
    )

    if not large_nodes:
        print("  Warning: No large chunks found, using all chunks for Summary Index")
        large_nodes = nodes

    # Create new collection
    print("  Connecting to ChromaDB...")
    collection = chroma_client.create_collection(name=collection_name)
    print(f"  Created new ChromaDB collection: {collection_name}")

    # Create ChromaVectorStore
    vector_store = ChromaVectorStore(chroma_collection=collection)

    # Create Summary Index with large chunks
    # LlamaIndex's SummaryIndex will handle summarization automatically when queried
    # using tree_summarize response mode - no upfront API calls needed!
    print("\n  Creating Summary Index with LlamaIndex's built-in summarization...")
    print(
        "    Note: Summarization happens on-the-fly during queries (no upfront API calls)"
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = SummaryIndex(large_nodes, storage_context=storage_context)

    print("  ✓ Summary Index created and stored in ChromaDB")
    print(
        "    Summarization will be handled automatically by LlamaIndex during queries"
    )

    return index


def load_or_create_indexes(
    data_path: str = "./data",
) -> tuple[SummaryIndex, VectorStoreIndex]:
    """
    Load existing indexes from ChromaDB or create new ones from documents
    Returns: (summary_index, hierarchical_index)
    """
    setup_llm_settings()

    summary_collection_name = "summary_index"
    hierarchical_collection_name = "hierarchical_index"

    # Try to load existing indexes from ChromaDB
    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

        # Check if collections exist and have data
        try:
            summary_collection = chroma_client.get_collection(
                name=summary_collection_name
            )
            hierarchical_collection = chroma_client.get_collection(
                name=hierarchical_collection_name
            )

            # Check if collections have data
            if summary_collection.count() == 0 or hierarchical_collection.count() == 0:
                raise ValueError("Collections exist but are empty")

            # Create vector stores from existing collections
            summary_vector_store = ChromaVectorStore(
                chroma_collection=summary_collection
            )
            hierarchical_vector_store = ChromaVectorStore(
                chroma_collection=hierarchical_collection
            )

            # Create storage contexts
            summary_storage_context = StorageContext.from_defaults(
                vector_store=summary_vector_store
            )
            hierarchical_storage_context = StorageContext.from_defaults(
                vector_store=hierarchical_vector_store
            )

            # Reconstruct indexes from ChromaDB
            summary_index = SummaryIndex([], storage_context=summary_storage_context)
            hierarchical_index = VectorStoreIndex(
                [], storage_context=hierarchical_storage_context
            )

            print("✓ Loaded existing indexes from ChromaDB")
            print(f"  Summary Index: {summary_collection.count()} vectors")
            print(f"  Hierarchical Index: {hierarchical_collection.count()} vectors")
            return summary_index, hierarchical_index
        except ValueError as e:
            print(f"Collections don't exist or are empty: {e}")
            raise
        except Exception as e:
            print(f"Error loading collections: {e}")
            raise

    except Exception as e:
        print(f"Could not load existing indexes from ChromaDB: {e}")
        print("Creating new indexes from documents...")

    # Load documents
    reader = SimpleDirectoryReader(data_path, recursive=True)
    documents = reader.load_data()

    if not documents:
        raise ValueError(f"No documents found in {data_path}")

    print(f"Loaded {len(documents)} documents")

    # Create indexes
    print("\n" + "=" * 80)
    print("Creating Summary Index with ChromaDB storage...")
    print("=" * 80)
    summary_index = create_summary_index(documents, summary_collection_name)
    print("=" * 80)
    print("✓ Summary Index created and stored in ChromaDB")

    print("\n" + "=" * 80)
    print("Creating Hierarchical Index with ChromaDB storage...")
    print("=" * 80)
    hierarchical_index = create_hierarchical_index(
        documents, hierarchical_collection_name
    )
    print("=" * 80)
    print("✓ Hierarchical Index created and stored in ChromaDB")

    print("\n" + "=" * 80)
    print("✓ All indexes created and stored in ChromaDB successfully")
    print("=" * 80)
    return summary_index, hierarchical_index
