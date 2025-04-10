import pandas as pd
from tabulate import tabulate
import os
from IPython.display import HTML, display

def format_results_for_table(results):
    table_data = []
    
    for result in results:
        resume_name = result['resume_name']
        
        if result['top_matches']:
            for i, match in enumerate(result['top_matches']):
                table_data.append({
                    'Resume': resume_name if i == 0 else '',
                    'Job': match['job_details'],
                    'Fit Score': f"{match['fit_score']}/10",
                    'RRF Score': f"{match['rrf_score']:.4f}",
                    'Justification': match['justification']
                })
        else:
            table_data.append({
                'Resume': resume_name,
                'Job': 'No suitable matches found.',
                'Fit Score': 'N/A',
                'RRF Score': 'N/A',
                'Justification': 'N/A'
            })
    
    return table_data

def generate_html_table(data, df):
    # CSS for dark theme
    css = """
    <style>
    .results-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #e1e1e1;
        background-color: #1e1e1e;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        margin: 20px 0;
    }
    
    .results-table th {
        background-color: #333;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 14px;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #444;
    }
    
    .results-table td {
        padding: 10px 16px;
        border-bottom: 1px solid #333;
        vertical-align: top;
    }
    
    .results-table tr:last-child td {
        border-bottom: none;
    }
    
    .results-table tr:nth-child(even) {
        background-color: #282828;
    }
    
    .results-table tr:hover {
        background-color: #2a2a2a;
    }
    
    .fit-score {
        font-weight: bold;
    }
    
    .high-score {
        color: #4caf50;
    }
    
    .medium-score {
        color: #ff9800;
    }
    
    .low-score {
        color: #f44336;
    }
    
    .no-match {
        color: #888;
        font-style: italic;
    }
    
    .resume-name {
        font-weight: bold;
        color: #64b5f6;
    }
    </style>
    """
    
    # HTML table generation
    html = "<html><head><title>Resume Job Matching Results</title>" + css + "</head><body style='background-color: #121212; padding: 20px;'>"
    html += "<h1 style='color: #e1e1e1; text-align: center; margin-bottom: 30px;'>Resume Job Matching Results</h1>"
    html += "<table class='results-table'>"
    
    # Table headers
    html += "<thead><tr>"
    for column in df.columns:
        html += f"<th>{column}</th>"
    html += "</tr></thead><tbody>"
    
    # Table body
    for _, row in df.iterrows():
        html += "<tr>"
        
        for i, col in enumerate(df.columns):
            value = row[col]
            
            if col == 'Resume' and value:
                html += f"<td class='resume-name'>{value}</td>"
            elif col == 'Job' and value == 'No suitable matches found.':
                html += f"<td class='no-match'>{value}</td>"
            elif col == 'Fit Score':
                if value == 'N/A':
                    html += f"<td class='no-match'>{value}</td>"
                else:
                    score = float(value.split('/')[0])
                    class_name = 'high-score' if score >= 8 else 'medium-score' if score >= 6 else 'low-score'
                    html += f"<td class='fit-score {class_name}'>{value}</td>"
            else:
                html += f"<td>{value}</td>"
                
        html += "</tr>"
    
    html += "</tbody></table></body></html>"
    return html


#### TASK 2 #####

def generate_task2_html_table(df, output_filename):
    """Generates an HTML table with dark theme for Task 2 results and saves it."""

    css = """
    <style>
    body {
        background-color: #121212;
        color: #e1e1e1;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        padding: 20px;
    }
    h1 {
        color: #e1e1e1;
        text-align: center;
        margin-bottom: 30px;
    }
    .results-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #1e1e1e;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        margin: 20px 0;
    }
    .results-table th {
        background-color: #333;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 12px; /* Smaller font for header */
        letter-spacing: 0.5px;
        border-bottom: 2px solid #444;
    }
    .results-table td {
        padding: 10px 16px;
        border-bottom: 1px solid #333;
        vertical-align: top;
        font-size: 14px; /* Standard font size for data */
    }
    .results-table tr:last-child td {
        border-bottom: none;
    }
    .results-table tr:nth-child(even) {
        background-color: #282828;
    }
    .results-table tr:hover {
        background-color: #2a2a2a;
    }
    .fit-score {
        font-weight: bold;
        text-align: center; /* Center score */
    }
    .rank {
        font-weight: bold;
        text-align: center;
        color: #bb86fc; /* Highlight rank */
    }
    .high-score { color: #4caf50; } /* Green for high scores */
    .medium-score { color: #ffeb3b; } /* Yellow for medium scores */
    .low-score { color: #f44336; } /* Red for low scores */
    .candidate-name {
        font-weight: bold;
        color: #64b5f6; /* Light blue for name */
    }
    .linkedin-link a {
        color: #03dac6; /* Teal for links */
        text-decoration: none;
    }
    .linkedin-link a:hover {
        text-decoration: underline;
    }
    .justification {
        font-size: 13px; /* Slightly smaller for justification */
        color: #b0b0b0; /* Lighter gray for justification */
    }
    .message {
         font-size: 13px;
         font-style: italic;
         color: #9e9e9e;
    }
    </style>
    """

    html = f"<html><head><title>Top Candidate Matches</title>{css}</head><body>"
    html += "<h1>Top Candidate Matches</h1>"
    html += "<table class='results-table'>"

    html += "<thead><tr>"
    headers = ['Rank', 'Name', 'LinkedIn', 'Score', 'Why (Justification)', 'LinkedIn Message (Optional)']
    for header in headers:
        html += f"<th>{header}</th>"
    html += "</tr></thead><tbody>"

    for _, row in df.iterrows():
        html += "<tr>"
        html += f"<td class='rank'>{row.get('Rank', 'N/A')}</td>"
        html += f"<td class='candidate-name'>{row.get('Name', 'N/A')}</td>"
        linkedin_url = row.get('LinkedIn', '')
        if linkedin_url and isinstance(linkedin_url, str) and linkedin_url.startswith('http'):
            html += f"<td class='linkedin-link'><a href='{linkedin_url}' target='_blank'>{linkedin_url}</a></td>"
        else:
            html += f"<td>{linkedin_url if linkedin_url else 'N/A'}</td>"
        score = row.get('Score', 0.0)
        if score == 'N/A':
             score_val = 0
             score_display = 'N/A'
        else:
            try:
                score_val = float(score)
                score_display = f"{score_val:.1f}/10"
            except ValueError:
                score_val = 0
                score_display = 'N/A'

        class_name = 'high-score' if score_val >= 8 else 'medium-score' if score_val >= 6 else 'low-score'
        html += f"<td class='fit-score {class_name}'>{score_display}</td>"
        html += f"<td class='justification'>{row.get('Why', 'N/A')}</td>"
        html += f"<td class='message'>{row.get('LinkedIn Message (Optional)', '')}</td>"
        html += "</tr>"

    html += "</tbody></table></body></html>"
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Results successfully saved to {output_filename}")
    except Exception as e:
        print(f"Error saving HTML file: {e}")
    return html