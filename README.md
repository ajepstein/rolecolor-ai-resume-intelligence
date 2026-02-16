
# RoleColorAI Take-Home — NLP Prototype

## Overview
This prototype analyzes a resume through a **team-role lens** rather than job titles.

It:
1. Scores a resume across four RoleColors (Builder, Thriver, Enabler, Supportee)
2. Outputs a normalized RoleColor distribution
3. Uses a free public LLM (Llama 3 via Groq) to rewrite a resume summary aligned to the dominant RoleColor

The goal is to demonstrate practical NLP + applied LLM integration in a lightweight, explainable way.

---

# Approach Explanation

## 1. RoleColor Keyword Framework
Each RoleColor represents a different team contribution style:

- **Builder** → strategy, architecture, innovation, systems thinking  
- **Thriver** → speed, ownership under pressure, execution  
- **Enabler** → cross‑functional collaboration and alignment  
- **Supportee** → reliability, quality, stability and documentation  

A curated keyword + phrase lexicon was created for each RoleColor based on:
- common resume language
- leadership/teamwork vocabulary
- how recruiters evaluate contribution styles

Multi‑word phrases are weighted higher than single words because they carry stronger signal.

---

## 2. Resume Scoring Logic

Steps:
1. Resume text is normalized (lowercase, punctuation removed)
2. Text is split into sections (summary, experience, projects, skills)
3. Keyword/phrase matches counted per RoleColor
4. Section weighting applied:
   - Summary / experience weighted higher
   - Skills weighted lower
5. Log scaling applied to reduce keyword stuffing impact
6. Scores normalized to produce a distribution summing to 1.0

Output example:
Builder: 0.42  
Enabler: 0.31  
Thriver: 0.18  
Supportee: 0.09  

This keeps scoring explainable and auditable.

---

## 3. Resume Rewrite Using LLM

After scoring:
- The dominant RoleColor is selected
- An evidence pack is extracted:
  - strongest matching keywords
  - strongest experience lines
- A constrained prompt is sent to a free public LLM (Llama 3 via Groq)

Constraints:
- 4–6 lines
- grounded only in resume evidence
- recruiter‑friendly tone
- emphasize dominant RoleColor contribution

This ensures the generation is aligned and avoids hallucinated claims.

---

# How to Run the Code

## 1. Install dependencies
pip install -r requirements.txt

## 2. Get free Groq API key
Create free account:
https://console.groq.com

Set key:
export GROQ_API_KEY="your_key_here"

## 3. Run script
python rolecolor_ai.py --input sample_resume.txt --title "AI/ML Engineer"

---

# Assumptions Made

1. Resume provided as plain text (.txt)
2. Keyword‑based scoring sufficient for prototype
3. Resume language reflects contribution style
4. LLM rewrite must remain grounded in evidence
5. System optimized for clarity and explainability over ML accuracy
6. No frontend required — CLI output sufficient

---

# Possible Future Improvements

- Embedding similarity instead of pure keyword match
- Trained classifier on labeled resumes
- RoleColor detection per experience section
- Web UI for interactive upload + rewrite
- Recruiter dashboard for candidate comparison
---

## Senior-level Touches Included

### 1) Explainability (“Why this RoleColor?”)
In addition to the score distribution, the script prints a short explanation showing the **top matched signals** (keywords/phrases)
that most contributed to the dominant RoleColor. This makes the scoring decision more interpretable and recruiter-friendly.

### 2) Production evolution path
The README includes a clear upgrade path from this keyword prototype to a more robust ML/LLM system (embeddings, classifier, grounded rewrite).

---

## How this would evolve into a production ML system

If scaled beyond a prototype, I would:

1. **Replace keyword scoring with embedding similarity**
   - Use sentence-transformers to compare resume text with RoleColor descriptors
   - Captures semantic matches beyond literal keyword overlap

2. **Train a lightweight classifier**
   - Label a starter dataset (e.g., ~500 resumes with RoleColor blends)
   - Train logistic regression / gradient boosting on embeddings, or a small transformer classifier
   - Output probabilistic RoleColor mix with calibration

3. **Strengthen grounding for LLM rewrite**
   - Retrieve highest-signal resume lines (already implemented as an “evidence pack”)
   - Constrain generation to evidence-only content and add automated checks (length, claim novelty)

4. **Recruiter-facing workflow**
   - Upload resume → show RoleColor distribution + explanation
   - Generate role-aligned summaries per job family
   - Compare candidates by RoleColor blend for team-fit analysis

## Optional: Select Groq model
Groq model IDs can change over time. By default this project uses a current production model and falls back automatically.

You can override the model(s) with:
```bash
export GROQ_MODEL="llama-3.3-70b-versatile"
export GROQ_MODEL_FALLBACK="llama-3.1-8b-instant"
```
