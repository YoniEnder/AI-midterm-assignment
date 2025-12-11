"""
MapReduce Summarization Implementation
Implements Map Phase (chunk summaries) and Reduce Phase (hierarchical merging)
"""

from typing import List, Dict
from llama_index.core.schema import TextNode
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings


class MapReduceSummarizer:
    """
    Implements MapReduce summarization:
    - Map Phase: Each chunk summarized individually
    - Reduce Phase: Summaries merged into Section → Document → Claim-level summaries
    """

    def __init__(self, llm=None):
        self.llm = llm or Settings.llm or OpenAI(temperature=0.3, model="gpt-4")

        # Map phase prompt - summarize individual chunk
        self.map_prompt = PromptTemplate(
            """Summarize the following chunk of text. Focus on:
- Key events and timeline information
- Important entities (people, organizations, locations)
- Key decisions and outcomes
- Important dates and timestamps

Chunk Text:
{chunk_text}

Provide a concise summary that captures the essential information.
"""
        )

        # Reduce phase prompt - merge summaries
        self.reduce_prompt = PromptTemplate(
            """Merge the following summaries into a comprehensive summary. 
Organize by:
- Timeline of events
- Key entities involved
- Important decisions made
- Outcomes and conclusions

Summaries to merge:
{summaries}

Provide a well-structured merged summary.
"""
        )

    def map_phase(self, nodes: List[TextNode]) -> Dict[str, str]:
        """
        Map Phase: Summarize each chunk individually
        Returns: dict mapping node_id to summary
        """
        summaries = {}
        print(f"  Map Phase: Summarizing {len(nodes)} chunks...")
        print(f"    This may take a while. Processing in batches...")

        for i, node in enumerate(nodes):
            # Print progress more frequently for better visibility
            if i % 5 == 0 or i == len(nodes) - 1:
                print(
                    f"    Processed {i}/{len(nodes)} chunks... ({i*100//len(nodes)}%)"
                )

            # Skip empty nodes
            if not node.text or not node.text.strip():
                print(f"    Warning: Skipping empty chunk {i}")
                continue

            try:
                # Truncate very long chunks to avoid token limits
                chunk_text = node.text[:5000] if len(node.text) > 5000 else node.text
                prompt = self.map_prompt.format(chunk_text=chunk_text)
                response = self.llm.complete(prompt)
                summaries[node.node_id] = response.text.strip()
            except Exception as e:
                print(f"    Error summarizing chunk {i}: {e}")
                # Use a simple summary as fallback
                summaries[node.node_id] = (
                    f"Summary: {node.text[:200]}..."
                    if len(node.text) > 200
                    else node.text
                )

        print(f"    Completed: {len(summaries)}/{len(nodes)} chunks summarized")
        return summaries

    def reduce_by_section(
        self, nodes: List[TextNode], chunk_summaries: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Reduce Phase: Merge summaries by section
        """
        section_summaries = {}

        # Group nodes by section
        sections = {}
        for node in nodes:
            section = node.metadata.get("section", "Unknown Section")
            if section not in sections:
                sections[section] = []
            sections[section].append(node)

        # Merge summaries for each section
        print(f"  Reduce Phase: Merging {len(sections)} sections...")
        for section, section_nodes in sections.items():
            if len(section_nodes) == 0:
                continue

            summaries_to_merge = []
            for node in section_nodes:
                if node.node_id in chunk_summaries:
                    summaries_to_merge.append(chunk_summaries[node.node_id])

            if summaries_to_merge:
                try:
                    merged_text = "\n\n".join(summaries_to_merge)
                    prompt = self.reduce_prompt.format(summaries=merged_text)
                    response = self.llm.complete(prompt)
                    section_summaries[section] = response.text.strip()
                except Exception as e:
                    print(f"    Error merging section {section}: {e}")
                    section_summaries[section] = "\n".join(summaries_to_merge[:3])

        return section_summaries

    def reduce_by_document(
        self, nodes: List[TextNode], section_summaries: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Reduce Phase: Merge section summaries into document summaries
        """
        document_summaries = {}

        # Group sections by document
        documents = {}
        for node in nodes:
            filename = node.metadata.get("filename", "unknown")
            section = node.metadata.get("section", "Unknown Section")
            if filename not in documents:
                documents[filename] = set()
            documents[filename].add(section)

        print(f"  Reduce Phase: Merging into {len(documents)} documents...")
        for filename, sections in documents.items():
            summaries_to_merge = []
            for section in sections:
                if section in section_summaries:
                    summaries_to_merge.append(
                        f"Section: {section}\n{section_summaries[section]}"
                    )

            if summaries_to_merge:
                try:
                    merged_text = "\n\n".join(summaries_to_merge)
                    prompt = self.reduce_prompt.format(summaries=merged_text)
                    response = self.llm.complete(prompt)
                    document_summaries[filename] = response.text.strip()
                except Exception as e:
                    print(f"    Error merging document {filename}: {e}")
                    document_summaries[filename] = "\n".join(summaries_to_merge[:3])

        return document_summaries

    def reduce_by_claim(
        self, nodes: List[TextNode], document_summaries: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Reduce Phase: Merge document summaries into claim-level summaries
        """
        claim_summaries = {}

        # Group documents by claim
        claims = {}
        for node in nodes:
            claim_id = node.metadata.get("claim_id", "unknown")
            filename = node.metadata.get("filename", "unknown")
            if claim_id not in claims:
                claims[claim_id] = set()
            claims[claim_id].add(filename)

        print(f"  Reduce Phase: Merging into {len(claims)} claims...")
        for claim_id, filenames in claims.items():
            summaries_to_merge = []
            for filename in filenames:
                if filename in document_summaries:
                    doc_type = None
                    for node in nodes:
                        if node.metadata.get("filename") == filename:
                            doc_type = node.metadata.get("document_type", "Unknown")
                            break
                    summaries_to_merge.append(
                        f"Document: {filename} ({doc_type})\n{document_summaries[filename]}"
                    )

            if summaries_to_merge:
                try:
                    merged_text = "\n\n".join(summaries_to_merge)
                    prompt = self.reduce_prompt.format(summaries=merged_text)
                    response = self.llm.complete(prompt)
                    claim_summaries[claim_id] = response.text.strip()
                except Exception as e:
                    print(f"    Error merging claim {claim_id}: {e}")
                    claim_summaries[claim_id] = "\n".join(summaries_to_merge[:3])

        return claim_summaries

    def create_summary_nodes(
        self,
        original_nodes: List[TextNode],
        chunk_summaries: Dict[
            str, str
        ],  # Used for reference, not directly in this function
        section_summaries: Dict[str, str],
        document_summaries: Dict[str, str],
        claim_summaries: Dict[str, str],
    ) -> List[TextNode]:
        """
        Create summary nodes at different hierarchy levels
        """
        summary_nodes = []

        # Create claim-level summary nodes
        for claim_id, summary_text in claim_summaries.items():
            node = TextNode(
                text=summary_text,
                metadata={
                    "hierarchy_level": "claim",
                    "claim_id": claim_id,
                    "summary_type": "claim_level",
                },
            )
            summary_nodes.append(node)

        # Create document-level summary nodes
        for filename, summary_text in document_summaries.items():
            # Get claim_id and document_type from original nodes
            claim_id = None
            doc_type = None
            for orig_node in original_nodes:
                if orig_node.metadata.get("filename") == filename:
                    claim_id = orig_node.metadata.get("claim_id")
                    doc_type = orig_node.metadata.get("document_type")
                    break

            node = TextNode(
                text=summary_text,
                metadata={
                    "hierarchy_level": "document",
                    "claim_id": claim_id,
                    "document_type": doc_type,
                    "filename": filename,
                    "summary_type": "document_level",
                },
            )
            summary_nodes.append(node)

        # Create section-level summary nodes
        for section, summary_text in section_summaries.items():
            # Get metadata from original nodes
            claim_id = None
            filename = None
            for orig_node in original_nodes:
                if orig_node.metadata.get("section") == section:
                    claim_id = orig_node.metadata.get("claim_id")
                    filename = orig_node.metadata.get("filename")
                    break

            node = TextNode(
                text=summary_text,
                metadata={
                    "hierarchy_level": "section",
                    "claim_id": claim_id,
                    "section": section,
                    "filename": filename,
                    "summary_type": "section_level",
                },
            )
            summary_nodes.append(node)

        return summary_nodes
