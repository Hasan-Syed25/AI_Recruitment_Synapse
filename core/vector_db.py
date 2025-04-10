from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
from clients import embedding_client
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import time
import os
import re
import numpy as np
from collections import defaultdict

load_dotenv()

azure_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# --- Constants --- #
QDRANT_COLLECTION_NAME = "job_postings_v2"
EMBEDDING_DIMENSION = 1536

# Initialize Qdrant Client
try:
    qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=3000)
    print("Qdrant client initialized successfully.")
except Exception as e:
    print(f"Error initializing Qdrant client: {e}")
    print("Please ensure Qdrant is running (e.g., via Docker) and accessible.")
    exit()

# --- Helper Functions ---
stop_words = set(stopwords.words('english'))

def preprocess_text_for_bm25(text):
    """Basic text cleaning and tokenization for BM25."""
    if not isinstance(text, str):
        return []
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text) # Remove punctuation
    tokens = word_tokenize(text, language='english', preserve_line=True)
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
    return tokens


def get_azure_embedding(text, model_deployment=azure_embedding_deployment):
    """Generates embedding using Azure OpenAI."""
    if not text or not isinstance(text, str):
        print("Warning: Empty or invalid text passed to get_azure_embedding.")
        return [0.0] * EMBEDDING_DIMENSION # Return zero vector
    try:
        # Azure OpenAI client expects 'input' not 'inputs'
        response = embedding_client.embeddings.create(input=text, model=model_deployment)
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting Azure embedding: {e}")
        # Retry mechanism could be added here
        return [0.0] * EMBEDDING_DIMENSION # Return zero vector on error


def index_jobs_to_qdrant(jobs, collection_name=QDRANT_COLLECTION_NAME):
    """Creates Qdrant collection and indexes jobs with embeddings."""
    try:
        # Check if collection exists, create if not
        collections = qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            print(f"Creating Qdrant collection: {collection_name}")
            qdrant_client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE) # We are handling sparse vectors separately
            )
        else:
            print(f"Using existing Qdrant collection: {collection_name}")

        points_to_upsert = []
        print(f"Generating embeddings and preparing points for {len(jobs)} jobs...")
        count = 0
        batch_size = 16 # Process in batches
        for i in range(0, len(jobs), batch_size):
            batch_jobs = jobs[i:i+batch_size]
            job_texts = [job['text'] for job in batch_jobs]

            # Get embeddings in batch (more efficient if API supports it, Azure client handles it)
            try:
                 embeddings = [get_azure_embedding(text) for text in job_texts]
            except Exception as e:
                 print(f"Error getting batch embeddings: {e}. Retrying individually.")
                 embeddings = []
                 for text in job_texts:
                     # Add slight delay if hitting rate limits
                     time.sleep(0.1)
                     embeddings.append(get_azure_embedding(text))


            for job, embedding in zip(batch_jobs, embeddings):
                 if embedding is not None and any(embedding): # Check for valid embedding
                     points_to_upsert.append(
                         PointStruct(
                             id=job['id'],
                             vector=embedding,
                             payload=job['payload'] # Store original text and metadata
                         )
                     )
                 else:
                     print(f"Warning: Skipping job {job['id']} due to embedding failure.")

            if points_to_upsert:
                 print(f"Upserting batch {i//batch_size + 1} ({len(points_to_upsert)} points)...")
                 qdrant_client.upsert(collection_name=collection_name, points=points_to_upsert, wait=True)
                 count += len(points_to_upsert)
                 points_to_upsert = [] # Reset batch
            time.sleep(0.5) # Small delay between batches

        print(f"Successfully indexed {count} jobs into Qdrant collection '{collection_name}'.")

    except Exception as e:
        print(f"Error during Qdrant indexing: {e}")

# --- Matching Logic ---

def perform_dense_search(query_text, top_k=10):
    """Performs dense vector search in Qdrant."""
    query_vector = get_azure_embedding(query_text)
    if not any(query_vector):
        print("Error: Could not generate query embedding for dense search.")
        return []
    try:
        search_result = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        # Convert ScoredPoint to a simpler dict
        return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in search_result]
    except Exception as e:
        print(f"Error during Qdrant dense search: {e}")
        return []

def perform_sparse_search(query_text, bm25_index, job_corpus_ids, top_k=10):
    """Performs sparse search using BM25."""
    tokenized_query = preprocess_text_for_bm25(query_text)
    if not tokenized_query:
        return []
    try:
        # Get scores for all documents in the corpus
        doc_scores = bm25_index.get_scores(tokenized_query)

        # Get top N indices and their scores
        top_n_indices = np.argsort(doc_scores)[::-1][:top_k]
        results = []
        for idx in top_n_indices:
             # Ensure score is not negative infinity or NaN
             score = doc_scores[idx]
             if np.isfinite(score):
                 results.append({
                     "id": job_corpus_ids[idx], # Map index back to job ID
                     "score": score
                 })
        return results
    except Exception as e:
        print(f"Error during BM25 sparse search: {e}")
        return []


def combine_results_rrf(dense_results, sparse_results, k=60):
    """
    Combines dense and sparse search results using Reciprocal Rank Fusion (RRF),
    handling string-based UUIDs as document IDs.

    Args:
        dense_results: List of search results (e.g., ScoredPoint objects or dicts) from dense vector search.
                       Each result must have an 'id' attribute/key.
        sparse_results: List of search results (e.g., ScoredPoint objects or dicts) from sparse vector search.
                        Each result must have an 'id' attribute/key.
        k (int): The ranking constant for RRF (default: 60).

    Returns:
        list: A list of dictionaries, each containing the 'id' (string UUID),
              'rrf_score', and 'payload' of the combined and ranked results.
              Returns results with payload=None if retrieval fails.
    """
    combined_scores = defaultdict(float)

    # Helper function to process results and ensure ID is string
    def process_results(results, current_rank_offset=0):
        # Start enumeration from 0 for rank calculation relative to the list start
        for rank, result in enumerate(results):
            # Handle both ScoredPoint objects and dictionaries for flexibility
            doc_id_raw = getattr(result, 'id', None) or result.get('id')
            if doc_id_raw is None:
                print(f"Warning: Skipping result at rank {rank} due to missing ID.")
                continue

            # Ensure doc_id is a string for consistency (handles UUID objects or strings)
            doc_id = str(doc_id_raw)

            # RRF formula uses the rank within its own list (0-based)
            combined_scores[doc_id] += 1.0 / (k + rank + 1)

    # Process dense and sparse results
    process_results(dense_results)
    process_results(sparse_results)


    # Sort by combined RRF score in descending order
    # combined_scores.items() -> [('uuid-str-1', score1), ('uuid-str-3', score3), ...]
    sorted_results = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)

    # Retrieve payloads for the top results from Qdrant
    final_results = []
    # Ensure top_ids contains strings
    top_ids = [doc_id for doc_id, score in sorted_results]

    if not top_ids:
        return [] # No results to combine or retrieve

    try:
        # Fetch points from Qdrant using the string UUIDs
        qdrant_points = qdrant_client.retrieve(
            collection_name=QDRANT_COLLECTION_NAME,
            ids=top_ids, # Pass the list of string UUIDs
            with_payload=True,
            with_vectors=False
        )

        # Create a map for quick payload lookup using string UUIDs
        # Ensure point.id is also treated as string for map keys
        payload_map = {str(point.id): point.payload for point in qdrant_points}

        # Build final results list, preserving the RRF order
        for doc_id, rrf_score in sorted_results: # doc_id is already a string here from the initial processing/sorting
            payload = payload_map.get(doc_id)
            # Include result even if payload is missing (was None or retrieve failed for that ID)
            final_results.append({
                "id": doc_id,
                "rrf_score": rrf_score,
                "payload": payload # Will be None if not found in payload_map or if originally None
            })

    except Exception as e:
        print(f"Error retrieving payloads for RRF results: {e}. Returning results without payloads.")
        # Fallback: return IDs and scores only
        final_results = [{"id": str(doc_id), "rrf_score": rrf_score, "payload": None}
                         for doc_id, rrf_score in sorted_results]

    return final_results

def score_fit_hybrid(rrf_score):
    """Converts RRF score to a 1-10 scale with significant differentiation between scores."""
    # Typical RRF scores are small but meaningful differences matter
    # Using a logarithmic scale to amplify differences
    max_observed_rrf = 0.04  # Base calibration value
    
    if rrf_score <= 0:
        return 1.0

    log_score = np.log1p(rrf_score * 100) / np.log1p(max_observed_rrf * 100)
    scaled_score = 1.0 + 9.0 * (log_score ** 1.5)
    fit_score = round(scaled_score * 2) / 2.0
    
    return max(1.0, min(10.0, fit_score))  # Ensure score is within [1, 10]
