# 🧠 `src/` README — Core Pipeline Modules

The `src/` directory now includes the **Feature Store** and **Data Processing** components — the backbone of the **MLOps Titanic Survival Prediction** project’s mid-stage pipeline.
At this point, the focus shifts from *data extraction* to *feature engineering*, *balancing*, and *storing processed features* in a **Redis-based feature store** for model training and inference.

## 📁 Folder Overview

```text
src/
├─ custom_exception.py       # Unified and descriptive error handling across modules
├─ logger.py                 # Centralised logging configuration (UTF-8 supported)
├─ data_ingestion.py         # Extracts raw Titanic data from PostgreSQL to artifacts/raw/
├─ feature_store.py          # Redis-based key-value feature store interface
└─ feature_processing.py     # Preprocesses data, handles imbalance, stores features to Redis
```



## ⚙️ `feature_store.py` — Redis Feature Store

### Purpose

Implements the **RedisFeatureStore** class — a lightweight abstraction over **Redis** used for feature management.
It provides **row-level** and **batch-level** operations to persist engineered Titanic features and retrieve them efficiently for downstream tasks (model training, inference, and monitoring).

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

retrieved = store.get_features("1001")
print(retrieved)
# → {'Age': 29, 'Fare': 72.5, 'Sex': 0}
```

### Typical Log Output

```
2025-10-16 13:22:10,421 - INFO - RedisFeatureStore initialised: host=localhost, port=6379, db=0
2025-10-16 13:22:10,426 - DEBUG - Stored features for entity 1001 with key: entity:1001:features
2025-10-16 13:22:10,430 - INFO - ✅ Retrieved sample features: {'Age': 29, 'Fare': 72.5, 'Sex': 0}
```



## 🧮 `feature_processing.py` — Data Preparation & Feature Engineering

### Purpose

Implements the **DataProcessing** class — responsible for:

* Loading training and test datasets from `artifacts/raw/`.
* Performing **data cleaning** and **feature engineering**.
* Addressing **class imbalance** using **SMOTE**.
* Writing the resulting features into the **Redis feature store** for reuse in training and inference.

### Pipeline Overview

| Step | Description                                                                                                                                              |
| :--- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1️⃣  | Load CSVs for training and testing from configured paths.                                                                                                |
| 2️⃣  | Clean and impute missing values for `Age`, `Embarked`, and `Fare`.                                                                                       |
| 3️⃣  | Encode categorical fields (`Sex`, `Embarked`) and create engineered variables (`Familysize`, `Isalone`, `HasCabin`, `Title`, `Pclass_Fare`, `Age_Fare`). |
| 4️⃣  | Use **SMOTE** to balance the target variable `Survived`.                                                                                                 |
| 5️⃣  | Store engineered features in the Redis Feature Store via `RedisFeatureStore`.                                                                            |

### Key Features

| Feature                        | Description                                                              |
| :----------------------------- | :----------------------------------------------------------------------- |
| 🧩 **Automated Preprocessing** | Handles imputations, encoding, and engineered feature creation.          |
| ⚖️ **SMOTE Integration**       | Balances the dataset for improved model generalisation.                  |
| 🔁 **Redis Integration**       | Exports engineered features to the feature store for cross-stage access. |
| 🧾 **Traceable Pipeline Logs** | Logs each transformation for full reproducibility and debugging.         |
| 🧠 **Feature Reuse**           | Allows models to directly query engineered features by `PassengerId`.    |

### Example Usage

```bash
python src/feature_processing.py
```

### Internal Workflow

```python
from config.paths_config import TRAIN_PATH, TEST_PATH
from src.feature_store import RedisFeatureStore
from src.feature_processing import DataProcessing

store = RedisFeatureStore()
processor = DataProcessing(TRAIN_PATH, TEST_PATH, store)
processor.run()
```

### Typical Log Output

```
2025-10-16 14:01:22,115 - INFO - 🚀 Starting Data Processing pipeline...
2025-10-16 14:01:22,432 - INFO - Data preprocessing complete.
2025-10-16 14:01:23,010 - INFO - Class imbalance handled with SMOTE (original n=712, resampled n=1200).
2025-10-16 14:01:23,428 - INFO - Pushed 712 entities to the Redis feature store.
2025-10-16 14:01:23,431 - INFO - ✅ Data Processing pipeline completed successfully.
```



## ⚙️ `data_ingestion.py` — Data Extraction Pipeline (Context Recap)

For context, this file (from the previous stage) still forms the *entry point* of the overall pipeline —
responsible for fetching and splitting Titanic data from PostgreSQL before preprocessing.

| Step | Description                                      |
| :--- | :----------------------------------------------- |
| 1️⃣  | Extract data from PostgreSQL (`public.titanic`). |
| 2️⃣  | Split into 80/20 training and test sets.         |
| 3️⃣  | Save results to `artifacts/raw/`.                |

Together with `feature_processing.py`, it defines the **Raw ➜ Processed ➜ Feature Store** data flow.


## ⚠️ `custom_exception.py` — Unified Error Handling

No changes in behaviour — it continues to manage all exception reporting uniformly across the ingestion and processing stages.

| Benefit                        | Description                                                                   |
| :----------------------------- | :---------------------------------------------------------------------------- |
| 🪶 **Lightweight**             | Works with any raised error across pipeline files.                            |
| 🔍 **Context-Rich Tracebacks** | Identifies file name and line number automatically.                           |
| 🧩 **Seamless Integration**    | Used in `data_ingestion.py`, `feature_processing.py`, and `feature_store.py`. |



## 🪵 `logger.py` — Centralised Logging

Provides UTF-8-enabled logging for all pipeline components —
ensuring consistency between ingestion, processing, and storage phases.

| Property  | Example                                     |
| :-------- | :------------------------------------------ |
| Directory | `logs/`                                     |
| File name | `log_2025-10-16.log`                        |
| Format    | `%(asctime)s - %(levelname)s - %(message)s` |



## 🔗 Integration Summary

| Module                  | Primary Function                         | Downstream Dependency                |
| :---------------------- | :--------------------------------------- | :----------------------------------- |
| `data_ingestion.py`     | Extracts and splits raw Titanic data     | Feeds into `feature_processing.py`   |
| `feature_processing.py` | Cleans, engineers, and balances features | Writes to `feature_store.py`         |
| `feature_store.py`      | Manages Redis-based feature persistence  | Used during model training/inference |
| `custom_exception.py`   | Handles errors across all modules        | Shared                               |
| `logger.py`             | Logs pipeline progress consistently      | Shared                               |


✅ **In summary:**

* `feature_processing.py` → Transforms and engineers data for model readiness.
* `feature_store.py` → Persists these features for fast retrieval and reusability.
* `data_ingestion.py` → Provides the raw input foundation.
* `custom_exception.py` & `logger.py` → Provide consistency, observability, and traceability.

Together, these files represent the **intermediate data foundation** of the MLOps Titanic Survival Prediction system —
bridging raw ingestion with model training through **structured preprocessing**, **feature engineering**, and **stateful feature storage**.
