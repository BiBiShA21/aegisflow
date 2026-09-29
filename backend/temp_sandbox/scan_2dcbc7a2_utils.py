import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

STATE_LABELS = {
    0: "🟢 Focused",
    1: "🟡 Struggling",
    2: "🔴 Overloaded"
}

def get_ai_suggestion(state: int, typing_speed: float,
                       error_rate: float, avg_pause: float) -> str:
    """Call Groq and get a helpful suggestion based on cognitive state."""

    if state == 0:
        return "✅ You're in the zone! Keep going! 🔥"

    state_desc = STATE_LABELS[state]

    prompt = f"""You are CodeSense, an AI productivity coach for developers.

A developer's real-time coding stats for the last 30 seconds:
- Cognitive state: {state_desc}
- Typing speed: {typing_speed:.2f} keys/second
- Error rate: {error_rate:.2f} (backspaces / total keys)
- Average pause: {avg_pause:.2f} seconds

Give a SHORT (2-3 sentences), friendly, and practical suggestion
to help them. Be encouraging, not discouraging.
If overloaded, suggest a break or simplification strategy.
If struggling, suggest a debugging tip or rubber duck technique."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"API Error: {e}")
        fallback = {
            1: "🟡 Slow down and re-read the problem. Try explaining it out loud!",
            2: "🔴 Time for a 5 min break! Stretch, drink water, come back fresh. 💧"
        }
        return fallback.get(state, "Keep going!")


def test_suggestion():
    """Quick test to make sure API is working."""
    print("Testing AI suggestions...\n")

    print("State: Struggling")
    print(get_ai_suggestion(1, 3.2, 0.35, 1.8))
    print()

    print("State: Overloaded")
    print(get_ai_suggestion(2, 0.5, 0.6, 5.2))

def calculate_focus_score(df: pd.DataFrame) -> int:
    """Calculate a 0-100 focus score for the entire session."""
    if len(df) == 0:
        return 0

    import pandas as pd

    # Score each window
    scores = []
    for _, row in df.iterrows():
        score = 100

        # Penalise high error rate
        score -= min(row["error_rate"] * 100, 30)

        # Penalise long pauses
        score -= min(row["avg_pause"] * 5, 30)

        # Reward fast typing
        score += min(row["typing_speed"] * 2, 20)

        # Penalise high click rate (distraction)
        score -= min(row["click_rate"] * 20, 20)

        scores.append(max(0, min(100, score)))

    return int(sum(scores) / len(scores))
if __name__ == "__main__":
    test_suggestion()