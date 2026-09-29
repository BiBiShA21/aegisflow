import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from xgboost import XGBClassifier
import joblib
import os

# ── Step 1: Auto-label real data ──────────────────────────
def auto_label(row):
    """Label rows using simple rules based on behavior patterns."""
    if row["typing_speed"] < 0.5 or row["avg_pause"] > 4.0:
        return 2   # 🔴 Overloaded
    elif row["error_rate"] > 0.3 or row["avg_pause"] > 1.5:
        return 1   # 🟡 Struggling
    else:
        return 0   # 🟢 Focused

# ── Step 2: Generate synthetic training data ──────────────
def generate_synthetic_data(n=500):
    """Create realistic fake sessions for each cognitive state."""
    np.random.seed(42)
    rows = []

    for _ in range(n):
        state = np.random.choice([0, 1, 2])

        if state == 0:   # 🟢 Focused
            row = {
                "typing_speed" : np.random.uniform(5, 12),
                "error_rate"   : np.random.uniform(0.0, 0.15),
                "avg_pause"    : np.random.uniform(0.2, 0.8),
                "click_rate"   : np.random.uniform(0.0, 0.1),
                "label"        : 0
            }
        elif state == 1:  # 🟡 Struggling
            row = {
                "typing_speed" : np.random.uniform(2, 6),
                "error_rate"   : np.random.uniform(0.2, 0.45),
                "avg_pause"    : np.random.uniform(1.0, 2.5),
                "click_rate"   : np.random.uniform(0.1, 0.3),
                "label"        : 1
            }
        else:             # 🔴 Overloaded
            row = {
                "typing_speed" : np.random.uniform(0.0, 2.5),
                "error_rate"   : np.random.uniform(0.35, 0.8),
                "avg_pause"    : np.random.uniform(3.0, 8.0),
                "click_rate"   : np.random.uniform(0.2, 0.5),
                "label"        : 2
            }
        rows.append(row)

    return pd.DataFrame(rows)

# ── Step 3: Load + combine data ───────────────────────────
print("📂 Loading data...")

# Load your real session data
real_df = pd.read_csv("data/sessions.csv")
real_df["label"] = real_df.apply(auto_label, axis=1)

print(f"   Real sessions: {len(real_df)} rows")
print(f"   Labels assigned: {real_df['label'].value_counts().to_dict()}")

# Generate synthetic data
synth_df = generate_synthetic_data(500)
print(f"   Synthetic sessions: {len(synth_df)} rows")

# Combine both
df = pd.concat([real_df[["typing_speed","error_rate",
                          "avg_pause","click_rate","label"]],
                synth_df], ignore_index=True)

print(f"   Total training data: {len(df)} rows\n")

# ── Step 4: Train the model ───────────────────────────────
FEATURES = ["typing_speed", "error_rate", "avg_pause", "click_rate"]
X = df[FEATURES]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("🤖 Training XGBoost model...")
model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric="mlogloss",
    random_state=42
)
model.fit(X_train, y_train)

# ── Step 5: Evaluate ──────────────────────────────────────
print("\n📊 Model Performance:")
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred,
      target_names=["🟢 Focused","🟡 Struggling","🔴 Overloaded"]))

# ── Step 6: Save model ────────────────────────────────────
os.makedirs("models", exist_ok=True)
joblib.dump(model, "models/codesense_model.pkl")
print("✅ Model saved to models/codesense_model.pkl")
