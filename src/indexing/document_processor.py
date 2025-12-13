"""
Document Processor for Hierarchical Structure
Implements Claim → Document → Section → Chunk hierarchy with metadata extraction
"""

import re
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from llama_index.core.schema import Document, TextNode
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from pydantic import BaseModel, Field
import tiktoken
import json
from dotenv import load_dotenv

load_dotenv()


class ClaimMetadata(BaseModel):
    """Structured metadata extracted from insurance claim documents"""

    claim_id: Optional[str] = Field(
        None,
        description="Claim identifier (e.g., '01', '02', 'Claim Document 01', or full claim ID)",
    )
    document_type: Optional[str] = Field(
        None,
        description="Type of insurance claim: Auto Collision, Health, Property Damage, Fire, Travel, Life Insurance, or other",
    )
    section: Optional[str] = Field(
        None, description="Main section or header name in the document"
    )
    timestamp_range: Optional[str] = Field(
        None,
        description="Date range in format 'YYYY-MM-DD to YYYY-MM-DD' or single important date",
    )
    page_numbers: Optional[str] = Field(
        None, description="Page numbers if mentioned in the document"
    )


class HierarchicalDocumentProcessor:
    """
    Processes documents to extract hierarchical structure:
    Claim → Document → Section → Chunk
    Uses LLM for intelligent metadata extraction
    """

    def __init__(self, llm: Optional[LLM] = None):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        if llm is None:
            llm = Settings.llm
        if llm is None:
            metadata_model = os.getenv("METADATA_EXTRACTION_MODEL", "gpt-4o-mini")
            llm = OpenAI(temperature=0, model=metadata_model)
        self.llm = llm

    def extract_metadata_from_text(self, text: str, filename: str) -> Dict:
        """
        Extract metadata from document text using LLM with structured output
        Returns: dict with claim_id, document_type, section, timestamp_range
        """
        # Truncate text if too long (to save tokens)
        text_sample = text[:5000] if len(text) > 5000 else text

        prompt = f"""Extract structured metadata from the following insurance claim document.

Document Filename: {filename}

Document Text:
{text_sample}

Extract the following information:
1. claim_id: The claim number or identifier. Look for patterns like:
   - "Claim Document 01", "Claim Document 02", etc.
   - "Claim 01", "Claim 02"
   - "Claim ID: XXX" or "Claim Number: XXX"
   Extract just the number or identifier (e.g., "01", "02", or full ID if available)

2. document_type: Type of insurance claim. Common types:
   - "Auto Collision" (for auto accidents)
   - "Health" (for medical/health claims)
   - "Property Damage" (for water damage, storm damage, etc.)
   - "Fire" (for fire-related claims)
   - "Travel" (for travel insurance claims)
   - "Life Insurance" (for life insurance claims)
   If the type is unclear, use the most specific category that fits.

3. section: The main section or header name in the document (e.g., "CLAIM SUMMARY", "INCIDENT REPORT", etc.)

4. timestamp_range: Important dates mentioned in the document. Format as:
   - "YYYY-MM-DD to YYYY-MM-DD" if there's a date range
   - "YYYY-MM-DD" if there's a single important date
   - None if no dates are found

5. page_numbers: Any page numbers referenced in the document (e.g., "Page 1-5" or "p. 3")

Return the extracted metadata in the structured format."""

        try:
            # Try to use structured output if available (OpenAI models support this)
            if hasattr(self.llm, "structured_predict"):
                # Use LlamaIndex's structured output
                response = self.llm.structured_predict(
                    output_cls=ClaimMetadata, prompt=prompt
                )
                metadata = (
                    response.model_dump()
                    if hasattr(response, "model_dump")
                    else response.dict()
                )
            else:
                # Fallback to JSON mode parsing (works with all LLMs)
                metadata = self._extract_with_json_mode(prompt)

            metadata["filename"] = filename
            return metadata

        except Exception as e:
            print(f"    Warning: LLM metadata extraction failed for {filename}: {e}")
            print("    Falling back to basic metadata extraction")
            # Fallback to basic extraction
            return self._extract_metadata_fallback(text, filename)

    def _extract_with_json_mode(self, prompt: str) -> Dict:
        """
        Extract metadata using JSON mode (fallback method)
        Uses LLM completion with JSON response format
        """
        json_prompt = (
            prompt
            + '\n\nReturn ONLY a valid JSON object with this exact structure (use null for missing values):\n{\n  "claim_id": "string or null",\n  "document_type": "string or null",\n  "section": "string or null",\n  "timestamp_range": "string or null",\n  "page_numbers": "string or null"\n}'
        )

        response_text = self.llm.complete(json_prompt).text
        json_str = self._extract_json_from_text(response_text)

        if not json_str:
            return self._empty_metadata()

        try:
            parsed = json.loads(json_str)
            response = ClaimMetadata(**parsed)
            return (
                response.model_dump()
                if hasattr(response, "model_dump")
                else response.dict()
            )
        except (TypeError, ValueError):
            return self._empty_metadata()

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON string from LLM response text"""
        json_str = text.strip()

        # Remove markdown code blocks if present
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        # Find JSON object boundaries
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            return json_str[start_idx:end_idx]

        return ""

    def _empty_metadata(self) -> Dict:
        """Return empty metadata structure"""
        return {
            "claim_id": None,
            "document_type": None,
            "section": None,
            "timestamp_range": None,
            "page_numbers": None,
        }

    def _extract_metadata_fallback(self, text: str, filename: str) -> Dict:
        """
        Fallback metadata extraction using simple patterns
        Used when LLM extraction fails
        """
        metadata = {
            "claim_id": None,
            "document_type": None,
            "section": None,
            "timestamp_range": None,
            "page_numbers": None,
            "filename": filename,
        }

        # Simple claim ID extraction
        claim_match = re.search(r"Claim\s+Document\s+(\d+)", text, re.IGNORECASE)
        if claim_match:
            metadata["claim_id"] = claim_match.group(1)

        # Simple document type from filename
        if "collision" in filename.lower() or "auto" in filename.lower():
            metadata["document_type"] = "Auto Collision"
        elif "health" in filename.lower() or "medical" in filename.lower():
            metadata["document_type"] = "Health"
        elif "water" in filename.lower() or "damage" in filename.lower():
            metadata["document_type"] = "Property Damage"
        elif "fire" in filename.lower():
            metadata["document_type"] = "Fire"
        elif "travel" in filename.lower():
            metadata["document_type"] = "Travel"
        elif "life" in filename.lower():
            metadata["document_type"] = "Life Insurance"

        return metadata

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def create_multi_size_chunks(
        self, text: str, base_metadata: Dict
    ) -> List[TextNode]:
        """
        Create chunks of multiple sizes:
        - Small (150-250 tokens): High precision
        - Medium (400-600 tokens): Balanced reasoning
        - Large (800-1200 tokens): High-level context
        """
        all_nodes = []

        # Validate input text
        if not text or not text.strip():
            return all_nodes

        # Small chunks (150-250 tokens) - 20% overlap
        small_parser = SimpleNodeParser.from_defaults(
            chunk_size=200,
            chunk_overlap=40,  # 20% of 200
        )
        small_nodes = small_parser.get_nodes_from_documents([Document(text=text)])
        for node in small_nodes:
            # Only add nodes with actual text content
            if node.text and node.text.strip():
                node.metadata = {
                    **base_metadata,
                    "chunk_size": "small",
                    "chunk_tokens": self.count_tokens(node.text),
                }
                all_nodes.append(node)

        # Medium chunks (400-600 tokens) - 18% overlap
        medium_parser = SimpleNodeParser.from_defaults(
            chunk_size=500,
            chunk_overlap=90,  # ~18% of 500
        )
        medium_nodes = medium_parser.get_nodes_from_documents([Document(text=text)])
        for node in medium_nodes:
            # Only add nodes with actual text content
            if node.text and node.text.strip():
                node.metadata = {
                    **base_metadata,
                    "chunk_size": "medium",
                    "chunk_tokens": self.count_tokens(node.text),
                }
                all_nodes.append(node)

        # Large chunks (800-1200 tokens) - 15% overlap
        large_parser = SimpleNodeParser.from_defaults(
            chunk_size=1000,
            chunk_overlap=150,  # 15% of 1000
        )
        large_nodes = large_parser.get_nodes_from_documents([Document(text=text)])
        for node in large_nodes:
            # Only add nodes with actual text content
            if node.text and node.text.strip():
                node.metadata = {
                    **base_metadata,
                    "chunk_size": "large",
                    "chunk_tokens": self.count_tokens(node.text),
                }
                all_nodes.append(node)

        return all_nodes

    def process_documents(
        self, documents: List[Document]
    ) -> Tuple[List[TextNode], Dict]:
        """
        Process documents into hierarchical structure with metadata
        Returns: (all_nodes, hierarchy_info)
        """
        all_nodes = []
        hierarchy_info = {
            "claims": {},
            "documents": {},
            "sections": {},
        }

        for i, doc in enumerate(documents, 1):
            # Extract metadata
            filename = doc.metadata.get("file_name", "unknown")
            text = doc.text if doc.text else ""

            # Skip empty documents
            if not text or not text.strip():
                print(f"  Warning: Skipping empty document: {filename}")
                continue

            # Extract hierarchical metadata using LLM
            print(f"  Extracting metadata from {filename} ({i}/{len(documents)})...")
            metadata = self.extract_metadata_from_text(text, filename)

            # Track hierarchy
            claim_id = metadata.get("claim_id") or "unknown"
            doc_type = metadata.get("document_type") or "unknown"

            if claim_id not in hierarchy_info["claims"]:
                hierarchy_info["claims"][claim_id] = {
                    "documents": [],
                    "document_types": set(),
                }

            if filename not in hierarchy_info["documents"]:
                hierarchy_info["documents"][filename] = {
                    "claim_id": claim_id,
                    "document_type": doc_type,
                    "sections": [],
                }
                hierarchy_info["claims"][claim_id]["documents"].append(filename)
                hierarchy_info["claims"][claim_id]["document_types"].add(doc_type)

            # Create multi-size chunks with metadata
            nodes = self.create_multi_size_chunks(text, metadata)
            if nodes:
                all_nodes.extend(nodes)
                print(
                    f"    Created {len(nodes)} chunks for {filename} "
                    f"(small: {sum(1 for n in nodes if n.metadata.get('chunk_size') == 'small')}, "
                    f"medium: {sum(1 for n in nodes if n.metadata.get('chunk_size') == 'medium')}, "
                    f"large: {sum(1 for n in nodes if n.metadata.get('chunk_size') == 'large')})"
                )
            else:
                print(
                    f"    Warning: No chunks created for {filename} (text length: {len(text)})"
                )

            # Track sections
            if metadata.get("section"):
                section = metadata["section"]
                if section not in hierarchy_info["sections"]:
                    hierarchy_info["sections"][section] = {
                        "claim_id": claim_id,
                        "document": filename,
                    }

        # Convert sets to lists for JSON serialization
        for claim_id in hierarchy_info["claims"]:
            hierarchy_info["claims"][claim_id]["document_types"] = list(
                hierarchy_info["claims"][claim_id]["document_types"]
            )

        return all_nodes, hierarchy_info
