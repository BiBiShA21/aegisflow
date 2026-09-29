import streamlit as st
import pandas as pd
import joblib
import time
import os
import firebase_admin
from firebase_admin import credentials, firestore
from utils import get_ai_suggestion, calculate_focus_score

# ── Firebase Setup ────────────────────────────────────────
if not firebase_admin._apps:
    if os.path.exists("firebase_key.json"):
        cred = credentials.Certificate("firebase_key.json")
    else:
        firebase_config = dict(st.secrets["firebase"])
        firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def load_from_firebase():
    """Load all sessions from Firebase into a DataFrame."""
    try:
        docs = db.collection("sessions").order_by("timestamp").limit(50).stream()
        rows = []
        for doc in docs:
            rows.append(doc.to_dict())
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return pd.DataFrame()

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="CodeSense",
    page_icon="🧠",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@300;400;600&display=swap');

#MainMenu { visibility: hidden; }
header { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }
[data-testid="stToolbar"] { display: none; }

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #ffffff;
}

.main {
    background-color: #0a0a0f;
    padding-top: 10px;
}

.block-container {
    padding-top: 20px !important;
    max-width: 1200px;
}

.title-container {
    text-align: center;
    padding: 15px 0 5px 0;
}

.title-text {
    font-family: 'Orbitron', monospace;
    font-size: 2.8em;
    font-weight: 900;
    background: linear-gradient(90deg, #00f5ff, #7b2ff7, #ff006e, #00f5ff);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 4s ease infinite;
    letter-spacing: 5px;
    text-transform: uppercase;
}

@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.subtitle {
    color: #666;
    font-size: 0.75em;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: -5px;
}

.state-card {
    padding: 18px 25px;
    border-radius: 14px;
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.08);
}

.live-badge {
    display: inline-flex;
    align-items: center;
    background: rgba(0,245,255,0.08);
    border: 1px solid rgba(0,245,255,0.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.7em;
    letter-spacing: 2px;
    color: #00f5ff;
}

.pulse {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 7px;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%   { transform: scale(1);   opacity: 1; }
    50%  { transform: scale(1.4); opacity: 0.5; }
    100% { transform: scale(1);   opacity: 1; }
}

div[data-testid="stMetric"] {
    background: #13131f;
    border-radius: 12px;
    padding: 12px 15px;
    border: 1px solid rgba(255,255,255,0.06);
}

div[data-testid="stMetricLabel"] {
    font-size: 0.75em !important;
    color: #888 !important;
    letter-spacing: 1px;
}

div[data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.4em !important;
}

.suggestion-card {
    background: linear-gradient(135deg, #13131f, #1a1a2e);
    border-radius: 14px;
    padding: 20px;
    border: 1px solid rgba(123,47,247,0.25);
    box-shadow: 0 0 25px rgba(123,47,247,0.08);
    height: 100%;
}

.score-container {
    text-align: center;
    padding: 15px;
    background: #13131f;
    border-radius: 14px;
    margin-bottom: 20px;
    border: 1px solid rgba(255,255,255,0.06);
}

.footer-text {
    text-align: center;
    color: #333;
    font-size: 0.7em;
    letter-spacing: 2px;
    padding: 15px 0;
}

.stApp { background-color: #0a0a0f; }
</style>
""", unsafe_allow_html=True)

# ── Load Model ────────────────────────────────────────────
@st.cache_resource
def load_model():
    return joblib.load("models/codesense_model.pkl")

model = load_model()

# ── State Config ──────────────────────────────────────────
STATE_CONFIG = {
    0: {
        "label"  : "FOCUSED",
        "emoji"  : "🟢",
        "color"  : "#00C851",
        "glow"   : "rgba(0,200,81,0.12)",
        "border" : "rgba(0,200,81,0.35)",
        "message": "You're in the zone. Keep crushing it!",
    },
    1: {
        "label"  : "STRUGGLING",
        "emoji"  : "🟡",
        "color"  : "#ffbb33",
        "glow"   : "rgba(255,187,51,0.12)",
        "border" : "rgba(255,187,51,0.35)",
        "message": "Hitting some bumps. You've got this!",
    },
    2: {
        "label"  : "OVERLOADED",
        "emoji"  : "🔴",
        "color"  : "#ff4444",
        "glow"   : "rgba(255,68,68,0.12)",
        "border" : "rgba(255,68,68,0.35)",
        "message": "Brain needs a reset. Time for a break!",
    },
}

# ── Header ────────────────────────────────────────────────
st.markdown("""
<div class='title-container'>
    <div class='title-text'>CodeSense</div>
    <div class='subtitle'>⚡ Real-Time Cognitive Load Monitor ⚡</div>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main Loop ─────────────────────────────────────────────
placeholder = st.empty()
iteration   = 0

while True:
    iteration += 1

    df = load_from_firebase()

    if df.empty:
        with placeholder.container():
            st.markdown("""
            <div style='text-align:center; padding:60px; color:#444;'>
                <div style='font-size:3em;'>⏳</div>
                <div style='font-family:Orbitron; font-size:1em;
                     letter-spacing:3px; margin-top:15px;'>
                     WAITING FOR DATA
                </div>
                <div style='color:#555; margin-top:8px; font-size:0.85em;'>
                    Run tracker.py on your laptop to start
                </div>
            </div>
            """, unsafe_allow_html=True)
        time.sleep(5)
        continue

    # Predict
    latest   = df.iloc[-1]
    features = [[
        latest["typing_speed"],
        latest["error_rate"],
        latest["avg_pause"],
        latest["click_rate"]
    ]]
    state = int(model.predict(features)[0])
    cfg   = STATE_CONFIG[state]

    suggestion  = get_ai_suggestion(
        state,
        latest["typing_speed"],
        latest["error_rate"],
        latest["avg_pause"]
    )
    focus_score = calculate_focus_score(df)

    if focus_score >= 70:
        score_color = "#00C851"
        score_label = "Great Session! 🔥"
    elif focus_score >= 40:
        score_color = "#ffbb33"
        score_label = "Getting There 💪"
    else:
        score_color = "#ff4444"
        score_label = "Needs Improvement 😴"

    with placeholder.container():

        st.markdown(f"""
        <div style='display:flex; justify-content:flex-end; margin-bottom:8px;'>
            <div class='live-badge'>
                <span class='pulse' style='background:#00f5ff;'></span>
                LIVE — UPDATE #{iteration}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='state-card' style='
            background:{cfg["glow"]};
            border-color:{cfg["border"]};
            box-shadow: 0 0 30px {cfg["glow"]};
        '>
            <div style='display:flex; align-items:center; gap:12px;'>
                <div style='font-size:2em;'>{cfg["emoji"]}</div>
                <div>
                    <div style='
                        font-family:Orbitron;
                        font-size:1.4em;
                        font-weight:900;
                        color:{cfg["color"]};
                        letter-spacing:3px;
                    '>{cfg["label"]}</div>
                    <div style='color:#aaa; font-size:0.85em; margin-top:3px;'>
                        {cfg["message"]}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        score_col, m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1, 1])

        with score_col:
            st.markdown(f"""
            <div class='score-container'>
                <div style='color:#555; font-family:Orbitron;
                     font-size:0.6em; letter-spacing:2px;'>
                     FOCUS SCORE
                </div>
                <div style='
                    font-family:Orbitron;
                    font-size:2.8em;
                    font-weight:900;
                    color:{score_color};
                    line-height:1.1;
                '>{focus_score}</div>
                <div style='color:{score_color};
                     font-size:0.75em;'>{score_label}</div>
            </div>
            """, unsafe_allow_html=True)

        with m1:
            st.metric("⌨️ Typing Speed",
                      f"{latest['typing_speed']:.2f}",
                      help="Keystrokes per second")
        with m2:
            st.metric("⌫ Error Rate",
                      f"{latest['error_rate']:.2f}",
                      help="Backspaces / total keys")
        with m3:
            st.metric("⏸️ Avg Pause",
                      f"{latest['avg_pause']:.2f}s",
                      help="Average pause between keystrokes")
        with m4:
            st.metric("🖱️ Click Rate",
                      f"{latest['click_rate']:.2f}",
                      help="Mouse clicks per second")

        st.markdown("<br>", unsafe_allow_html=True)

        left, right = st.columns([2, 1])

        with left:
            st.markdown("""
            <div style='font-family:Orbitron; font-size:0.75em;
                 letter-spacing:3px; color:#666; margin-bottom:10px;'>
                📈 SESSION HISTORY
            </div>
            """, unsafe_allow_html=True)

            if len(df) > 1:
                chart_df = df[["typing_speed",
                               "error_rate",
                               "avg_pause"]].tail(20).copy()
                for col in chart_df.columns:
                    max_val = chart_df[col].max()
                    if max_val > 0:
                        chart_df[col] = chart_df[col] / max_val
                st.line_chart(chart_df, height=240)
                st.caption("📊 Values normalized 0→1 for comparison")
            else:
                st.markdown("""
                <div style='text-align:center; padding:50px;
                     color:#333; border:1px dashed #1a1a1a;
                     border-radius:12px; font-size:0.85em;'>
                    🎹 Keep coding — graph appears after 2 windows
                </div>
                """, unsafe_allow_html=True)

        with right:
            st.markdown("""
            <div style='font-family:Orbitron; font-size:0.75em;
                 letter-spacing:3px; color:#666; margin-bottom:10px;'>
                💡 AI SUGGESTION
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div class='suggestion-card'>
                <div style='
                    color:#ddd;
                    font-size:0.9em;
                    line-height:1.7;
                '>{suggestion}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='footer-text'>
            CODESENSE &nbsp;•&nbsp;
            UPDATED {pd.Timestamp.now().strftime('%H:%M:%S')} &nbsp;•&nbsp;
            {len(df)} WINDOWS RECORDED
        </div>
        """, unsafe_allow_html=True)

    time.sleep(30)