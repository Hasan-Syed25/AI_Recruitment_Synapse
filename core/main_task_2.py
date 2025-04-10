import pandas as pd
import json
import random
from clients import *
from justification import *
from html_output import *
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helper_task_2 import *

PARA_JOB_CSV = '../data/jobs/Paraform_Jobs.csv'
CANDIDATE_CSV = '../data/candidates/JuiceboxExport_1743820890826.csv'
LINKEDIN_JSON = '../data/candidates/first_five_profiles.json'
OUTPUT_HTML_FILE = '../output/task2_candidate_results.html'


def main_task2_pipeline(para_job_csv, candidate_csv, linkedin_json):
    """Runs the entire Task 2 pipeline."""

    # --- 1. Load Data --- #
    print("--- Loading Data ---")
    try:
        jobs_df = pd.read_csv(para_job_csv)
        print(f"Loaded {len(jobs_df)} jobs.")
    except FileNotFoundError:
        print(f"Error: Job CSV not found at {para_job_csv}")
        return
    except Exception as e:
        print(f"Error loading jobs CSV: {e}")
        return

    try:
        candidates_df = pd.read_csv(candidate_csv)
        candidates_df['Full Name'] = candidates_df['First name'].fillna('') + ' ' + candidates_df['Last name'].fillna('')
        candidates_df['LinkedIn'] = candidates_df['LinkedIn'].str.strip()
        print(f"Loaded {len(candidates_df)} candidates.")
    except FileNotFoundError:
        print(f"Error: Candidate CSV not found at {candidate_csv}")
        return
    except Exception as e:
        print(f"Error loading candidates CSV: {e}")
        return

    linkedin_profiles = {}
    try:
        with open(linkedin_json, 'r') as f:
            linkedin_data_list = json.load(f)
        for profile in linkedin_data_list:
            profile_url = f"https://linkedin.com/in/{profile.get('public_identifier', '')}".strip()
            if profile_url:
                 linkedin_profiles[profile_url] = profile
        print(f"Loaded {len(linkedin_profiles)} scraped LinkedIn profiles.")
    except FileNotFoundError:
        print(f"Warning: LinkedIn JSON not found at {linkedin_json}. Enhancement will be limited.")
    except Exception as e:
        print(f"Error loading LinkedIn JSON: {e}")


    # --- 2. Select Job --- #
    print("\n--- Selecting Job ---")
    selected_job_index = random.randint(0, len(jobs_df) - 1)
    selected_job = jobs_df.iloc[selected_job_index].to_dict()
    print(f"Selected Job: {selected_job.get('Role', 'N/A')} at {selected_job.get('Company', 'N/A')}")
    job_summary = {
        'Role': selected_job.get('Role'),
        'Company': selected_job.get('Company'),
        'YOE': selected_job.get('YOE'),
        'Requirements': selected_job.get('Requirements', ''),
        'Tech Stack': selected_job.get('Tech Stack', ''),
        'Industry': selected_job.get('Industry', '')
    }


    # --- 3. Process & Score Candidates --- #
    print("\n--- Processing and Scoring Candidates ---")
    candidate_scores = []

    for index, cand_row in candidates_df.iterrows():
        print(f"Processing candidate {index+1}/{len(candidates_df)}: {cand_row['Full Name']}")
        juicebox_info = cand_row.to_dict()
        linkedin_url = juicebox_info.get('LinkedIn')
        scraped_profile = None

        if linkedin_url and linkedin_url in linkedin_profiles:
            scraped_profile = linkedin_profiles[linkedin_url]
        candidate_unified = {
            'name': juicebox_info.get('Full Name'),
            'linkedin': linkedin_url,
            'location': juicebox_info.get('Location'),
            'current_title': juicebox_info.get('Current Title')
        }
        if scraped_profile:
             candidate_unified['current_title'] = scraped_profile.get('occupation', candidate_unified['current_title'])
             candidate_unified['headline'] = scraped_profile.get('headline')
             candidate_unified['summary'] = scraped_profile.get('summary')
             candidate_unified['experiences'] = scraped_profile.get('experiences', [])
             candidate_unified['skills_direct'] = scraped_profile.get('skills', [])
             yoe, hopping = calculate_experience_details(candidate_unified['experiences'])
             candidate_unified['yoe'] = yoe
             print(f"Calculated YOE: {yoe} years")
             print(f"Job Hopping: {hopping}")
             candidate_unified['job_hopping'] = hopping
             candidate_unified['startup_fit'] = check_startup_fit(candidate_unified['experiences'], job_summary)
        else:
             candidate_unified['yoe'] = 0 
             candidate_unified['job_hopping'] = False
             candidate_unified['startup_fit'] = 0.5
        candidate_unified['skills'] = extract_skills(scraped_profile, juicebox_info)

        score, score_details, overlap_skills = score_candidate_fit(candidate_unified, job_summary)

        candidate_scores.append({
            'Name': candidate_unified['name'],
            'LinkedIn': candidate_unified['linkedin'],
            'Score': score,
            'Details': score_details,
            'Summary': candidate_unified
        })


    # --- 4. Rank Candidates --- #
    print("\n--- Ranking Candidates ---")
    ranked_candidates = sorted(candidate_scores, key=lambda x: x['Score'], reverse=True)
    top_candidates = ranked_candidates[:10]

    # --- 5. Generate Justifications & Messages for Top Candidates --- #
    print("\n--- Generating Justifications & Messages for Top Candidates ---")
    results_table = []
    for i, cand in enumerate(top_candidates):
        print(f"Generating justification for: {cand['Name']} (Rank {i+1}, Score: {cand['Score']})")
        justification = generate_candidate_justification_azure(
            cand['Summary'], job_summary, cand['Score'], cand['Details']
        )
        linkedin_message = generate_linkedin_message_azure(cand['Summary'], job_summary)
        
        results_table.append({
            'Rank': i + 1,
            'Name': cand['Name'],
            'LinkedIn': cand['LinkedIn'],
            'Score': cand['Score'],
            'Why': justification,
            'LinkedIn Message (Optional)': linkedin_message
        })

    # --- 6. Display Results --- #
    print("\n\n--- FINAL RESULTS (Top Candidates) ---")
    results_df = pd.DataFrame(results_table)
    generate_task2_html_table(results_df, OUTPUT_HTML_FILE)
    print("--- END OF RESULTS ---")


# --- Run the Pipeline --- #
if __name__ == "__main__":
    if '../data/' not in PARA_JOB_CSV or '../data/' not in CANDIDATE_CSV or '../data/' not in LINKEDIN_JSON:
         print("\nERROR: Please update the placeholder file paths (PARA_JOB_CSV, CANDIDATE_CSV, LINKEDIN_JSON) in the script before running.")
    elif not all([azure_endpoint, azure_api_key, azure_api_version, azure_chat_deployment]):
         print("\nERROR: Azure OpenAI environment variables are not fully set. Please check your .env file or environment.")
    else:
        main_task2_pipeline(PARA_JOB_CSV, CANDIDATE_CSV, LINKEDIN_JSON)