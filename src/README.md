# 🧠 `src/` README — Core Pipeline Modules

The `src/` directory now includes **Model Training** alongside the **Feature Store** and **Data Processing** components — completing the mid-stage pipeline for the **MLOps Titanic Survival Prediction** project.
The flow is now: *data extraction* ➜ *feature engineering & storage in Redis* ➜ *model training with persisted features*.

## 📁 Folder Overview

```text
src/
├─ custom_exception.py       # Unified and descriptive error handling across modules
├─ logger.py                 # Centralised logging configuration (UTF-8 supported)
├─ data_ingestion.py         # Extracts raw Titanic data from PostgreSQL to artifacts/raw/
├─ feature_store.py          # Redis-based key-value feature store interface
├─ feature_processing.py     # Preprocesses data, handles imbalance, stores features to Redis
└─ model_training.py         # Loads features from Redis, tunes & trains RF, saves model
```

## 🤖 `model_training.py` — Random Forest Training & Persistence

### Purpose

Implements the **ModelTraining** class — responsible for:

* Loading engineered features by `PassengerId` from the **Redis Feature Store**
* Splitting entity IDs into train/test sets
* Hyperparameter tuning with **RandomizedSearchCV** on **RandomForestClassifier**
* Evaluating **accuracy** on the held-out set
* Persisting the trained model to `artifacts/models/random_forest_model.pkl`

### Pipeline Overview

| Step | Description                                                                                               |
| :--- | :-------------------------------------------------------------------------------------------------------- |
| 1️⃣  | Fetch all entity IDs from Redis and split into train/test.                                                |
| 2️⃣  | Load per-entity features (including `Survived`) from Redis.                                               |
| 3️⃣  | Build `X_train`, `X_test`, `y_train`, `y_test`.                                                           |
| 4️⃣  | Run **RandomizedSearchCV** for RF (`n_estimators`, `max_depth`, `min_samples_split`, `min_samples_leaf`). |
| 5️⃣  | Evaluate accuracy and save the best model to disk.                                                        |

### Key Features

| Feature                                 | Description                                                           |
| :-------------------------------------- | :-------------------------------------------------------------------- |
| 🧲 **Feature Store Integration**        | Pulls features directly from Redis (`entity:<PassengerId>:features`). |
| 🧪 **Randomised Hyperparameter Search** | Small yet effective search space for fast iteration.                  |
| 📈 **Evaluation**                       | Reports test accuracy for quick feedback loops.                       |
| 📦 **Model Persistence**                | Serialises the best estimator to `artifacts/models/`.                 |
| 🧾 **Logging + Exceptions**             | Full traceability with `logger` and `CustomException`.                |

### Example Usage

```bash
python src/model_training.py
```

### Internal Workflow

```python
from src.feature_store import RedisFeatureStore
from src.model_training import ModelTraining

store = RedisFeatureStore()
trainer = ModelTraining(feature_store=store)
trainer.run()
```

### Typical Log Output

```
2025-10-16 15:08:41,210 - INFO - 🚀 Starting Model Training pipeline...
2025-10-16 15:08:41,415 - INFO - Prepared training data with 569 rows and 11 features.
2025-10-16 15:08:43,102 - INFO - Best parameters: {'n_estimators': 200, 'max_depth': 20, 'min_samples_split': 2, 'min_samples_leaf': 1}
2025-10-16 15:08:43,415 - INFO - ✅ Test Accuracy: 0.8425
2025-10-16 15:08:43,417 - INFO - 📦 Model saved at: artifacts/models/random_forest_model.pkl
2025-10-16 15:08:43,418 - INFO - 🏁 End of Model Training pipeline.
```

## ⚙️ `feature_store.py` — Redis Feature Store

### Purpose

Implements the **RedisFeatureStore** class — a lightweight abstraction over **Redis** used for feature management.
It provides **row-level** and **batch-level** operations to persist engineered Titanic features and retrieve them efficiently for downstream tasks.

### Key Features

| Feature                                  | Description                                                            |
| :--------------------------------------- | :--------------------------------------------------------------------- |
| 🧱 **Key–Value Architecture**            | Stores each entity’s feature set under a structured Redis key pattern. |
| 💾 **Batch Operations**                  | Efficiently handles multi-row insertions and retrievals.               |
| 🔎 **Entity Search**                     | Supports lookup of all stored entity IDs in Redis.                     |
| 🧩 **Integration-Ready**                 | Connects seamlessly with `DataProcessing` and training pipelines.      |
| 🪵 **Full Logging + Exception Handling** | Every Redis operation is logged and wrapped in `CustomException`.      |

### Example Key Format

```
entity:<PassengerId>:features
```

### Example Usage

```python
from src.feature_store import RedisFeatureStore

store = RedisFeatureStore()
sample_features = {"Age": 29, "Fare": 72.5, "Sex": 0}
store.store_features("1001", sample_features)
print(store.get_features("1001"))
```

## 🧮 `feature_processing.py` — Data Preparation & Feature Engineering

### Purpose

Implements the **DataProcessing** class — responsible for:

* Loading training and test datasets from `artifacts/raw/`
* Cleaning, encoding, and **feature engineering**
* Addressing **class imbalance** using **SMOTE**
* Writing engineered features into the **Redis Feature Store**

### Typical Log Output

```
2025-10-16 14:01:22,115 - INFO - 🚀 Starting Data Processing pipeline...
2025-10-16 14:01:22,432 - INFO - Data preprocessing complete.
2025-10-16 14:01:23,010 - INFO - Class imbalance handled with SMOTE (original n=712, resampled n=1200).
2025-10-16 14:01:23,428 - INFO - Pushed 712 entities to the Redis feature store.
2025-10-16 14:01:23,431 - INFO - ✅ Data Processing pipeline completed successfully.
```

## ⚙️ `data_ingestion.py` — Data Extraction Pipeline (Context Recap)

Still the *entry point* of the overall data flow — fetching and splitting Titanic data from PostgreSQL before preprocessing.

| Step | Description                                      |
| :--- | :----------------------------------------------- |
| 1️⃣  | Extract data from PostgreSQL (`public.titanic`). |
| 2️⃣  | Split into 80/20 training and test sets.         |
| 3️⃣  | Save results to `artifacts/raw/`.                |

## 🗂️ Updated Project Structure (relevant paths)

```text
mlops-titanic-survival-prediction/
├─ artifacts/
│  ├─ raw/
│  │  ├─ titanic_train.csv
│  │  └─ titanic_test.csv
│  ├─ processed/
│  └─ models/
│     └─ random_forest_model.pkl
├─ config/
│  ├─ database_config.py
│  └─ paths_config.py
├─ notebook/
│  └─ titanic.ipynb
├─ src/
│  ├─ custom_exception.py
│  ├─ logger.py
│  ├─ data_ingestion.py
│  ├─ feature_store.py
│  ├─ feature_processing.py
│  └─ model_training.py
└─ logs/
   └─ log_YYYY-MM-DD.log
```

## ⚠️ `custom_exception.py` — Unified Error Handling

Continues to manage exception reporting uniformly across ingestion, processing, and training.

| Benefit                        | Description                                         |
| :----------------------------- | :-------------------------------------------------- |
| 🪶 **Lightweight**             | Works with any raised error across pipeline files.  |
| 🔍 **Context-Rich Tracebacks** | Identifies file name and line number automatically. |
| 🧩 **Seamless Integration**    | Used in all pipeline modules.                       |

## 🪵 `logger.py` — Centralised Logging

UTF-8-enabled logging shared by all modules for consistent, readable progress and diagnostics.

| Property  | Example                                     |
| :-------- | :------------------------------------------ |
| Directory | `logs/`                                     |
| File name | `log_2025-10-16.log`                        |
| Format    | `%(asctime)s - %(levelname)s - %(message)s` |

## 🔗 Integration Summary

| Module                  | Primary Function                          | Downstream Dependency                    |
| :---------------------- | :---------------------------------------- | :--------------------------------------- |
| `data_ingestion.py`     | Extracts and splits raw Titanic data      | Feeds into `feature_processing.py`       |
| `feature_processing.py` | Cleans, engineers, and balances features  | Writes to `feature_store.py`             |
| `feature_store.py`      | Manages Redis-based feature persistence   | Used by `model_training.py`              |
| `model_training.py`     | Tunes, trains, evaluates, and saves model | Produces artefact in `artifacts/models/` |
| `custom_exception.py`   | Handles errors across all modules         | Shared                                   |
| `logger.py`             | Logs pipeline progress consistently       | Shared                                   |

✅ **In summary:**

* `feature_processing.py` → transforms and engineers data for model readiness
* `feature_store.py` → persists engineered features for fast retrieval
* `model_training.py` → pulls features, tunes & trains RF, and saves the model artefact
* `data_ingestion.py`, `custom_exception.py`, `logger.py` → provide the stable foundation for reliable, observable pipelines

This completes the mid-stage pipeline and sets up the project for the next branch: **evaluation, model registry/versioning, and inference deployment**.