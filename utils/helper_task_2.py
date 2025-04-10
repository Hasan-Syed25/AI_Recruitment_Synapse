import pandas as pd
import os
import re
import json
import random
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from openai import AzureOpenAI
from thefuzz import fuzz # For fuzzy string matching
import numpy as np
import nltk # Using NLTK for tokenization if needed

def parse_yoe_string(yoe_str):
    """Parses YOE strings like '5-10 years', '3+ years', '2 years' into min/max."""
    if not isinstance(yoe_str, str):
        return None, None
    yoe_str = yoe_str.lower().replace('years', '').replace('year', '').strip()
    min_yoe, max_yoe = None, None
    try:
        if '-' in yoe_str:
            parts = yoe_str.split('-')
            min_yoe = int(parts[0].strip())
            max_yoe = int(parts[1].strip())
        elif '+' in yoe_str:
            min_yoe = int(yoe_str.replace('+', '').strip())
            max_yoe = float('inf') # No upper limit
        else:
            min_yoe = int(yoe_str.strip())
            max_yoe = min_yoe
    except ValueError:
        print(f"Warning: Could not parse YOE string: {yoe_str}")
        return None, None
    return min_yoe, max_yoe

def calculate_experience_details(experiences):
    """Calculates total YOE and checks for job hopping from LinkedIn experience list."""
    if not experiences:
        return 0, False # No experience, no job hopping

    total_months = 0
    job_durations_months = []
    now = datetime.now()

    for exp in experiences:
        starts_at = exp.get('starts_at')
        ends_at = exp.get('ends_at')

        if not starts_at: continue # Skip if no start date

        try:
            start_date = datetime(starts_at['year'], starts_at['month'], starts_at.get('day', 1))
        except (ValueError, TypeError):
             print(f"Warning: Invalid start date format: {starts_at}")
             continue # Skip invalid entry

        end_date = None
        if ends_at:
            try:
                # Handle potential missing day - default to end of month? For duration, start of month is safer.
                end_date = datetime(ends_at['year'], ends_at['month'], ends_at.get('day', 1))
            except (ValueError, TypeError):
                 print(f"Warning: Invalid end date format: {ends_at}")
                 end_date = now # Assume ongoing if end date is invalid but present
        else:
            # No end date usually means current job
            end_date = now

        # Calculate duration for this job
        duration = relativedelta(end_date, start_date)
        duration_months = duration.years * 12 + duration.months
        job_durations_months.append(duration_months)
        total_months += duration_months # Note: This simple sum can overestimate if jobs overlap

    total_yoe = round(total_months / 12.0, 1)

    # Job hopping heuristic: more than 2 jobs lasting less than 12 months in recent history (e.g., last 5 years - harder to check precisely without full dates)
    short_tenures = sum(1 for duration in job_durations_months if duration < 12)
    job_hopping_flag = short_tenures >= 2 # Adjust threshold as needed

    return total_yoe, job_hopping_flag

def extract_skills(profile_data, juicebox_data):
    """Extracts skills from combined profile data."""
    skills = set()

    # From LinkedIn data (if available)
    if profile_data:
        if profile_data.get('skills'): # Direct skills list
             for skill in profile_data['skills']:
                 if isinstance(skill, str): # Proxycurl sometimes returns list of strings
                      skills.add(skill.lower())
                 elif isinstance(skill, dict) and 'name' in skill: # Or list of dicts
                      skills.add(skill['name'].lower())

        if profile_data.get('headline'):
            # Simple tokenization of headline
            tokens = re.findall(r'\b\w+\b', profile_data['headline'].lower())
            skills.update(tokens) # Add individual words

        if profile_data.get('summary'):
             tokens = re.findall(r'\b\w+\b', profile_data['summary'].lower())
             skills.update(tokens)

        if profile_data.get('experiences'):
            for exp in profile_data['experiences']:
                if exp.get('title'):
                    tokens = re.findall(r'\b\w+\b', exp['title'].lower())
                    skills.update(tokens)
                if exp.get('description'):
                    tokens = re.findall(r'\b\w+\b', exp['description'].lower())
                    skills.update(tokens)

    # From Juicebox data (fallback or supplement)
    if juicebox_data.get('Current Title'):
        tokens = re.findall(r'\b\w+\b', juicebox_data['Current Title'].lower())
        skills.update(tokens)

    # Basic cleanup (remove generic terms, could use NLTK stopwords)
    common_words = {'at', 'and', 'the', 'of', 'in', 'on', 'engineer', 'software', 'developer', 'manager', 'senior', 'lead', 'data', 'product'}
    skills = {skill for skill in skills if skill not in common_words and len(skill) > 1}

    return list(skills)


def check_startup_fit(experiences, job_company_context):
    """Heuristic check for startup experience."""
    # Very basic heuristic: Check for company names that don't sound like large corporations
    # Or check if funding/team size info is available and small.
    # This requires significant assumptions or external data enrichment.
    # For now, let's do a simple check based on company name length or common startup keywords.
    has_startup_exp = False
    if not experiences:
        return 0.5 # Unknown

    startup_keywords = ['labs', 'ai', 'tech', 'innovations', 'systems'] # Example keywords
    large_corp_indicators = ['technologies', 'corporation', 'inc', 'llc', 'group'] # Might indicate larger orgs

    for exp in experiences:
        company_name = exp.get('company', '').lower()
        # Simple check: shorter names or names ending in startup keywords might indicate startup
        if any(keyword in company_name for keyword in startup_keywords) and not any(ind in company_name for ind in large_corp_indicators):
             has_startup_exp = True
             break
        # Could also check company follower count on LinkedIn if available via scraping tool

    # Compare with job context (if available) - e.g., if job is at a startup, favor startup exp
    # job_is_startup = 'startup' in job_company_context.get('Industry', '').lower() or job_company_context.get('Team Size', 100) < 50

    if has_startup_exp:
        return 1.0 # Found potential startup experience
    else:
        # Could check if ONLY large company experience exists
        only_large_exp = True
        for exp in experiences:
             company_name = exp.get('company', '').lower()
             if not any(ind in company_name for ind in large_corp_indicators) and len(company_name) < 15: # Crude check
                 only_large_exp = False
                 break
        if only_large_exp and len(experiences) > 0:
             return 0.0 # Only seems to have large company experience
        else:
             return 0.5 # Unclear / Mixed
         
####### SCORING ########
         
def score_candidate_fit(candidate_data, job_data):
    """Scores a candidate against a job based on multiple criteria."""
    score_details = {}
    final_score = 0.0

    weights = {
        "title": 0.25,
        "yoe": 0.20,
        "tech_stack": 0.35,
        "startup_fit": 0.10,
        "tenure_penalty": 0.10 # Penalty weight if job hopping detected
    }

    # --- 1. Title Match --- #
    candidate_title = candidate_data.get('current_title', '')
    job_role = job_data.get('Role', '')
    title_score = 0.0
    if candidate_title and job_role:
        match_ratio = fuzz.token_set_ratio(candidate_title.lower(), job_role.lower())
        title_score = match_ratio / 100.0
    score_details['title'] = f"{title_score:.2f} (Cand: '{candidate_title}' vs Job: '{job_role}')"
    final_score += title_score * weights['title']

    # --- 2. YOE Match --- #
    cand_yoe, job_hopping = candidate_data.get('yoe', 0), candidate_data.get('job_hopping', False)
    job_yoe_min, job_yoe_max = parse_yoe_string(job_data.get('YOE', ''))
    yoe_score = 0.0
    yoe_detail = f"Cand YOE: {cand_yoe}, Job Req: {job_data.get('YOE', 'N/A')}"

    if job_yoe_min is not None:
        if cand_yoe >= job_yoe_min:
            yoe_score = 1.0 # Meets minimum
            if job_yoe_max is not None and job_yoe_max != float('inf') and cand_yoe > job_yoe_max * 1.5:
                 yoe_score *= 0.8 # Slight penalty for being vastly overqualified
        else:
            # Penalize based on how far below minimum
            yoe_score = max(0, 1.0 - (job_yoe_min - cand_yoe) / job_yoe_min) # Linear penalty
        yoe_detail += f" -> Score: {yoe_score:.2f}"
    else:
        yoe_score = 0.5 # Cannot determine requirement, neutral score
        yoe_detail += " -> Score: 0.5 (Job YOE unclear)"
    score_details['yoe'] = yoe_detail
    final_score += yoe_score * weights['yoe']

    # --- 3. Tech Stack Match --- #
    candidate_skills = candidate_data.get('skills', [])
    job_req_text = f"{job_data.get('Requirements', '')} {job_data.get('Tech Stack', '')}".lower()
    tech_score = 0.0
    overlap_skills = []
    if candidate_skills and job_req_text:
        job_req_tokens = set(re.findall(r'\b\w+\b', job_req_text))
        candidate_skills_set = set(s.lower() for s in candidate_skills) # Ensure lowercase

        # Find intersection
        overlap_skills = list(candidate_skills_set.intersection(job_req_tokens))

        # Score based on number of overlapping skills relative to candidate skills or job requirements
        relevant_job_tokens = {token for token in job_req_tokens if len(token) > 2 and token not in ['and', 'or', 'the', 'with', 'experience', 'required']}
        if relevant_job_tokens:
             tech_score = min(1.0, len(overlap_skills) / max(5, len(relevant_job_tokens)*0.5))
        else:
             tech_score = 0.0
             
    score_details['tech_stack'] = f"{tech_score:.2f} (Overlap: {len(overlap_skills)} skills - {', '.join(overlap_skills[:5])}..)"
    final_score += tech_score * weights['tech_stack']

    # --- 4. Startup Fit --- #
    startup_fit_score = candidate_data.get('startup_fit', 0.5) # Default to neutral
    score_details['startup_fit'] = f"{startup_fit_score:.2f}"
    final_score += startup_fit_score * weights['startup_fit']

    # --- 5. Tenure Penalty --- #
    tenure_penalty_applied = 0.0
    if job_hopping:
        tenure_penalty_applied = weights['tenure_penalty']
        final_score -= tenure_penalty_applied # Subtract penalty
        score_details['tenure'] = f"Potential job hopping detected (-{tenure_penalty_applied:.2f} penalty)"
    else:
        score_details['tenure'] = "OK"

    # --- Final Score (0-1 scale, then map to 1-10) --- #
    final_score_0_1 = max(0, final_score)
    final_score_1_10 = round(1 + final_score_0_1 * 9, 1)

    return final_score_1_10, score_details, overlap_skills


