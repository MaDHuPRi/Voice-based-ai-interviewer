def build_prompt(jd_text, resume_text, n_tech, n_behav, difficulty, include_answers):
    return f"""
You are an expert technical interviewer and hiring manager.

Your job is to create a structured interview-preparation report for the candidate based on their resume and the provided job description.

======================================================

🎯 **STRICT OUTPUT FORMAT (Format B)**  
Do NOT output JSON.  
Do NOT create custom formats.  
Do NOT change section titles.  
Follow EXACTLY the structure below:

======================================================

### Candidate Fit Summary
- Strong fit: <3–5 bullet points about what makes this candidate a good match>
- Weak fit: <2–4 bullet points of gaps or risks>

---

### Generate EXACTLY {n_tech} distinct technical interview questions.
Number them clearly from 1 to {n_tech}.
Each question must be complete and self-contained.
Do NOT include instructional text, placeholders, or repetition notes.

For EACH technical question, use this format:

1. <Question text tailored to the JD and resume>
- Difficulty: <easy / medium / hard — matching target: {difficulty}>
- Follow-up: <one follow-up question>
{"- Expected Answer Outline:\n  - Key point 1\n  - Key point 2\n  - Key point 3" if include_answers else ""}

---

### Behavioral Questions
If {n_behav} > 0, generate EXACTLY {n_behav} distinct behavioral interview questions.
Number them clearly from 1 to {n_behav}.
Each question MUST include one follow-up question.
Do NOT include instructional text, placeholders, or repetition notes.

For EACH behavioral question, use this format:

1. <Behavioral question tailored to the role responsibilities>
- Follow-up: <a deeper probing follow-up>

======================================================

🎯 **Additional Requirements**
- Questions MUST be tailored to the candidate's resume experience.
- Questions MUST match the job description’s domain.
- Keep questions concise and practical.
- Follow the exact markdown structure above.
- Do NOT include JSON, YAML, tables, or code blocks.

IMPORTANT EXPERIENCE COVERAGE RULES:

- At least 2 technical questions MUST be explicitly based on the candidate’s projects or prior work experience.
- These questions should reference:
  • A specific project, system, or tool mentioned in the resume
  • OR a concrete responsibility from a past role

- At least 1 question SHOULD focus on a project end-to-end, such as:
  • problem definition
  • design choices
  • trade-offs
  • challenges or limitations
  • impact or results

- Do NOT limit questions only to the most recent role.
- When possible, vary questions across different projects or experiences listed in the resume.

======================================================

### JOB DESCRIPTION
{jd_text}

### RESUME
{resume_text}

======================================================

Now generate the final formatted interview preparation following ALL rules above.
"""
