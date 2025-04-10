TASK_1_PROMPT = """
**Objective:** Analyze the provided resume snippet against the job details to explain the assigned Fit Score. Your explanation should be concise, evidence-based, and directly link elements from the resume to the job requirements.

**Context:** You are assessing the suitability of a candidate for a specific job opening based on limited information.

**Inputs:**

1.  **Candidate Resume Snippet:**
    ```text
    {resume_snippet}
    ```
    *This snippet contains selected highlights from the candidate's resume.*

2.  **Job Details:**
    * **Role:** {role}
    * **Company:** {company}
    * **Job Source:** {job_source}
    * **Job Description Snippet:**
        ```text
        {job_snippet}
        ```
        *This snippet contains selected requirements or responsibilities from the full job description.*

3.  **Assigned Fit Score:** {assigned_score}/10
    *This score represents an estimated level of alignment between the resume and the job.*

**Task:**

Based *only* on the information provided in the **Resume Snippet** and the **Job Description Snippet**:

1.  Identify the **most critical overlapping keywords, skills, technologies, qualifications, or experiences** present in *both* snippets.
2.  Also, note any obvious **key requirements mentioned in the job description that seem absent** in the resume snippet, especially if the score is not high.
3.  Write a brief explanation (strictly 1-3 sentences) justifying the **Fit Score ({fit_score}/10)**.
4.  Your explanation **must cite specific examples** of matches (or significant mismatches if applicable) found in the text snippets to support the reasoning. For instance, "The score of {justified_score} is justified because the resume mentions proficiency in 'Skill X' and 'Technology Y', directly matching key requirements listed in the job description." Or, for a lower score: "While the resume shows 'Experience A', the score is limited to {limited_score} because the job explicitly requires 'Skill B' which is not mentioned in the provided snippet."

**Output Format:**

Provide *only* the concise justification sentences as requested. Do not repeat the inputs. Focus on clarity and direct evidence from the snippets.
"""

TASK_2_PROMPT = """
**Objective:** Generate a concise justification for the calculated Fit Score by analyzing the provided candidate and job summaries, paying close attention to the factors outlined in the score breakdown.

**Inputs:**

1.  **Candidate Summary:**
    * Name: {}
    * Title: {}
    * Location: {}
    * Years of Experience (YOE): {}
    * Skills Snippet: {}...
    * LinkedIn: {}

2.  **Job Summary:**
    * Role: {}
    * Company: {}
    * Required YOE: {}
    * Tech Stack/Requirements Snippet: {}... {}...

3.  **Calculated Fit Score:** {}/10

4.  **Key Factors Influencing Score (Score Breakdown Hints):**
    ```text
    {}
    ```
    *(This section provides specific reasons contributing to the score, like matching skills, YOE alignment, identified gaps, etc.)*

**Task:**

1.  **Analyze:** Carefully compare the **Candidate Summary** (especially YOE and Skills Snippet) against the **Job Summary** (especially Required YOE and Requirements/Tech Stack Snippet).
2.  **Correlate:** Use the **Key Factors Influencing Score** to understand the *primary reasons* behind the calculated **Fit Score ({}/10)**.
3.  **Synthesize:** Based on the most significant points of alignment (or misalignment) highlighted by the analysis and the key factors, formulate a brief justification (strictly 1-2 sentences).
4.  **Justify:** Your justification must explicitly reference 1-2 *specific examples* of matching factors (e.g., "matching YOE", "presence of 'Skill X'") or key differentiating factors (e.g., "lacks required 'Technology Y'") derived from the inputs and mentioned or implied in the Key Factors, to explain *why* the score is what it is.

**Output Requirements:**

* Provide only the 1-2 sentence justification.
* Do not include introductory phrases like "The justification is...".
* Focus on connecting specific evidence from the summaries and key factors directly to the score.
"""

LINKEDIN_OUTREACH = """
**Objective:** Craft a highly concise, personalized, and professional LinkedIn outreach message to a specific candidate regarding a relevant job opportunity, adhering to a strict character limit.

**Context:** You are initiating contact on LinkedIn to gauge a candidate's interest in a new role. The message needs to quickly capture attention and convey relevance.

**Inputs:**

1.  **Candidate Information:**
    * Name: {}
    * Current Title: {}
    * Skills Snippet: {}... *(A list highlighting some of the candidate's skills)*

2.  **Job Information:**
    * Target Role: {}
    * Hiring Company: {}
    * Job Key Requirements Snippet: {}... *(Highlights of essential requirements)*
    * Job Tech Stack Snippet: {}... *(Key technologies used in the role)*

**Task:**

1.  **Identify Strongest Link:** Analyze the Candidate's Title and Skills Snippet against the Job's Requirements and Tech Stack Snippets. Pinpoint **one clear, specific point of alignment** (e.g., a prominent skill listed by the candidate that matches a key job requirement, or how their current title relates directly to the target role).
2.  **Draft Outreach Message:** Compose a LinkedIn message adhering to the following:
    * **Recipient:** Address {}.
    * **Personalization:** Explicitly mention the *specific alignment point* identified above (e.g., "Noticed your experience with [Specific Skill/Tech]" or "Your background as a [Candidate Title] looks relevant...").
    * **Opportunity:** Briefly introduce the {} position at {}.
    * **Call to Action (CTA):** Include a concise and clear CTA, like "Open to a quick chat?" or "Interested in hearing more?".
    * **Tone:** Maintain a professional, respectful, and inviting tone.

**Constraints & Output Requirements:**

* **Maximum Length:** The *entire* generated message must **not exceed 250 characters**. Brevity is crucial.
* **Format:** Provide *only* the text of the LinkedIn message. Do not add any explanations, labels, or introductory text.

"""