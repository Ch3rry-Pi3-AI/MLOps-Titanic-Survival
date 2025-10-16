import pickle
import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from src.logger import get_logger
from alibi_detect.cd import KSDrift
from src.feature_store import RedisFeatureStore
from sklearn.preprocessing import StandardScaler
from prometheus_client import start_http_server, Counter

logger = get_logger(__name__)

app = Flask(__name__, template_folder="templates")

prediction_count = Counter('prediction_count', "Number of prediction count")
drift_count = Counter('drift_count', "Number of times data drift is detected")

MODEL_PATH = "artifacts/models/random_forest_model.pkl"
with open(MODEL_PATH, 'rb') as model_file:
    model = pickle.load(model_file)

FEATURE_NAMES = [
    'Age', 'Fare', 'Pclass', 'Sex', 'Embarked', 'Familysize', 'Isalone',
    'HasCabin', 'Title', 'Pclass_Fare', 'Age_Fare'
]

feature_store = RedisFeatureStore()
scaler = StandardScaler()

def fit_scaler_on_ref_data():
    entity_ids = feature_store.get_all_entity_ids()
    all_features = feature_store.get_batch_features(entity_ids)
    all_features_df = pd.DataFrame.from_dict(all_features, orient='index')[FEATURE_NAMES]
    scaler.fit(all_features_df)
    return scaler.transform(all_features_df)

historical_data = fit_scaler_on_ref_data()
ksd = KSDrift(x_ref=historical_data, p_val=0.05)

@app.route('/')
def home():
    return render_template('index.html', prediction_label=None, drift=None)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.form

        # Enforce integer types & bounds
        Age = int(float(data["Age"]))
        if Age < 0 or Age > 120:
            raise ValueError("Age out of valid range (0–120).")

        Fare = int(float(data["Fare"]))
        if Fare < 0 or Fare > 10000:
            raise ValueError("Fare out of valid range (0–10000).")

        Pclass = int(data["Pclass"])
        if Pclass not in (1, 2, 3):
            raise ValueError("Pclass must be 1, 2, or 3.")

        Sex = int(data["Sex"])
        Embarked = int(data["Embarked"])

        Familysize = int(float(data["Familysize"]))
        if Familysize < 0:
            raise ValueError("Family Size cannot be negative.")

        Isalone = int(data["Isalone"])
        HasCabin = int(data["HasCabin"])
        Title = int(data["Title"])

        # Interaction features (server-side, hidden from UI)
        Pclass_Fare = Pclass * Fare
        Age_Fare = Age * Fare

        features = pd.DataFrame([[
            Age, Fare, Pclass, Sex, Embarked, Familysize, Isalone,
            HasCabin, Title, Pclass_Fare, Age_Fare
        ]], columns=FEATURE_NAMES)

        # ----- Data Drift Detection -----
        features_scaled = scaler.transform(features)
        drift_raw = ksd.predict(features_scaled)
        drift_data = drift_raw.get('data', {})
        is_drift = drift_data.get('is_drift', None)
        p_vals = drift_data.get('p_val', None)

        # Prepare drift info for UI
        alpha = 0.05
        rows = []
        flagged_features = []
        if p_vals is not None:
            try:
                pv_list = p_vals.tolist()
            except Exception:
                pv_list = [float(x) for x in np.ravel(p_vals)]
            for fname, pv in zip(FEATURE_NAMES, pv_list):
                flagged = pv < alpha
                rows.append({
                    "feature": fname,
                    "pval": f"{pv:.6f}",
                    "flagged": flagged
                })
                if flagged:
                    flagged_features.append(fname)

        # Log drift details
        if p_vals is not None:
            logger.info(f"Drift check → is_drift={is_drift}, alpha={alpha}, p_vals={list(zip(FEATURE_NAMES, pv_list))}")
            print(f"[DRIFT CHECK] is_drift={is_drift}, alpha={alpha}, p_vals={list(zip(FEATURE_NAMES, pv_list))}")
        else:
            logger.info(f"Drift check → is_drift={is_drift} (no p_vals returned)")
            print(f"[DRIFT CHECK] is_drift={is_drift} (no p_vals returned)")

        if is_drift is not None and is_drift == 1:
            drift_count.inc()
            logger.warning(f"DRIFT DETECTED — features below alpha: {flagged_features}")
            print(f"[DRIFT] DRIFT DETECTED — features below alpha: {flagged_features}")

        drift_payload = {
            "is_drift": bool(is_drift == 1),
            "alpha": f"{alpha:.2f}",
            "rows": rows,
            "flagged_features": flagged_features
        }

        # ----- Model Inference -----
        yhat = int(model.predict(features)[0])
        prediction_count.inc()
        label = 'SURVIVED' if yhat == 1 else 'DID NOT SURVIVE'

        prob_pct = None
        try:
            if hasattr(model, "predict_proba"):
                prob_survive = float(model.predict_proba(features)[0, 1])
                prob_pct = f"{prob_survive * 100:.2f}"
        except Exception as e:
            logger.warning(f"predict_proba failed: {e}")

        # Build human-readable summary sentence
        sex_map = {0: "Male", 1: "Female"}
        embarked_map = {0: "Cherbourg", 1: "Queenstown", 2: "Southampton"}
        title_map = {0: "Mr", 1: "Miss", 2: "Mrs", 3: "Master", 4: "Rare"}
        has_cabin_text = "with a cabin" if HasCabin == 1 else "without a cabin"
        alone_text = "travelling alone" if Isalone == 1 else "travelling with others"

        sentence = (
            f"A {sex_map.get(Sex, 'Person')} aged {Age} in class {Pclass}, paying fare {Fare}, "
            f"embarked at {embarked_map.get(Embarked, 'Unknown')}, title {title_map.get(Title, 'Unknown')}, "
            f"family size {Familysize}, {has_cabin_text}, {alone_text}."
        )

        return render_template(
            'index.html',
            prediction_label=label,
            prediction_sentence=sentence,
            prediction_prob=prob_pct,
            drift=drift_payload,
            error_text=None
        )

    except Exception as e:
        logger.exception("Prediction failed")
        return render_template(
            'index.html',
            prediction_label=None,
            prediction_sentence=None,
            prediction_prob=None,
            drift=None,
            error_text=f"Error: {str(e)}"
        ), 400

@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    from flask import Response
    return Response(generate_latest(), content_type='text/plain')

if __name__ == "__main__":
    start_http_server(8000)
    app.run(debug=True, host='0.0.0.0', port=5000)