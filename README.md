# 🤖 **Model Training — MLOps Titanic Survival Prediction**

This stage transforms the engineered features stored in Redis into a **trained machine learning model**.
It retrieves features by `PassengerId`, splits them into training and test sets, performs **Random Forest** hyperparameter tuning, evaluates accuracy, and saves the trained model to the local filesystem for reuse in downstream pipelines.

## 🧾 What this stage includes

* ✅ **Model training module** (`src/model_training.py`) — trains and evaluates a Random Forest classifier
* ✅ **Integration with Redis Feature Store** — retrieves features and target labels directly from the store
* ✅ **Model artefact storage** — saves the trained model under `artifacts/models/random_forest_model.pkl`
* ✅ **Automatic logging and exception handling** for every step of the process

## 🧮 Run the Model Training pipeline

This script will:

1. Connect to the **Redis Feature Store** and retrieve all entity features
2. Split entity IDs into training and test subsets
3. Run **RandomizedSearchCV** for hyperparameter tuning on a Random Forest model
4. Evaluate accuracy on the test set
5. Save the trained model to `artifacts/models/random_forest_model.pkl`

```bash
python src/model_training.py
```

**Typical output:**

```
2025-10-16 13:51:34,756 - INFO - 🔧 Initialising Feature Store and running Model Training...
2025-10-16 13:51:34,757 - INFO - RedisFeatureStore initialised: host=localhost, port=6379, db=0
2025-10-16 13:51:34,758 - INFO - ModelTraining initialised.
2025-10-16 13:51:34,758 - INFO - 🚀 Starting Model Training pipeline...
2025-10-16 13:51:34,773 - INFO - Found 712 entities in Redis.
2025-10-16 13:51:34,775 - INFO - Extracting data from Redis...
2025-10-16 13:51:35,148 - INFO - Fetched 569 feature rows from Redis.
2025-10-16 13:51:35,149 - INFO - Extracting data from Redis...
2025-10-16 13:51:35,250 - INFO - Fetched 143 feature rows from Redis.
2025-10-16 13:51:35,255 - INFO - Prepared training data with 569 rows and 11 features.
2025-10-16 13:51:40,543 - INFO - Best parameters: {'n_estimators': 100, 'min_samples_split': 5, 'min_samples_leaf': 2, 'max_depth': 20}
2025-10-16 13:51:40,726 - INFO - ✅ Test Accuracy: 0.8322
2025-10-16 13:51:40,733 - INFO - 📦 Model saved at: artifacts/models/random_forest_model.pkl
2025-10-16 13:51:40,733 - INFO - 🏁 End of Model Training pipeline.
```

## 🗂️ Updated Project Structure

```
mlops-titanic-survival-prediction/
├── artifacts/
│   ├── raw/
│   │   ├── titanic_train.csv
│   │   └── titanic_test.csv
│   ├── processed/
│   └── models/                        # 🧠 Stores trained ML model artefacts
│       └── random_forest_model.pkl
├── config/
│   ├── database_config.py
│   └── paths_config.py
├── notebook/
│   └── titanic.ipynb
├── src/
│   ├── custom_exception.py
│   ├── logger.py
│   ├── data_ingestion.py
│   ├── feature_store.py
│   ├── feature_processing.py
│   └── model_training.py              # 🧩 Trains, tunes, evaluates, and saves model
├── logs/
│   └── log_YYYY-MM-DD.log
├── requirements.txt
├── setup.py
└── README.md                          # You are here
```

## 🔗 How this stage fits the pipeline

**Raw data** (PostgreSQL → CSV) ➜
**Feature engineering** (`feature_processing.py`) ➜
**Feature storage** (Redis) ➜
**Model training** (`model_training.py`) ➜
**Saved model artefact** (`artifacts/models/random_forest_model.pkl`)

This marks the transition from **feature preparation** to **machine learning model training**, where features created and stored in previous stages are now leveraged to train and persist a predictive model.

## 🛠️ Quick tips

* Ensure Redis is running (`docker ps`) before executing the training script
* The model artefact (`random_forest_model.pkl`) can later be loaded for inference or retraining
* All logs are stored in `logs/log_YYYY-MM-DD.log` for traceability
* If you re-run training, the model file is automatically overwritten with the latest version

## 🚀 Next stage — Training Pipeline

The next branch evolves this into a **modular training pipeline**, integrating:

* Configurable model selection and hyperparameter search
* Automated saving of model metadata and performance metrics
* Seamless linkage to model registry and inference stages