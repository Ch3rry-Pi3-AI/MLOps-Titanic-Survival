# 🧠 `src/` README — Core Pipeline Modules

The `src/` directory contains the **core functional modules** for the  
**MLOps Titanic Survival Prediction** project.  
It includes utilities for **logging**, **error handling**, and **data ingestion**, ensuring that all components of the pipeline maintain a consistent, traceable, and reproducible structure.

## 📁 Folder Overview

```text
src/
├─ custom_exception.py     # Unified and detailed exception handling
├─ logger.py               # Centralised logging configuration (UTF-8)
└─ data_ingestion.py       # Data extraction pipeline from PostgreSQL to raw artifacts
````
## ⚙️ `data_ingestion.py` — Data Extraction Pipeline

### Purpose

Implements the **DataIngestion** class, responsible for:

* Connecting to the **PostgreSQL** database defined in `config/database_config.py`.
* Extracting the Titanic dataset from the `public.titanic` table.
* Splitting the data into **training** and **test** sets.
* Saving both CSVs into the local `artifacts/raw/` directory.

This script integrates with the project’s:

* Centralised logging (`src/logger.py`)
* Custom exception handling (`src/custom_exception.py`)
* Configuration management (`config/database_config.py`, `config/paths_config.py`)

### Key Features

| Feature                              | Description                                                              |
| :----------------------------------- | :----------------------------------------------------------------------- |
| 🧩 **SQLAlchemy Integration**        | Uses SQLAlchemy engine for efficient and compatible database querying.   |
| 🗃️ **Automatic Directory Creation** | Creates `artifacts/raw/` dynamically if missing.                         |
| 🔁 **Train/Test Split**              | Splits the dataset (80/20) using scikit-learn’s `train_test_split`.      |
| 🧾 **Logging + Exception Handling**  | Every stage is logged and wrapped in custom exceptions for traceability. |

### Example Usage

```bash
python src/data_ingestion.py
```

### Internal Workflow

```python
from config.database_config import DB_CONFIG
from config.paths_config import RAW_DIR
from src.data_ingestion import DataIngestion

data_ingestion = DataIngestion(DB_CONFIG, RAW_DIR)
data_ingestion.run()
```

### Typical Log Output

```
2025-10-15 20:05:47,180 - INFO - 🚀 Starting Data Ingestion Pipeline...
2025-10-15 20:05:49,362 - INFO - Data extracted successfully via SQLAlchemy. Shape: (891, 12)
2025-10-15 20:05:49,372 - INFO - Data successfully split and saved.
Train: artifacts/raw/titanic_train.csv (712, 12), Test: artifacts/raw/titanic_test.csv (179, 12)
2025-10-15 20:05:49,372 - INFO - ✅ Data Ingestion Pipeline completed successfully.
```



## ⚠️ `custom_exception.py` — Unified Error Handling

### Purpose

Provides a **CustomException** class that enriches raised errors with:

* The **file name** and **line number** where the error occurred.
* A formatted **traceback** for debugging complex failures.
* Flexible constructor logic that accepts:

  * the `sys` module,
  * an exception instance, or
  * nothing (defaults to the current `sys.exc_info()`).

### Key Features

* Produces readable, context-rich tracebacks for Airflow and local debugging.
* Works seamlessly across all stages — from data ingestion to model training.
* Prevents missing-argument errors when raising dynamically within pipeline code.

### Example Usage

```python
from src.custom_exception import CustomException
import sys

try:
    result = 10 / 0
except Exception as e:
    raise CustomException("Division error", sys) from e
```

### Example Output

```
Error in src/data_ingestion.py, line 82: Division error
Traceback (most recent call last):
  File "src/data_ingestion.py", line 82, in <module>
    result = 10 / 0
ZeroDivisionError: division by zero
```



## 🪵 `logger.py` — Centralised Logging (UTF-8 Enabled)

### Purpose

Defines a **standardised logging system** that outputs logs both to console and to a daily log file (`logs/log_YYYY-MM-DD.log`), with full UTF-8 support for emojis and symbols.

### Log File Format

| Property  | Example                                     |
| :-------- | :------------------------------------------ |
| Directory | `logs/`                                     |
| File name | `log_2025-10-15.log`                        |
| Format    | `%(asctime)s - %(levelname)s - %(message)s` |

### Example Usage

```python
from src.logger import get_logger

logger = get_logger(__name__)
logger.info("🚀 Data ingestion started.")
logger.error("❌ Failed to connect to database.")
```

### Example Output

```
2025-10-15 20:12:45,103 - INFO - 🚀 Starting Data Ingestion Pipeline...
2025-10-15 20:12:48,392 - INFO - ✅ Data Ingestion Pipeline completed successfully.
```



## 🧩 Integration Guidelines

| Module Type  | Use `CustomException` for…             | Use `get_logger` for…                          |
| ------------ | -------------------------------------- | ---------------------------------------------- |
| Airflow DAGs | Database or network operation failures | Logging DAG/task progress or run status        |
| ETL Scripts  | Transformation or extraction errors    | Progress messages (e.g. “Extracted 891 rows.”) |
| Pipelines    | Model training/inference exceptions    | Performance and validation metrics             |

### Combined Example

```python
from src.logger import get_logger
from src.custom_exception import CustomException
import sys

logger = get_logger(__name__)

def extract_data():
    try:
        logger.info("Starting data extraction...")
        raise ValueError("Missing column detected.")
    except Exception as e:
        logger.error("Extraction failed.")
        raise CustomException("ETL extraction error", sys) from e
```



✅ **In summary:**

* `data_ingestion.py` → Handles data extraction, splitting, and saving from PostgreSQL.
* `custom_exception.py` → Provides consistent, informative exception handling.
* `logger.py` → Provides timestamped, UTF-8-enabled logging for all modules.

Together, these files form the **core operational layer** of the MLOps Titanic Survival Prediction pipeline — ensuring that every workflow step is **observable**, **robust**, and **maintainable**.