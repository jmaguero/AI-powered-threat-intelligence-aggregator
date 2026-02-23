"""
Vector database operations using ChromaDB for semantic search over threat intelligence.
"""
import hashlib
import chromadb
from chromadb.config import Settings
from pathlib import Path
import ollama

from django.conf import settings


# Initialize ChromaDB client
CHROMA_DB_PATH = Path(settings.BASE_DIR) / "chroma_db"
CHROMA_DB_PATH.mkdir(exist_ok=True)

client = chromadb.PersistentClient(
    path=str(CHROMA_DB_PATH),
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True,
    )
)

# Collection for article embeddings
COLLECTION_NAME = "threat_intel_articles"


def get_collection():
    """Get or create the ChromaDB collection for articles."""
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Threat intelligence article embeddings"}
    )


def generate_embedding(text: str, model: str = "qwen2.5:7b") -> list[float]:
    """
    Generate embeddings for text using Ollama.

    Args:
        text: Text to embed
        model: Ollama model to use for embeddings

    Returns:
        List of floats representing the embedding vector
    """
    try:
        response = ollama.embed(
            model=model,
            input=text,
        )

        # Ollama returns embeddings in the 'embeddings' key
        if "embeddings" in response and response["embeddings"]:
            return response["embeddings"][0]
        elif "embedding" in response:
            return response["embedding"]
        else:
            raise ValueError(f"Unexpected response format: {response.keys()}")

    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")


def create_article_text(article) -> str:
    """
    Create a comprehensive text representation of an article for embedding.

    Args:
        article: Article model instance

    Returns:
        Formatted text combining all relevant article fields
    """
    parts = [
        f"Title: {article.title}",
        f"Summary: {article.summary}" if article.summary else "",
        f"AI Summary: {article.ai_summary}" if article.ai_summary else "",
        f"Threat Type: {article.threat_type}" if article.threat_type else "",
        f"Severity: {article.severity}" if article.severity else "",
        f"Affected Technology: {article.affected_tech}" if article.affected_tech else "",
        f"Source: {article.source}",
    ]

    return "\n".join(filter(None, parts))


def add_article_to_vector_db(article):
    """
    Add or update an article in the vector database.

    Args:
        article: Article model instance to embed and store

    Returns:
        True if successful, False otherwise
    """
    try:
        collection = get_collection()

        # Create text representation for embedding
        article_text = create_article_text(article)

        # Generate embedding
        embedding = generate_embedding(article_text)

        # Create unique ID for ChromaDB
        doc_id = f"article_{article.id}"

        # Prepare metadata (ChromaDB doesn't support null values)
        metadata = {
            "article_id": article.id,
            "title": article.title[:500] if article.title else "",  # ChromaDB has metadata size limits
            "source": article.source or "",
            "threat_type": article.threat_type or "",
            "severity": article.severity or "",
            "link": article.link[:500] if article.link else "",
        }

        # Add to collection (upsert behavior - updates if exists)
        collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[article_text[:1000]],  # Store truncated text for reference
        )

        return True

    except Exception as e:
        print(f"Error adding article {article.id} to vector DB: {e}")
        return False


def semantic_search(query: str, n_results: int = 10, filters: dict = None) -> list[dict]:
    """
    Perform semantic search over the article embeddings.

    Args:
        query: Natural language search query
        n_results: Number of results to return
        filters: Optional metadata filters (e.g., {"threat_type": "ransomware"})

    Returns:
        List of dicts with article_id, distance, and metadata
    """
    try:
        collection = get_collection()

        # Generate embedding for the query
        query_embedding = generate_embedding(query)

        # Build where clause for filtering
        where_clause = None
        if filters:
            where_clause = {}
            for key, value in filters.items():
                if value:  # Only add non-empty filters
                    where_clause[key] = value

        # Search the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
        )

        # Format results
        formatted_results = []
        if results and results.get("ids") and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "article_id": results["metadatas"][0][i]["article_id"],
                    "distance": results["distances"][0][i] if "distances" in results else 0,
                    "metadata": results["metadatas"][0][i],
                })

        return formatted_results

    except Exception as e:
        print(f"Error performing semantic search: {e}")
        return []


def delete_article_from_vector_db(article_id: int):
    """
    Remove an article from the vector database.

    Args:
        article_id: ID of the article to remove
    """
    try:
        collection = get_collection()
        doc_id = f"article_{article_id}"
        collection.delete(ids=[doc_id])
        return True
    except Exception as e:
        print(f"Error deleting article {article_id} from vector DB: {e}")
        return False


def get_vector_db_stats() -> dict:
    """
    Get statistics about the vector database.

    Returns:
        Dict with count and other stats
    """
    try:
        collection = get_collection()
        return {
            "count": collection.count(),
            "name": collection.name,
        }
    except Exception as e:
        print(f"Error getting vector DB stats: {e}")
        return {"count": 0, "error": str(e)}
