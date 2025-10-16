# ⚙️ **Configuration Directory — `config/`**

The `config/` directory defines all **centralised configuration files** used by the **MLOps Titanic Survival Prediction** project.  
It separates **environment-specific** and **pipeline-specific** settings, ensuring a **reproducible, maintainable, and scalable** workflow across all development stages.

At this stage, configuration focuses on **data ingestion and storage structure**, with additional modules (e.g., training, monitoring) to be added as the pipeline evolves.

## 🗂️ **Folder Structure**

```

mlops-titanic-survival-prediction/
└── config/
├── paths_config.py        # Centralised directory and file path references
└── database_config.py     # PostgreSQL database connection configuration

````

## 🎯 **Purpose**

These files ensure **consistent and maintainable configuration management** throughout the project — especially during data ingestion and database loading stages.

| File                 | Description                                                                                     |
| -------------------- | ----------------------------------------------------------------------------------------------- |
| `paths_config.py`    | Defines directory and file paths for raw and processed data under the `artifacts/` hierarchy.   |
| `database_config.py` | Stores connection parameters for PostgreSQL, ensuring unified access across ingestion scripts.   |



## 🧱 **Overview of `paths_config.py`**

This file centralises all **key path references** for data ingestion and processing, keeping the pipeline modular and free from hardcoded values.

### 📋 **Path Groups**

| Category            | Description                              | Example Output / Directory     |
| :------------------ | :--------------------------------------- | :----------------------------- |
| **Data Ingestion**  | Stores raw Titanic CSV files.            | `artifacts/raw/`               |
| **Data Processing** | Stores cleaned or preprocessed datasets. | `artifacts/processed/`         |

### 🧩 **Highlights**

```python
# 🚢 DATA INGESTION
RAW_DIR = "artifacts/raw"
TRAIN_PATH = os.path.join(RAW_DIR, "titanic_train.csv")
TEST_PATH = os.path.join(RAW_DIR, "titanic_test.csv")

# 🧮 DATA PROCESSING
PROCESSED_DIR = "artifacts/processed"
````

### 🧠 **Notes**

* Keeps all artifact directories under `artifacts/` for a clear, standardised structure.
* Ensures that ingestion and preprocessing scripts reference consistent paths.
* Future sections (e.g., model artifacts, metrics) can be easily added without restructuring.



## 🗄️ **Overview of `database_config.py`**

This file defines **PostgreSQL connection details** used during data ingestion and loading stages.

### 🧩 **Highlights**

```python
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres",
    "dbname": "postgres",
}
```

### 🧠 **Notes**

* These credentials are intended for **local development only**.
* For production, migrate to environment variables or secret management tools (e.g., `.env`, Vault, or Airflow connections).
* The configuration can be accessed directly in ingestion or transformation scripts:

```python
from config.database_config import DB_CONFIG
import psycopg2

conn = psycopg2.connect(**DB_CONFIG)
```



## ✅ **Best Practices**

* Never hardcode file paths or database credentials — always import from `config/`.
* Use `os.makedirs(..., exist_ok=True)` in scripts to ensure artifact directories exist.
* Treat this directory as the **single source of truth** for configuration settings.
* Future configuration (e.g., `config.yaml` for model parameters) should also be placed here.

Together, these configuration files make your early pipeline **portable, maintainable, and environment-agnostic**, providing a solid foundation for future expansion into preprocessing, model training, and deployment.