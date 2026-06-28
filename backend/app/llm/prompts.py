"""
Centralised prompt templates for every LLM chain in the app.

What it does:
- Holds the 5 .format()-style prompt strings used across the pipeline.
- Keeps prompts in one place so wording can be tuned without touching business logic.
- JSON-producing prompts end with "Return ONLY valid JSON" to keep safe_parse_json happy.

Upstream (who imports this): app/llm/chains.py
Downstream (what this imports): nothing — pure string constants
"""


EXTRACT_SKILLS_PROMPT = """You are an expert resume analyzer. Extract structured information from the resume text below.

Resume Text:
{resume_text}

Return a JSON object with this exact structure:
{{
  "name": "full name or null",
  "email": "email or null",
  "phone": "phone or null",
  "location": "city/country or null",
  "summary": "2-3 sentence professional summary",
  "skills": ["skill1", "skill2", ...],
  "education": [
    {{
      "institution": "university name",
      "degree": "degree type",
      "field": "field of study",
      "graduation_year": "year or null"
    }}
  ],
  "experience": [
    {{
      "company": "company name",
      "role": "job title",
      "duration": "e.g. Jun 2023 - Present",
      "description": "brief description",
      "skills_used": ["skill1", ...]
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": "what it does",
      "technologies": ["tech1", ...]
    }}
  ],
  "years_of_experience": 0.5,
  "experience_level": "intern|entry|mid|senior"
}}

Focus on technical skills: programming languages, frameworks, AI/ML tools, cloud platforms, databases.
Return ONLY valid JSON, no markdown fences."""


RANK_JOBS_PROMPT = """You are an expert career advisor and technical recruiter.

Candidate Skills: {candidate_skills}
Candidate Experience Level: {experience_level}

Evaluate this job opportunity:
Title: {job_title}
Company: {job_company}
Required Skills: {job_skills}
Description: {job_description}

Return a JSON object:
{{
  "matched_skills": ["skills the candidate has that match"],
  "missing_skills": ["required skills the candidate lacks"],
  "fit_score": 0-100,
  "recommendation": "strong_match|good_match|partial_match|weak_match"
}}

Return ONLY valid JSON."""


EXPLAIN_MATCH_PROMPT = """You are a career coach explaining job fit to a candidate.

Candidate Profile:
- Skills: {candidate_skills}
- Experience: {experience_level}
- Summary: {candidate_summary}

Job: {job_title} at {job_company}
Matched Skills: {matched_skills}
Missing Skills: {missing_skills}
Similarity Score: {similarity_score}%

Write a concise, encouraging 3-4 sentence explanation of:
1. Why this job is a good fit
2. What skills the candidate brings
3. What they should learn to improve their chances

Be specific and actionable. Do not use bullet points."""


IMPROVEMENT_SUGGESTIONS_PROMPT = """You are a senior engineering career mentor.

Candidate's top missing skills across all job matches: {missing_skills}
Candidate's current skills: {current_skills}
Target roles: {target_roles}

Provide exactly 5 specific, actionable improvement suggestions.
Format as a JSON array of strings:
["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4", "suggestion 5"]

Each suggestion should name a specific technology, course, or project to build.
Return ONLY valid JSON."""


OVERALL_SUMMARY_PROMPT = """You are a career advisor summarizing a job search analysis.

Candidate Experience Level: {experience_level}
Number of jobs analyzed: {job_count}
Top match percentage: {top_match}%
Average match percentage: {avg_match}%
Most common missing skills: {missing_skills}

Write a 2-3 sentence overall summary of the candidate's job market readiness.
Be honest but encouraging. Mention their strongest alignment areas.
Return plain text, no JSON."""
