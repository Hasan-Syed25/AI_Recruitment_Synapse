import fitz
import pandas as pd
import re
import uuid
import os
from rank_bm25 import BM25Okapi


def load_paraform_jobs(csv_path):
    """Loads jobs from the Paraform CSV and prepares for indexing."""
    try:
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df)} jobs from CSV: {csv_path}")
        jobs = []
        for _, row in df.iterrows():
            # Combine relevant text fields for matching
            combined_text = (
                f"Role: {row.get('Role', '')}. "
                f"Company: {row.get('Company', '')}. "
                f"One Liner: {row.get('One liner', '')}. "
                f"Requirements: {row.get('Requirements', '')}. "
                f"Tech Stack: {row.get('Tech Stack', '')}"
            )
            job_id = f"Paraform_{uuid.uuid4()}" # Unique ID for Qdrant
            job_name = row.get('Role', 'N/A').replace(" ", "_").replace("/", "_")
            job_name = re.sub(r'[^a-zA-Z0-9_]', '', job_name)  # Remove special characters
            jobs.append({
                'id': job_id,
                'name': job_name,
                'text': combined_text,
                'source': 'Paraform',
                'company': row.get('Company', 'N/A'),
                'role': row.get('Role', 'N/A'),
                'payload': { # Data to store in Qdrant payload
                    "text": combined_text,
                    "source": "Paraform",
                    "company": row.get('Company', 'N/A'),
                    "role": row.get('Role', 'N/A'),
                    "link": row.get('Link', ''),
                    "locations": row.get('Locations', ''),
                    "tech_stack": row.get('Tech Stack', ''),
                    "salary": row.get('Salary', ''),
                    "yoe": row.get('YOE', '')
                }
            })
        return jobs
    except FileNotFoundError:
        print(f"Error: Paraform Job CSV not found at {csv_path}")
        return []
    except Exception as e:
        print(f"Error reading Paraform Job CSV: {e}")
        return []

def extract_srn_jobs_from_text(full_text, job_name):
    """Extracts structured job info from SRN PDF text based on example."""
    job_blocks = re.split(r'(?=ID: SRN\d{4}-\d+)', full_text)
    extracted_jobs = []
    print(f"Attempting to parse SRN jobs. Found {len(job_blocks)} potential blocks.")

    for block in job_blocks:
        block = block.strip()
        if not block or len(block) < 100: # Skip empty or very short blocks
            continue

        job_data = {'source': 'SRN PDF'}
        role_company_match = re.search(r'^(.*?)\n(.*?)\nID:', block, re.MULTILINE | re.DOTALL)
        if role_company_match:
            job_data['role'] = role_company_match.group(1).strip()
            job_data['company'] = role_company_match.group(2).strip()
        else:
             role_lines = re.findall(r'^(?:AI|ML|Software|Data)\s+Engineer.*', block, re.IGNORECASE | re.MULTILINE)
             job_data['role'] = role_lines[0].strip() if role_lines else 'N/A'
             job_data['company'] = 'N/A (SRN PDF)'

        sections = {}
        patterns = {
            'about': r'About the Company:(.*?)(?:Roles and Responsibilities:|Job Requirements:|Interview Process:|$)',
            'responsibilities': r'Roles and Responsibilities:(.*?)(?:Job Requirements:|Interview Process:|$)',
            'requirements': r'Job Requirements:(.*?)(?:X Do NOT Apply If You:|Interview Process:|$)',
            'do_not_apply': r'X Do NOT Apply If You:(.*?)(?:Interview Process:|$)',
            'process': r'Interview Process:(.*?)($)'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
            if match:
                sections[key] = re.sub(r'\s+', ' ', match.group(1).replace('•', '').strip())

        combined_text = (
            f"Role: {job_data.get('role', '')}. "
            f"Company: {job_data.get('company', '')}. "
            f"About: {sections.get('about', '')}. "
            f"Responsibilities: {sections.get('responsibilities', '')}. "
            f"Requirements: {sections.get('requirements', '')}"
        )
        job_data['text'] = combined_text
        job_data['payload'] = {
             "name": job_name,
             "text": combined_text,
             "source": "SRN PDF",
             "company": job_data.get('company', 'N/A'),
             "role": job_data.get('role', 'N/A'),
             "requirements_detail": sections.get('requirements', ''),
             "responsibilities_detail": sections.get('responsibilities', ''),
        }
        extracted_jobs.append(job_data)

    print(f"Extracted {len(extracted_jobs)} potential jobs from SRN PDF text.")
    return extracted_jobs

def parse_pdf_resume(pdf_path):
    """Parse PDF and extract text using PyMuPDF."""
    if not os.path.isfile(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return None
    try:
        doc = fitz.open(pdf_path)
        text = " ".join(page.get_text() for page in doc)
        doc.close()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error parsing PDF {os.path.basename(pdf_path)}: {str(e)}")
        return None

def load_srn_jobs(pdf_path):
    """Loads job descriptions from the SRN PDF using improved parsing."""
    srn_text = parse_pdf_resume(pdf_path)
    job_name = os.path.basename(pdf_path).replace('.pdf', '').replace(" ", "_").replace("/", "_")
    job_name = re.sub(r'[^a-zA-Z0-9_]', '', job_name)  # Remove special characters
    if not srn_text:
        return []
    return extract_srn_jobs_from_text(srn_text, job_name)