# 🧩 **Feature Store & Data Processing — MLOps Titanic Survival Prediction**

This stage turns your exploratory preprocessing into a **repeatable pipeline** and persists engineered features in a **Redis-backed Feature Store**.
You’ll spin up Redis in Docker locally, run the processing script, and verify that features are written and retrievable by `PassengerId`.

## 🧾 What this stage includes

* ✅ **Redis Feature Store** (`src/feature_store.py`) for fast key–value access to features
* ✅ **Data Processing pipeline** (`src/feature_processing.py`) for cleaning, encoding, engineering, and SMOTE balancing
* ✅ **End-to-end run** that loads raw CSVs, processes data, and writes features to Redis

## 🐳 Start Redis locally (Docker)

### 1) Pull the Redis image

```bash
docker pull redis
```

**Expected output (abridged):**

```
Using default tag: latest
latest: Pulling from library/redis
7e44f5a6338c: Pull complete
fa85867e458c: Pull complete
20770aaf8f7b: Pull complete
3ac4f782b24c: Pull complete
628b0785ec0d: Pull complete
4f4fb700ef54: Pull complete
Digest: sha256:f0957bcaa75fd58a9a1847c1f07caf370579196259d69ac07f2e27b5b389b021
Status: Downloaded newer image for redis:latest
docker.io/library/redis:latest
```

### 2) Run the Redis container

```bash
docker run -d --name redis-container -p 6379:6379 redis
```

**Expected output (container id):**

```
c4271ee1d69caebb23f2e3a4ef41b5b5da0b2c47b6434b56d6f5f5212c6c4eae
```

## 🧮 Run the Data Processing pipeline

This script will:

1. Load `titanic_train.csv` and `titanic_test.csv` from `artifacts/raw/`
2. Impute and encode fields; engineer features (`Familysize`, `Isalone`, `HasCabin`, `Title`, `Pclass_Fare`, `Age_Fare`)
3. Apply **SMOTE** to address class imbalance
4. Write per-passenger feature dicts to Redis under `entity:<PassengerId>:features`

```bash
python src/feature_processing.py
```

**Typical output:**

```
2025-10-16 13:24:59,245 - INFO - 🔧 Initialising Redis feature store and running pipeline...
2025-10-16 13:24:59,246 - INFO - RedisFeatureStore initialised: host=localhost, port=6379, db=0
2025-10-16 13:24:59,246 - INFO - DataProcessing initialised.
2025-10-16 13:24:59,247 - INFO - 🚀 Starting Data Processing pipeline...
2025-10-16 13:24:59,254 - INFO - Training data loaded from 'artifacts/raw\titanic_train.csv' (shape=(712, 12)); Test data loaded from 'artifacts/raw\titanic_test.csv' (shape=(179, 12)).
2025-10-16 13:24:59,263 - INFO - Data preprocessing complete.
2025-10-16 13:24:59,272 - INFO - Class imbalance handled with SMOTE (original n=712, resampled n=888).
2025-10-16 13:24:59,792 - INFO - Batch stored 712 entities into Redis.
2025-10-16 13:24:59,792 - INFO - Pushed 712 entities to the Redis feature store.
2025-10-16 13:24:59,792 - INFO - ✅ Data Processing pipeline completed successfully.
2025-10-16 13:24:59,793 - INFO - 🔎 Retrieved features for PassengerId=332: {'Age': 45.5, 'Fare': 28.5, 'Pclass': 1, 'Sex': 0, 'Embarked': 2, 'Familysize': 1, 'Isalone': 1, 'HasCabin': 1, 'Title': 0.0, 'Pclass_Fare': 28.5, 'Age_Fare': 1296.75, 'Survived': 0}
```

## 🗂️ Updated Project Structure

```
mlops-titanic-survival-prediction/
├── artifacts/
├── config/
├── notebook/
├── src/
│   ├── custom_exception.py
│   ├── feature_store.py            # Redis Feature Store
│   └── feature_processing.py       # Cleaning, FE, SMOTE, push to Redis
├── logs/
├── requirements.txt
├── setup.py
└── README.md                       # You are here
```

## 🔗 How this stage fits the pipeline

Raw data (PostgreSQL → CSV) ➜ **Preprocessing & Feature Engineering** ➜ **Redis Feature Store**
Downstream components (training, inference, monitoring) can now **fetch features by `PassengerId`** without re-running preprocessing.

## 🛠️ Quick tips

* If you re-run processing, keys are overwritten safely using the same `entity:<PassengerId>:features` pattern
* Verify Redis is running: `docker ps`
* Inspect keys directly inside the container:

  ```bash
  docker exec -it redis-container redis-cli
  keys "entity:*:features"
  get "entity:332:features"
  ```

## 🚀 Next stage — Model Training

With features centralised in Redis, the next branch focuses on **model training**: building the training pipeline, pulling features from the store, logging metrics, and preparing the model artefacts for evaluation and deployment.