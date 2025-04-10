from clients import azure_client, azure_chat_deployment
from prompts import TASK_1_PROMPT, TASK_2_PROMPT, LINKEDIN_OUTREACH

###### TASK 1 #######
def generate_justification_azure(resume_text, job_payload, score, model_deployment=azure_chat_deployment):
    """Generates justification using Azure OpenAI ChatCompletion."""
    try:
        resume_snippet = resume_text # Increase snippet size slightly
        job_text = job_payload.get('text', 'N/A') if job_payload else 'N/A'
        job_snippet = job_text

        prompt = TASK_1_PROMPT.format(
            resume_snippet=resume_text,
            role=job_payload.get('name', 'N/A') if job_payload else 'N/A',
            company=job_payload.get('company', 'N/A') if job_payload else 'N/A',
            job_source=job_payload.get('source', 'N/A') if job_payload else 'N/A',
            job_snippet=job_snippet,
            assigned_score=score,
            fit_score=score,
            justified_score=score,
            limited_score=score
        )
        response = azure_client.chat.completions.create(
            model=model_deployment,
            messages=[
                {"role": "system", "content": "You are an expert recruitment assistant helping to explain job matches."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=512
        )
        justification = response.choices[0].message.content.strip()
        return justification
    except Exception as e:
        print(f"Error generating justification via Azure: {e}")
        return "Could not generate justification due to an API error."
    
    
###### TASK 2 #######
def generate_candidate_justification_azure(candidate_summary, job_summary, score, score_details, model_deployment=azure_chat_deployment):
    """Generates justification for a candidate match using Azure OpenAI."""
    try:
        # Format score details for the prompt
        details_str = "\n".join([f"- {key.replace('_', ' ').title()}: {value}" for key, value in score_details.items()])

        prompt = TASK_2_PROMPT.format(
            candidate_summary.get('name', 'Candidate'),
            candidate_summary.get('current_title', 'your current role'),
            candidate_summary.get('location', 'your location'),
            candidate_summary.get('years_of_experience', 'N/A'),
            ', '.join(candidate_summary.get('skills', [])),
            candidate_summary.get('linkedin_url', 'N/A'),
            job_summary.get('Role', 'an exciting role'),
            job_summary.get('Company', 'our company'),
            job_summary.get('YOE', 'N/A'),
            job_summary.get('Requirements', ''),
            job_summary.get('Tech Stack', ''),
            score,
            details_str,
            score
        )

        response = azure_client.chat.completions.create(
            model=model_deployment,
            messages=[
                {"role": "system", "content": "You are an expert recruitment assistant explaining candidate-job fit."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=100
        )
        justification = response.choices[0].message.content.strip()
        return justification
    except Exception as e:
        print(f"Error generating justification via Azure: {e}")
        return "Could not generate justification due to an API error."
    

def generate_linkedin_message_azure(candidate_summary, job_summary, model_deployment=azure_chat_deployment):
    """Generates a concise LinkedIn outreach message using Azure OpenAI."""
    try:
        
        prompt = LINKEDIN_OUTREACH.format(
            candidate_summary.get('name', 'Candidate'),
            candidate_summary.get('current_title', 'your current role'),
            ', '.join(candidate_summary.get('skills', [])),
            job_summary.get('Role', 'an exciting role'),
            job_summary.get('Company', 'our company'),
            job_summary.get('Requirements', ''),
            job_summary.get('Tech Stack', ''),
            candidate_summary.get('name', 'Candidate'),
            job_summary.get('Role', 'role'),
            job_summary.get('Company', 'our company')
        )

        response = azure_client.chat.completions.create(
            model=model_deployment,
            messages=[
                {"role": "system", "content": "You are a friendly recruiter drafting concise LinkedIn outreach messages. It should not be more than 250 characters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, 
            max_tokens=70 
        )
        message = response.choices[0].message.content.strip()
        return message[:250]
    except Exception as e:
        print(f"Error generating LinkedIn message via Azure: {e}")
        return "Could not generate message due to an API error."