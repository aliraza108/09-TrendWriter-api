"""
Content Generation Agent
Uses the openai-agents SDK (Gemini backend) — same pattern as your scraper.
Provides:
  • generate_post_variants()  → list of content variants
  • score_content()           → predicted engagement score
  • detect_trends()           → trending topics for a niche
"""
from __future__ import annotations
import json
from agents import Agent, Runner, function_tool


# ── Tools ──────────────────────────────────────────────────────────────────────
@function_tool
async def analyze_hook_strength(hook: str) -> dict:
    """
    Analyze the strength of a LinkedIn post hook.
    Returns a score 0–10 and improvement suggestions.
    """
    # Heuristic scoring (replace with LLM sub-call if desired)
    score = 0
    tips = []
    if len(hook) < 10:
        tips.append("Too short — add intrigue or a bold claim.")
    if any(w in hook.lower() for w in ["you", "your", "i ", "we "]):
        score += 2
    if "?" in hook:
        score += 2
    if any(w in hook.lower() for w in ["mistake", "secret", "truth", "surprising", "nobody"]):
        score += 3
    if len(hook.split()) <= 15:
        score += 3
    score = min(score, 10)
    return {"score": score, "tips": tips}


# ── Agents ─────────────────────────────────────────────────────────────────────
trend_agent = Agent(
    name="TrendDetector",
    instructions="""
You are a LinkedIn trend analyst. Given a professional niche, identify the
top 5–8 trending discussion topics RIGHT NOW on LinkedIn for that niche.

Return ONLY valid JSON (no markdown fences), structured as:
{
  "trends": [
    {"topic": "...", "reason": "...", "urgency": "high|medium|low"},
    ...
  ]
}
""",
)

content_agent = Agent(
    name="ContentWriter",
    tools=[analyze_hook_strength],
    instructions="""
You are a LinkedIn ghostwriter and growth strategist.
Generate high-performing LinkedIn posts.

Rules:
- Hook: ≤15 words, pattern-interrupt, stops the scroll
- Body: value-packed, white space friendly, NO jargon
- CTA: single clear ask (comment / save / follow / DM)
- Hashtags: 3–5 relevant, mix of broad + niche
- Tone options: professional | conversational | storytelling | bold

Return ONLY valid JSON (no markdown fences):
{
  "variants": [
    {
      "variant_id": "v1",
      "hook": "...",
      "body": "...",
      "cta": "...",
      "hashtags": ["...", "..."],
      "predicted_score": 7.4
    }
  ]
}
""",
)

strategy_agent = Agent(
    name="StrategyAdvisor",
    instructions="""
You are a LinkedIn growth strategist.
Given a user's niche, posting history, and engagement data:
1. Recommend content topics for next 7 days
2. Suggest best posting times (day + hour)
3. Identify best-performing formats
4. Give tone/style recommendations

Return ONLY valid JSON (no markdown fences):
{
  "recommended_topics": [...],
  "recommended_formats": [...],
  "best_times": ["Tuesday 10:00", "Thursday 08:30"],
  "tone_suggestions": "...",
  "content_calendar_preview": [
    {"day": "Mon", "topic": "...", "format": "..."}
  ],
  "insights": "..."
}
""",
)


# ── Public helpers ──────────────────────────────────────────────────────────────
async def detect_trends(niche: str) -> list[dict]:
    """Return trending topics for a given niche."""
    result = await Runner.run(
        trend_agent,
        input=f"Niche: {niche}. Find trending LinkedIn topics NOW.",
    )
    raw = result.final_output or "{}"
    try:
        data = json.loads(raw)
        return data.get("trends", [])
    except json.JSONDecodeError:
        return [{"topic": raw[:100], "reason": "parse error", "urgency": "low"}]


async def generate_post_variants(
    topic: str,
    niche: str,
    format_type: str,
    tone: str,
    target_audience: str,
    num_variants: int = 3,
) -> dict:
    """Generate N content variants for a topic."""
    prompt = (
        f"Niche: {niche}\n"
        f"Target audience: {target_audience}\n"
        f"Topic: {topic}\n"
        f"Format: {format_type}\n"
        f"Tone: {tone}\n"
        f"Generate {num_variants} distinct variants."
    )
    result = await Runner.run(content_agent, input=prompt)
    raw = result.final_output or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"variants": []}


async def get_strategy_recommendations(
    niche: str,
    recent_performance: dict,
    user_prefs: dict,
) -> dict:
    """Generate strategic content recommendations."""
    prompt = (
        f"Niche: {niche}\n"
        f"Recent performance summary: {json.dumps(recent_performance)}\n"
        f"User preferences: {json.dumps(user_prefs)}\n"
        f"Generate a 7-day LinkedIn content strategy."
    )
    result = await Runner.run(strategy_agent, input=prompt)
    raw = result.final_output or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "recommended_topics": [],
            "recommended_formats": ["thought_leadership"],
            "best_times": ["Tuesday 10:00", "Thursday 08:30"],
            "tone_suggestions": "Professional and authentic.",
            "content_calendar_preview": [],
            "insights": raw[:300],
        }
