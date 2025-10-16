# 🚀 Data Ingestion — PostgreSQL ➜ `artifacts/raw/` (train/test split)

This stage ingests the **Titanic** table from **PostgreSQL**, splits it into **train/test**, and writes CSVs under `artifacts/raw/`.  
It uses centralised configuration in `config/` and a single ingestion script in `src/`.

## 🗂️ Project Structure (relevant files)

```text
mlops-titanic-survival-prediction/
├─ config/
│  ├─ database_config.py     # 🗄️ DB connection parameters (host, port, dbname, user, password)
│  └─ paths_config.py        # 📁 Paths: artifacts/raw, titanic_train.csv, titanic_test.csv
└─ src/
   └─ data_ingestion.py      # ⚙️ Extracts from Postgres, splits, saves CSVs
````

## 🎯 What This Does

1. 🧩 Connects to PostgreSQL using `config/database_config.py`.
2. 🧠 Runs `SELECT * FROM public.titanic`.
3. ✂️ Splits 80/20 with `train_test_split`.
4. 💾 Saves to:

   * `artifacts/raw/titanic_train.csv`
   * `artifacts/raw/titanic_test.csv`
 
## ⚙️ Configuration

### 🗄️ `config/database_config.py`

Edit these if your database isn’t using local defaults:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres",
    "dbname": "postgres",
}
```

### 📁 `config/paths_config.py`

Paths already defined for this stage:

```python
RAW_DIR = "artifacts/raw"
TRAIN_PATH = os.path.join(RAW_DIR, "titanic_train.csv")
TEST_PATH  = os.path.join(RAW_DIR, "titanic_test.csv")
PROCESSED_DIR = "artifacts/processed"
```

## ▶️ Run It

From the project root:

```powershell
python src/data_ingestion.py
```

Expected log output (console and `logs/log_YYYY-MM-DD.log`):

```
INFO - 🚀 Starting Data Ingestion Pipeline...
INFO - Data extracted successfully via SQLAlchemy. Shape: (891, 12)
INFO - Data successfully split and saved.
Train: artifacts/raw/titanic_train.csv ((712, 12)), Test: artifacts/raw/titanic_test.csv ((179, 12))
INFO - ✅ Data Ingestion Pipeline completed successfully.
```

Check the output files:

```powershell
dir artifacts\raw
# titanic_train.csv
# titanic_test.csv
```

## 🧠 How It Works (internals)

`src/data_ingestion.py` performs the following steps:

* 🧩 Builds a SQLAlchemy engine using credentials from `DB_CONFIG`.
* 🗃️ Executes a query (`SELECT * FROM public.titanic`).
* ✂️ Splits the DataFrame with `train_test_split(test_size=0.2, random_state=42)`.
* 💾 Writes train/test CSVs to paths defined in `paths_config.py`.

## 🧰 Troubleshooting

* 💬 **Unicode sequences (`\u2705`, `\U0001f680`) in logs**
  Your logger is UTF-8 enabled, but ensure your terminal also uses UTF-8 (Windows: `chcp 65001`) to display emojis correctly.

* ⚠️ **Pandas DBAPI2 warning**
  Already handled — the ingestion uses SQLAlchemy, which avoids this warning entirely.

* 🧩 **Dependency versions (Python 3.13)**
  Make sure `numpy>=2.1`, `scipy>=1.11`, `scikit-learn>=1.6`, and `psycopg2-binary>=2.9.11` are installed.

## 🔗 Quick Integration Example

Use the class directly in another script or notebook:

```python
from config.database_config import DB_CONFIG
from config.paths_config import RAW_DIR
from src.data_ingestion import DataIngestion

ing = DataIngestion(DB_CONFIG, RAW_DIR)
ing.run()
```

## 🛠️ Next Steps

* 🧪 Add a simple `validate_ingestion.py` to verify row counts and schema consistency.
* 🔁 Extend ingestion for incremental or conditional loads.
* 🧮 Add preprocessing scripts that read from `artifacts/raw/` and write to `artifacts/processed/`.