# 🌐 **Inference Stage — Flask Web App (MLOps Titanic Survival Prediction)**

![Titanic Survival Dashboard Demo](img/flask_app/titanic.gif)

This stage transforms your trained Random Forest model into a **fully interactive inference dashboard**, served via **Flask**.  
Users can enter passenger details, receive **real-time predictions**, and view **data drift detection results** in a single elegant interface.  
The app also exports **Prometheus metrics** for future monitoring and alerting via **Grafana**.


## 🧠 **Key Features**

* 🧍 **Passenger Input Form** — enter values for age, fare, class, sex, port of embarkation, etc.  
* 📊 **Live Model Prediction** — displays *SURVIVED* or *DID NOT SURVIVE* with probability estimates.  
* ⚠️ **Data Drift Detection** — powered by **Alibi Detect (KSDrift)**, showing per-feature p-values and flagged drift indicators.  
* 🧾 **Human-Readable Summary** — contextualises predictions (e.g., “A Female aged 28 in Second Class…”).  
* 🌙 **Night Mode Glass UI** — a responsive dark theme with glowing buttons and translucent panels.  
* 📈 **Prometheus Metrics Endpoint** — exposes `/metrics` for scraping model activity statistics:
  - `prediction_count` — total predictions served  
  - `drift_count` — total drift detections  
* 🧩 **Scalable Design** — easy to extend with additional routes, models, or input variables.

## ⚙️ **Run the Flask App**

From the project root:

```bash
python app.py
````

This launches:

* Flask app on **port 5000**
* Prometheus metrics endpoint on **port 8000**

Then open your browser at 👉 `http://localhost:5000`

## 💡 **Dashboard Walkthrough**

The animated demo below illustrates:

* Submitting passenger details that yield both **SURVIVED** and **DID NOT SURVIVE** outcomes.
* A case where **data drift** is triggered and flagged in the Drift Detector panel.

![Titanic Survival GIF](img/flask_app/titanic.gif)

## 🗂️ **Updated Project Structure**

```text
mlops-titanic-survival-prediction/
├── artifacts/
│   ├── raw/
│   ├── processed/
│   └── models/
│       └── random_forest_model.pkl
├── config/
│   ├── database_config.py
│   └── paths_config.py
├── img/
│   └── flask_app/
│       └── titanic.gif
├── logs/
│   └── log_YYYY-MM-DD.log
├── notebook/
│   └── titanic.ipynb
├── pipeline/
│   └── training_pipeline.py
├── src/
│   ├── custom_exception.py
│   ├── logger.py
│   ├── data_ingestion.py
│   ├── feature_store.py
│   ├── feature_processing.py
│   └── model_training.py
├── templates/
│   └── index.html                # Flask UI template
├── static/
│   ├── style.css                 # Night Mode Glass UI stylesheet
│   └── background.jpg            # Optional background image
├── app.py                        # Flask inference web app
├── requirements.txt
├── setup.py
└── README.md
```

## 🧩 **Integration Summary**

This stage bridges **model training → real-time inference**.
It demonstrates the full loop of:

1. Loading trained model artefacts
2. Accepting user input
3. Computing predictions
4. Detecting data drift
5. Serving outputs through a modern UI

The result is an **end-to-end, production-style inference pipeline** with observability hooks in place.

## 🚀 **Next Stage — Monitoring with Prometheus & Grafana**

Next, you’ll deploy **Prometheus** and **Grafana** to monitor:

* Model prediction volume (`prediction_count`)
* Drift detection frequency (`drift_count`)
* System health and response latency

This step adds real-time **monitoring**, **alerting**, and **dashboarding** capabilities — completing the MLOps lifecycle.