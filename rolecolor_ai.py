import argparse
import math
import os
import re
from groq import Groq

# ----------------------------
# RoleColor keyword framework
# ----------------------------
ROLECOLOR_KEYWORDS = {
    "Builder": [
        "strategy","vision","innovation","architect","architecture","system design","design",
        "scalable","scalability","platform","framework","prototype","research","model","modeling","algorithm"
    ],
    "Thriver": [
        "fast-paced","rapid","quickly","deadline","deadlines","under pressure","ambiguous","ambiguity",
        "ownership","accountable","deliver","delivered","shipped","ship","launch","launched","execution",
        "urgent","iterate","iteration","iterative","go-live"
    ],
    "Enabler": [
        "collaborate","collaborated","collaboration","cross-functional","partner","partnering",
        "stakeholder","stakeholders","align","alignment","coordinate","coordination",
        "communicate","communication","influence","facilitate","facilitation","consensus",
        "bridge","unblock","unblocked","requirements","translate","mentor","mentorship","coaching","enablement"
    ],
    "Supportee": [
        "reliability","reliable","maintain","maintained","maintenance","monitoring","observability",
        "incident","on-call","uptime","stability","stable","documentation","documented","runbook",
        "testing","tests","quality","compliance","security","refactor","refactoring",
        "performance","optimize","optimized","optimization","best practices","reproducible","migration"
    ]
}

# Groq model: use a current production model by default (configurable via env var)
# See Groq "Supported Models" docs for latest model IDs.
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FALLBACK_GROQ_MODEL = os.getenv("GROQ_MODEL_FALLBACK", "llama-3.1-8b-instant")

def normalize(text: str) -> str:
    text = text.lower()
    # keep arrows like 0->1 / 0→1; remove most punctuation
    text = re.sub(r"[^\w\s→\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def count_keyword_hits(text_norm: str, keywords):
    """
    Counts boundary-ish matches for each keyword/phrase, returns:
    - total_raw_count
    - hit_map {keyword: hits}
    """
    total = 0
    hits = {}
    for kw in keywords:
        kw_n = normalize(kw)
        pattern = r"(?:^|\s)" + re.escape(kw_n) + r"(?:$|\s)"
        n = len(re.findall(pattern, text_norm))
        if n > 0:
            hits[kw] = n
            total += n
    return total, hits

def score_resume(text: str):
    """
    Returns:
      - normalized score distribution
      - per-role hit maps used for explainability
    """
    text_n = normalize(text)

    raw = {}
    hit_maps = {}

    for role, kws in ROLECOLOR_KEYWORDS.items():
        count, hits = count_keyword_hits(text_n, kws)

        # Phrase emphasis: phrases carry more signal than single tokens
        phrase_bonus = 0.0
        for k, n in hits.items():
            if " " in k or "->" in k or "→" in k:
                phrase_bonus += 1.2 * n
        raw_score = count + phrase_bonus

        # Dampen keyword stuffing
        raw[role] = math.log1p(raw_score)
        hit_maps[role] = hits

    total = sum(raw.values())
    if total == 0:
        dist = {k: 0.25 for k in raw}
    else:
        dist = {k: round(v / total, 3) for k, v in raw.items()}

    return dist, hit_maps

def dominant(scores):
    return max(scores, key=scores.get)

def explain_rolecolor(scores, hit_maps, top_k=5):
    dom = dominant(scores)
    role_hits = hit_maps.get(dom, {})

    top = sorted(role_hits.items(), key=lambda x: x[1], reverse=True)[:top_k]
    keywords = [k for k, _ in top]

    if not keywords:
        return (
            "Why this RoleColor:\n"
            f"The resume most strongly reflects a {dom}-type contributor based on the scoring distribution, "
            "but keyword evidence was limited in the provided text.\n"
        )

    return (
        "Why this RoleColor:\n"
        f"The resume most strongly reflects a {dom}-type contributor.\n\n"
        f"Top linguistic signals: {', '.join(keywords)}\n"
    )

def rewrite_with_llm(text: str, role: str, title: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY environment variable. Set it to run the LLM rewrite.")

    client = Groq(api_key=api_key)

    prompt = f"""
You are a resume-writing assistant for RoleColorAI.
Rewrite a resume summary to emphasize a {role}-type team contributor.

RoleColor definitions:
- Builder: vision, architecture, strategy, innovation, long-term thinking
- Thriver: fast execution, ownership under pressure, ambiguity, shipping
- Enabler: cross-functional alignment, coordination, stakeholder bridging
- Supportee: reliability, stability, documentation, quality, operational excellence

Hard constraints:
- Write EXACTLY 4 to 6 lines (line breaks).
- Professional resume tone.
- Do NOT invent companies, years, tools, or achievements not present in the resume.
- Focus on how the candidate contributes to teams.
- Use the title label: {title}

Resume text:
{text}

Return ONLY the summary (4–6 lines). No bullets, no headings, no extra commentary.
""".strip()

    # Try primary model, then fallback if decommissioned or unavailable.
    for model_id in [DEFAULT_GROQ_MODEL, FALLBACK_GROQ_MODEL]:
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.35,
                max_tokens=220,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            last_err = e

    raise last_err  # surface final error if both fail

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to resume .txt file")
    parser.add_argument("--title", default="Engineer", help="Title label for summary generation")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM rewrite and only print scores/explanation")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    scores, hit_maps = score_resume(text)
    dom = dominant(scores)

    print("\nRoleColor distribution:")
    for k, v in scores.items():
        print(f"  {k:10s}: {v}")

    print(f"\nDominant RoleColor: {dom}\n")
    print(explain_rolecolor(scores, hit_maps))

    if not args.no_llm:
        print("\nRewritten summary (LLM):\n")
        print(rewrite_with_llm(text, dom, args.title))

if __name__ == "__main__":
    main()
