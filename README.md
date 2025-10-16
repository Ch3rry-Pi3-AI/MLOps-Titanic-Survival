# 🔄 **Training Pipeline — MLOps Titanic Survival Prediction**

This stage introduces a **single orchestration script** that runs the whole workflow end-to-end:
**Data Ingestion ➜ Feature Processing ➜ Feature Store (Redis) ➜ Model Training ➜ Model Artefact**.

It’s a lightweight but reproducible entry point that ties together everything you built in earlier stages.

## 🧾 What this stage includes

* ✅ `pipeline/training_pipeline.py` — coordinates ingestion, processing, and training
* ✅ Saves a trained model to `artifacts/models/random_forest_model.pkl`
* ✅ Uses Redis Feature Store populated in the previous stage

## ⚙️ Run the full training pipeline

```bash
python pipeline/training_pipeline.py
```

**Typical output (abridged):**

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
│   ├── processed/
│   └── models/
│       └── random_forest_model.pkl
├── config/
│   ├── database_config.py
│   └── paths_config.py
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
├── logs/
│   └── log_YYYY-MM-DD.log
├── requirements.txt
├── setup.py
└── README.md
```

## 🔗 Where this fits

You can now reproduce the entire **data→features→model** flow with one command.
This sets the foundation for **CI/CD**, **scheduled retraining**, and downstream serving.

## 🚀 Next stage — Flask Inference App

Next, we’ll build a **Flask app** to serve predictions to users, loading the saved model from `artifacts/models/` and—optionally—pulling features from Redis on demand.