from clients import *
from data_loader import *
from vector_db import *
from justification import *
from html_output import *
import uuid

RESUME_DIR = '../data/resumes/'
PARA_JOB_CSV = '../data/jobs/Paraform_Jobs.csv'
SRN_JOBS_DIR = '../utils/scrape-pdf/output/'

def main_task1_hybrid_pipeline(resume_dir, para_job_csv, srn_job_dir):
    """Runs the entire Task 1 pipeline using hybrid search."""

    print("--- Loading & Indexing Jobs ---")
    try:
        paraform_jobs = load_paraform_jobs(para_job_csv)
        srn_jobs = []
        for filename in os.listdir(srn_job_dir):
            if filename.endswith(".pdf"):
                srn_jobs.extend(load_srn_jobs(os.path.join(srn_job_dir, filename)))
        all_jobs = paraform_jobs + srn_jobs
        
        for job in all_jobs:
            job['id'] = str(uuid.uuid4())
            
        if not all_jobs:
            print("Halting pipeline: No job data loaded.")
            return None, None
        index_jobs_to_qdrant(all_jobs, QDRANT_COLLECTION_NAME)
    except Exception as e:
         print(f"Qdrant collection '{QDRANT_COLLECTION_NAME}' not found or error checking. Attempting to index jobs...")
         paraform_jobs = load_paraform_jobs(para_job_csv)
         srn_jobs = load_srn_jobs(srn_job_dir)
         all_jobs = paraform_jobs + srn_jobs

         if not all_jobs:
             print("Halting pipeline: No job data loaded.")
             return None, None
         index_jobs_to_qdrant(all_jobs, QDRANT_COLLECTION_NAME)


    # --- 2. Prepare BM25 Index (Needs job texts) --- #
    print("\n--- Preparing BM25 Index ---")
    job_corpus_texts = [job['text'] for job in all_jobs]
    job_corpus_ids = [job['id'] for job in all_jobs]

    if not job_corpus_texts:
         print("Error: No job text available for BM25 index. Sparse search disabled.")
         bm25 = None
    else:
        tokenized_corpus = [preprocess_text_for_bm25(doc) for doc in job_corpus_texts]
        bm25 = BM25Okapi(tokenized_corpus)
        print("BM25 index prepared.")

    # --- 3. Load Resumes --- #
    print("\n--- Loading Resumes ---")
    resume_files = [f for f in os.listdir(resume_dir) if f.lower().endswith('.pdf')]
    if not resume_files:
        print(f"Halting pipeline: No PDF resumes found in {resume_dir}")
        return bm25, job_corpus_ids

    results = []

    # --- 4. Process Each Resume --- #
    print("\n--- Processing Resumes ---")
    for resume_filename in resume_files:
        print(f"\n--- Matching Resume: {resume_filename} ---")
        resume_path = os.path.join(resume_dir, resume_filename)
        resume_text = parse_pdf_resume(resume_path)

        if not resume_text:
            print(f"Skipping {resume_filename} due to parsing error.")
            continue

        # --- 5. Perform Hybrid Search --- #
        print("Performing dense search...")
        dense_results = perform_dense_search(resume_text, top_k=20)
        print(f"Dense search returned {len(dense_results)} results.")

        sparse_results = []
        if bm25:
            print("Performing sparse search...")
            sparse_results = perform_sparse_search(resume_text, bm25, job_corpus_ids, top_k=20)
            print(f"Sparse search returned {len(sparse_results)} results.")
        else:
            print("Skipping sparse search (BM25 index not available).")

        print("Combining results using RRF...")
        hybrid_results = combine_results_rrf(dense_results, sparse_results)
        print(f"Hybrid search yielded {len(hybrid_results)} combined results.")

        # --- 6. Generate Justifications for Top 2 ---
        top_2_matches = hybrid_results[:2]
        match_details_with_justification = []

        if not top_2_matches:
            print(f"No matches found for {resume_filename}.")
        else:
            print(f"Generating justifications for top {len(top_2_matches)} matches...")
            for match in top_2_matches:
                job_payload = match['payload']
                # Use RRF score for fit scoring
                fit_score = score_fit_hybrid(match['rrf_score'])
                justification = generate_justification_azure(resume_text, job_payload, fit_score)

                # Construct job details string from payload
                job_details_str = (
                    f"{job_payload.get('name', 'N/A')} "
                    f"({job_payload.get('source', 'N/A')}) - ID: {match['id']}"
                )

                match_details_with_justification.append({
                    "job_details": job_details_str,
                    "fit_score": fit_score,
                    "justification": justification,
                    "rrf_score": match['rrf_score'] # Keep for reference
                })

        results.append({
            "resume_name": resume_filename,
            "top_matches": match_details_with_justification
        })

    # --- 7. Display Results --- #
    print("\n\n--- FINAL RESULTS ---")
    if not results:
        print("No matching results were generated.")
    else:
        table_data = format_results_for_table(results)
        df = pd.DataFrame(table_data)
        html_output = generate_html_table(results, df)
        with open("../output/resume_job_matches.html", "w") as f:
            f.write(html_output)

        print(f"\nHTML table saved to: {os.path.abspath('task1_job_matches.html')}")
    print("--- END OF RESULTS ---")

    return bm25, job_corpus_ids

# --- Run the Pipeline --- #
if __name__ == "__main__":
    if not all([azure_endpoint, azure_api_key, azure_api_version, azure_chat_deployment, azure_embedding_deployment]):
         print("\nERROR: Azure OpenAI environment variables are not fully set. Please check your .env file or environment.")
    else:
        _, _ = main_task1_hybrid_pipeline(RESUME_DIR, PARA_JOB_CSV, SRN_JOBS_DIR)