"""
app.py
------
Flask inference service for the **MLOps Titanic Survival Prediction** project.

This module exposes a simple web UI and HTTP endpoints to:
- Load a trained Random Forest classifier from `artifacts/models/`.
- Collect user inputs, create interaction features server-side, and return a prediction.
- Detect **data drift** on each request via Alibi Detect's **KSDrift** (per-feature p-values).
- Export **Prometheus** metrics for **prediction counts** and **drift detections**.

It follows the project's formatting guidelines:
- Numpy-style docstrings
- Clear section headers
- Concise, inline comments above key lines
- UTF-8-friendly logging with helpful emojis

Routes
------
- `/`           : Render the index page.
- `/predict`    : Handle form POST, run drift detection + model inference, render results.
- `/metrics`    : Expose Prometheus metrics for scraping.

Notes
-----
- Reference feature values for the scaler are obtained from the **RedisFeatureStore**.
- Interaction features (`Pclass_Fare`, `Age_Fare`) are computed server-side and are not editable in the UI.
- The app uses **StandardScaler** fitted on historical/reference data from the feature store.
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Standard Library Imports
# -------------------------------------------------------------------
import pickle
from typing import Any, Dict, List, Optional, Tuple

# -------------------------------------------------------------------
# Third-Party Imports
# -------------------------------------------------------------------
import numpy as np
import pandas as pd
from flask import Flask, Response, render_template, request
from prometheus_client import Counter, start_http_server
from sklearn.preprocessing import StandardScaler
from alibi_detect.cd import KSDrift  # type: ignore[import-not-found]

# -------------------------------------------------------------------
# Local Project Imports
# -------------------------------------------------------------------
from src.logger import get_logger
from src.feature_store import RedisFeatureStore

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
# Create a module-scoped logger (UTF-8 and console/file handlers are set in src.logger)
logger = get_logger(__name__)

# -------------------------------------------------------------------
# Flask App Initialisation
# -------------------------------------------------------------------
# Instantiate the Flask application and point to the templates directory
app: Flask = Flask(__name__, template_folder="templates")

# -------------------------------------------------------------------
# Prometheus Metrics
# -------------------------------------------------------------------
# Count total predictions served (monotonic counter) 📈
prediction_count: Counter = Counter("prediction_count", "Number of prediction count")

# Count times drift is detected (monotonic counter) 🚨
drift_count: Counter = Counter("drift_count", "Number of times data drift is detected")

# -------------------------------------------------------------------
# Model Loading
# -------------------------------------------------------------------
# Path to the trained Random Forest model artefact
MODEL_PATH: str = "artifacts/models/random_forest_model.pkl"

# Load the trained model into memory (at import time for simplicity)
with open(MODEL_PATH, "rb") as model_file:
    model: Any = pickle.load(model_file)

# -------------------------------------------------------------------
# Feature Definitions
# -------------------------------------------------------------------
# Ordered list of features expected by the model
FEATURE_NAMES: List[str] = [
    "Age",
    "Fare",
    "Pclass",
    "Sex",
    "Embarked",
    "Familysize",
    "Isalone",
    "HasCabin",
    "Title",
    "Pclass_Fare",
    "Age_Fare",
]

# Map technical names to human-friendly labels and short hints for the drift table
FEATURE_LABELS: Dict[str, Tuple[str, Optional[str]]] = {
    "Age": ("Age of Passenger", None),
    "Fare": ("Ticket Fare", "Price paid for the ticket"),
    "Pclass": ("Passenger Class", "1 = First, 2 = Second, 3 = Third"),
    "Sex": ("Sex", "0 = Male, 1 = Female"),
    "Embarked": ("Port of Embarkation", "0 = Cherbourg, 1 = Queenstown, 2 = Southampton"),
    "Familysize": ("Family Size", "Siblings/Spouses + Parents/Children + 1"),
    "Isalone": ("Is Alone", "1 = Yes, 0 = No"),
    "HasCabin": ("Has Cabin", "1 = Yes, 0 = No"),
    "Title": ("Passenger Title", "Mr / Miss / Mrs / Master / Rare"),
    "Pclass_Fare": ("Passenger Class × Fare", "Interaction: class multiplied by fare"),
    "Age_Fare": ("Age × Fare", "Interaction: age multiplied by fare"),
}

# -------------------------------------------------------------------
# Stateful Utilities (Feature Store & Scaler)
# -------------------------------------------------------------------
# Create a single Redis feature store client (used to fetch reference data)
feature_store: RedisFeatureStore = RedisFeatureStore()

# StandardScaler instance that will be fitted on reference data below
scaler: StandardScaler = StandardScaler()


def fit_scaler_on_ref_data() -> np.ndarray:
    """
    Fit the global `scaler` on historical/reference features from the feature store.

    Returns
    -------
    np.ndarray
        The scaled historical feature matrix in the order defined by `FEATURE_NAMES`.

    Notes
    -----
    - This uses **all** entity IDs present in the RedisFeatureStore at start-up.
    - The scaler is fitted **once** at import time to act as the x_ref for drift detection.
    """
    # Pull all entity IDs we have stored as reference population
    entity_ids: List[str] = feature_store.get_all_entity_ids()

    # Fetch a batch of features for those entities (dict keyed by entity_id)
    all_features: Dict[str, Dict[str, Any]] = feature_store.get_batch_features(entity_ids)

    # Create a DataFrame in the correct column order expected by the model
    all_features_df: pd.DataFrame = pd.DataFrame.from_dict(all_features, orient="index")[FEATURE_NAMES]

    # Fit the scaler on the reference distribution
    scaler.fit(all_features_df)

    # Return the scaled reference data (used by KSDrift)
    return scaler.transform(all_features_df)


# -------------------------------------------------------------------
# Drift Detector (KSDrift) Initialisation
# -------------------------------------------------------------------
# Fit scaler and obtain the scaled reference sample for KSDrift baseline
historical_data: np.ndarray = fit_scaler_on_ref_data()

# Create a univariate K-S drift detector per feature at 5% significance
ksd: KSDrift = KSDrift(x_ref=historical_data, p_val=0.05)

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.route("/")
def home() -> str:
    """
    Render the home page.

    Returns
    -------
    str
        HTML for the index page with empty placeholders.
    """
    # Render base template with no prediction/drift context
    return render_template("index.html", prediction_label=None, drift=None)


@app.route("/predict", methods=["POST"])
def predict() -> Tuple[str, int] | str:
    """
    Handle form submission, validate inputs, detect drift, and run model inference.

    Returns
    -------
    Union[str, Tuple[str, int]]
        On success: rendered HTML string.
        On error   : (rendered HTML string, 400) with an error message.

    Behaviour
    ---------
    1) Validate and coerce inputs (with simple bounds).
    2) Build interaction features (`Pclass_Fare`, `Age_Fare`).
    3) Detect data drift with KSDrift (per-feature p-values).
    4) Run the classifier and (if available) compute survival probability.
    5) Render a human-readable summary sentence and a drift table.
    """
    try:
        # Extract raw form data (strings)
        data: Dict[str, str] = request.form  # type: ignore[assignment]

        # --- Validate & coerce inputs (with simple bounds) -------------------
        Age: int = int(float(data["Age"]))
        if not (0 <= Age <= 120):
            raise ValueError("Age out of valid range (0–120).")

        Fare: int = int(float(data["Fare"]))
        if not (0 <= Fare <= 10_000):
            raise ValueError("Fare out of valid range (0–10000).")

        Pclass: int = int(data["Pclass"])
        if Pclass not in (1, 2, 3):
            raise ValueError("Pclass must be 1, 2, or 3.")

        Sex: int = int(data["Sex"])
        Embarked: int = int(data["Embarked"])

        Familysize: int = int(float(data["Familysize"]))
        if Familysize < 0:
            raise ValueError("Family Size cannot be negative.")

        Isalone: int = int(data["Isalone"])
        HasCabin: int = int(data["HasCabin"])
        Title: int = int(data["Title"])

        # --- Server-side interaction features (hidden from the UI) ----------
        Pclass_Fare: int = Pclass * Fare
        Age_Fare: int = Age * Fare

        # Assemble a single-row DataFrame in the exact model feature order
        features: pd.DataFrame = pd.DataFrame(
            [[Age, Fare, Pclass, Sex, Embarked, Familysize, Isalone, HasCabin, Title, Pclass_Fare, Age_Fare]],
            columns=FEATURE_NAMES,
        )

        # -------------------------------------------------------------------
        # Data Drift Detection
        # -------------------------------------------------------------------
        # Scale current features with the scaler fitted on reference data
        features_scaled: np.ndarray = scaler.transform(features)

        # Run KSDrift (returns dict with `data` containing `is_drift` and `p_val`)
        drift_raw: Dict[str, Any] = ksd.predict(features_scaled)
        drift_data: Dict[str, Any] = drift_raw.get("data", {})
        is_drift: Optional[int] = drift_data.get("is_drift", None)
        p_vals: Optional[np.ndarray] = drift_data.get("p_val", None)

        # Prepare drift table rows for the UI
        alpha: float = 0.05
        rows: List[Dict[str, Any]] = []
        flagged_features: List[str] = []

        if p_vals is not None:
            # Convert to plain python list for serialisation/templating
            try:
                pv_list: List[float] = p_vals.tolist()  # type: ignore[assignment]
            except Exception:
                pv_list = [float(x) for x in np.ravel(p_vals)]

            # Build per-feature records (pretty label + rounded p-value)
            for fname, pv in zip(FEATURE_NAMES, pv_list):
                flagged: bool = pv < alpha
                label, hint = FEATURE_LABELS.get(fname, (fname, None))
                rows.append(
                    {
                        "feature": fname,          # technical fallback
                        "feature_label": label,    # human-friendly label
                        "hint": hint,              # optional hint
                        "pval": f"{pv:.3f}",       # round to 3 d.p. as requested
                        "flagged": flagged,        # highlight when pv < alpha
                    }
                )
                if flagged:
                    flagged_features.append(label if label else fname)

            # Log drift diagnostics for observability
            logger.info(
                "Drift check → is_drift=%s, alpha=%.2f, p_vals=%s",
                is_drift,
                alpha,
                list(zip(FEATURE_NAMES, pv_list)),
            )
            print(f"[DRIFT CHECK] is_drift={is_drift}, alpha={alpha}, p_vals={list(zip(FEATURE_NAMES, pv_list))}")
        else:
            # No p-values returned (unexpected, but keep going gracefully)
            logger.info("Drift check → is_drift=%s (no p_vals returned)", is_drift)
            print(f"[DRIFT CHECK] is_drift={is_drift} (no p_vals returned)")

        # Increment Prometheus counter if any drift was detected
        if is_drift is not None and is_drift == 1:
            drift_count.inc()
            logger.warning("DRIFT DETECTED — features below alpha: %s", flagged_features)
            print(f"[DRIFT] DRIFT DETECTED — features below alpha: {flagged_features}")

        # Payload sent to the template (controls badges/table)
        drift_payload: Dict[str, Any] = {
            "is_drift": bool(is_drift == 1),
            "alpha": f"{alpha:.2f}",
            "rows": rows,
            "flagged_features": flagged_features,
        }

        # -------------------------------------------------------------------
        # Model Inference
        # -------------------------------------------------------------------
        # Predict survival class (0 or 1)
        yhat: int = int(model.predict(features)[0])

        # Count every prediction served
        prediction_count.inc()

        # Human-readable label for the UI
        prediction_label: str = "SURVIVED" if yhat == 1 else "DID NOT SURVIVE"

        # Try to compute survival probability if the model supports it
        prediction_prob_pct: Optional[str] = None
        try:
            if hasattr(model, "predict_proba"):
                prob_survive: float = float(model.predict_proba(features)[0, 1])
                prediction_prob_pct = f"{prob_survive * 100:.2f}"
        except Exception as proba_err:  # keep inference resilient
            logger.warning("predict_proba failed: %s", proba_err)

        # -------------------------------------------------------------------
        # Human-Readable Summary Sentence
        # -------------------------------------------------------------------
        sex_map = {0: "Male", 1: "Female"}
        embarked_map = {0: "Cherbourg", 1: "Queenstown", 2: "Southampton"}
        title_map = {0: "Mr", 1: "Miss", 2: "Mrs", 3: "Master", 4: "Rare"}
        pclass_map = {1: "First", 2: "Second", 3: "Third"}

        # Compose a concise, natural language summary of the passenger
        has_cabin_text: str = "with a cabin" if HasCabin == 1 else "without a cabin"
        alone_text: str = "travelling alone" if Isalone == 1 else "travelling with others"
        prediction_sentence: str = (
            f"A {sex_map.get(Sex, 'Person')} aged {Age} in {pclass_map.get(Pclass, f'class {Pclass}')}, "
            f"paying fare {Fare}, embarked at {embarked_map.get(Embarked, 'Unknown')}, "
            f"title {title_map.get(Title, 'Unknown')}, family size {Familysize}, "
            f"{has_cabin_text}, {alone_text}."
        )

        # Render the template with all artefacts (prediction + drift)
        return render_template(
            "index.html",
            prediction_label=prediction_label,
            prediction_sentence=prediction_sentence,
            prediction_prob=prediction_prob_pct,
            drift=drift_payload,
            error_text=None,
        )

    except Exception as e:
        # Log full stack trace for observability and return a 400 with context
        logger.exception("Prediction failed")
        return (
            render_template(
                "index.html",
                prediction_label=None,
                prediction_sentence=None,
                prediction_prob=None,
                drift=None,
                error_text=f"Error: {str(e)}",
            ),
            400,
        )


@app.route("/metrics")
def metrics() -> Response:
    """
    Expose Prometheus metrics for scraping.

    Returns
    -------
    flask.Response
        Plain-text exposition format for Prometheus.
    """
    # Lazily import generate_latest to keep top imports tidy
    from prometheus_client import generate_latest

    # Emit the current metrics snapshot in text/plain
    return Response(generate_latest(), content_type="text/plain")


# -------------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Start a Prometheus side-car HTTP server on :8000 for metrics scraping
    start_http_server(8000)

    # Run the Flask development server (bind to all interfaces for container use)
    app.run(debug=True, host="0.0.0.0", port=5000)
