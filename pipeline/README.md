# 🔄 **Training Pipeline — MLOps Titanic Survival Prediction**

The `pipeline/` directory contains the **orchestration layer** for the entire MLOps workflow.
It coordinates all modular components under a **single, reproducible training entry point**, enabling the complete data-to-model process to run seamlessly from start to finish.

## 🧾 What this stage includes

* ✅ **`training_pipeline.py`** — integrates all pipeline stages:

  * **Data Ingestion** → extracts the Titanic dataset from PostgreSQL
  * **Data Processing** → cleans, engineers, and stores features in Redis
  * **Model Training** → retrieves features from Redis, trains and saves a Random Forest model
* ✅ **End-to-end automation** — runs the full lifecycle with one command
* ✅ **Traceable artefacts** — logs, data files, and trained models are versioned under `artifacts/`

## ⚙️ Run the full training pipeline

To execute all stages sequentially:

```bash
python pipeline/training_pipeline.py
```

**Typical log output:**

```
2025-10-16 14:52:14,105 - INFO - 🚀 Starting Data Ingestion Pipeline...
2025-10-16 14:52:15,301 - INFO - ✅ Data Ingestion Pipeline completed successfully.
2025-10-16 14:52:15,302 - INFO - 🚀 Starting Data Processing pipeline...
2025-10-16 14:52:15,611 - INFO - ✅ Data Processing pipeline completed successfully.
2025-10-16 14:52:15,612 - INFO - 🚀 Starting Model Training pipeline...
2025-10-16 14:52:18,244 - INFO - ✅ Test Accuracy: 0.8351
2025-10-16 14:52:18,247 - INFO - 📦 Model saved at: artifacts/models/random_forest_model.pkl
2025-10-16 14:52:18,248 - INFO - 🏁 End of Model Training pipeline.
```

## 🗂️ Updated Project Structure

```
mlops-titanic-survival-prediction/
├── artifacts/
│   ├── raw/
│   └── models/
│       └── random_forest_model.pkl
├── config/
├── src/
├── pipeline/
│   └── training_pipeline.py      # 🔄 Full end-to-end workflow
├── logs/
└── README.md
```

## 🔗 How this stage fits the pipeline

This script unifies all previous components into a **single orchestrated workflow**:

**PostgreSQL ➜ Data Ingestion ➜ Feature Processing ➜ Redis Store ➜ Model Training ➜ Model Artefact**

By centralising execution in one file, the pipeline provides a reproducible, auditable foundation for **deployment**, **CI/CD automation**, and **future model retraining**.

> 💡 Next: the upcoming **Model Registry and Inference** stages will build on this pipeline to serve and monitor trained models in production.