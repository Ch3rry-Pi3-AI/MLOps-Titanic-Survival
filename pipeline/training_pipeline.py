"""
training_pipeline.py
--------------------
Coordinates the **end-to-end MLOps workflow** for the Titanic Survival Prediction project,
executing all major pipeline stages sequentially:

1. 🗃️ Data Ingestion   → Extracts raw data from PostgreSQL into `artifacts/raw/`
2. 🧮 Data Processing  → Cleans, engineers, and stores features into Redis Feature Store
3. 🤖 Model Training   → Retrieves features from Redis, tunes & trains Random Forest model

This orchestrator script represents the first version of a **reproducible training pipeline** —
combining all standalone components under a single entry point.

Integrates with:
- `src.data_ingestion.DataIngestion`
- `src.data_processing.DataProcessing`
- `src.model_training.ModelTraining`
- `src.feature_store.RedisFeatureStore`
- Centralised logging and exception handling via `src.logger` & `src.custom_exception`

Usage
-----
Run the full pipeline from the project root:

    python pipeline/training_pipeline.py

Notes
-----
- Requires a running Redis container (started in the Feature Store stage).
- Assumes PostgreSQL connection settings are correctly defined in `config/database_config.py`.
- Output artefacts:
    - Raw data CSVs → `artifacts/raw/`
    - Engineered features → Redis
    - Trained model → `artifacts/models/random_forest_model.pkl`
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Temporary Import Path Hack (Option D)
# -------------------------------------------------------------------
# Ensures project root is added to sys.path so modules under `src/`
# and `config/` can be imported when executing this file directly.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))

# -------------------------------------------------------------------
# Internal Imports
# -------------------------------------------------------------------
from src.data_ingestion import DataIngestion
from src.data_processing import DataProcessing
from src.model_training import ModelTraining
from src.feature_store import RedisFeatureStore
from config.paths_config import *
from config.database_config import DB_CONFIG


# -------------------------------------------------------------------
# Pipeline Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    # -------------------------------------------------------------------
    # 1️⃣ Data Ingestion Stage
    # -------------------------------------------------------------------
    data_ingestion = DataIngestion(DB_CONFIG, RAW_DIR)
    data_ingestion.run()

    # -------------------------------------------------------------------
    # 2️⃣ Data Processing Stage
    # -------------------------------------------------------------------
    feature_store = RedisFeatureStore()
    data_processor = DataProcessing(TRAIN_PATH, TEST_PATH, feature_store)
    data_processor.run()

    # -------------------------------------------------------------------
    # 3️⃣ Model Training Stage
    # -------------------------------------------------------------------
    feature_store = RedisFeatureStore()
    model_trainer = ModelTraining(feature_store)
    model_trainer.run()