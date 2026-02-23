#!/usr/bin/env python
"""
Quick test script for Phase 7 semantic search functionality.

Run this after setting up Phase 7 to verify everything works.

Usage:
    python test_semantic_search.py
"""
import requests
import json
import sys


BASE_URL = "http://localhost:8000/api/articles"


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def test_vector_stats():
    """Test the vector database statistics endpoint."""
    print_header("Testing Vector Database Statistics")

    try:
        response = requests.get(f"{BASE_URL}/vector-stats/")
        response.raise_for_status()
        data = response.json()

        print(f"✓ Vector DB Stats Retrieved")
        print(f"  Articles indexed: {data.get('count', 0)}")
        print(f"  Collection name: {data.get('name', 'N/A')}")

        if data.get('count', 0) == 0:
            print("\n⚠ Warning: No articles are indexed yet!")
            print("  Run: python manage.py embed_articles --enriched-only")

        return True

    except requests.exceptions.ConnectionError:
        print("✗ Connection failed. Is Django running?")
        print("  Run: python manage.py runserver")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_semantic_search(query, filters=None):
    """Test semantic search with a query."""
    print_header(f"Testing Semantic Search: '{query}'")

    params = {"q": query}
    if filters:
        params.update(filters)

    try:
        response = requests.get(f"{BASE_URL}/search/", params=params)
        response.raise_for_status()
        data = response.json()

        print(f"✓ Search completed")
        print(f"  Query: {data.get('query', 'N/A')}")
        print(f"  Results found: {data.get('count', 0)}")

        if data.get('count', 0) > 0:
            print(f"\n  Top {min(3, data['count'])} results:")
            for i, article in enumerate(data.get('results', [])[:3], 1):
                relevance = article.get('relevance_score', 0)
                print(f"\n  {i}. [{relevance:.2f}] {article.get('title', 'N/A')[:80]}")
                print(f"     Threat: {article.get('threat_type', 'N/A')} | "
                      f"Severity: {article.get('severity', 'N/A')} | "
                      f"Source: {article.get('source', 'N/A')}")
        else:
            print("\n  No results found. Try:")
            print("    - Checking if articles are embedded")
            print("    - Using a broader query")
            print("    - Removing filters")

        return True

    except requests.exceptions.ConnectionError:
        print("✗ Connection failed. Is Django running?")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_search_with_filters():
    """Test semantic search with filters."""
    print_header("Testing Search with Filters")

    filters = {"severity": "critical", "limit": 5}
    return test_semantic_search("vulnerability", filters)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  Phase 7: Semantic Search Test Suite")
    print("=" * 60)

    # Test 1: Vector DB stats
    if not test_vector_stats():
        print("\n❌ Basic connectivity failed. Cannot continue.")
        sys.exit(1)

    # Test 2: Basic semantic search
    test_semantic_search("ransomware attacks")

    # Test 3: Specific query
    test_semantic_search("phishing campaigns targeting financial institutions")

    # Test 4: Search with filters
    test_search_with_filters()

    # Test 5: Broad query
    test_semantic_search("security vulnerabilities")

    # Summary
    print_header("Test Summary")
    print("✓ All tests completed!")
    print("\nNext steps:")
    print("  1. If no results, run: python manage.py embed_articles")
    print("  2. Try your own queries: curl 'http://localhost:8000/api/articles/search/?q=YOUR_QUERY'")
    print("  3. Read PHASE7_RAG_GUIDE.md for detailed documentation")


if __name__ == "__main__":
    main()
