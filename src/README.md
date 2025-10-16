# `src/` README — Core Utilities (Custom Exception & Logger)

This folder contains **project-wide utilities** for **error handling** and **logging**, ensuring that all modules within the MLOps Titanic Survival Prediction pipeline follow a consistent and traceable debugging and monitoring pattern.



## 📁 Folder Overview

```text
src/
├─ custom_exception.py   # Unified and detailed exception handling
└─ logger.py             # Centralised logging configuration
```



## ⚠️ `custom_exception.py` — Unified Error Handling

### Purpose

Provides a **CustomException** class that enriches raised errors with:

* The **file name** and **line number** where the error occurred.
* A formatted **traceback** (useful for debugging complex Airflow or pipeline failures).
* A flexible constructor that works whether you pass:

  * the `sys` module,
  * an exception instance, or
  * nothing (falls back to the current `sys.exc_info()`).

### Key Features

* Produces readable, context-rich tracebacks in logs or Airflow task logs.
* Prevents missing-argument errors when raising exceptions dynamically.
* Works seamlessly across your DAGs, pipeline modules, and testing scripts.

### Example Usage

```python
from src.custom_exception import CustomException
import sys

try:
    result = 10 / 0
except Exception as e:
    # Either style is acceptable:
    raise CustomException("Division error", sys) from e
    # or
    raise CustomException("Division error", e)
```

### Output Example

```
Error in /usr/local/airflow/dags/extract_data_from_gcp.py, line 42: Division error
Traceback (most recent call last):
  File "/usr/local/airflow/dags/extract_data_from_gcp.py", line 42, in <module>
    result = 10 / 0
ZeroDivisionError: division by zero
```

This ensures all pipeline-related errors display clearly in logs and in the Airflow UI.



## 🪵 `logger.py` — Centralised Logging

### Purpose

Provides a **standardised logging setup** for the entire project.
Every log entry is timestamped and written to a date-stamped file inside a dedicated `logs/` directory.

### Log File Format

* Directory: `logs/`
* File name: `log_YYYY-MM-DD.log`
* Example: `logs/log_2025-10-14.log`

### Default Configuration

* Logging **level**: `INFO`
* Format:

  ```
  %(asctime)s - %(levelname)s - %(message)s
  ```

### Example Usage

```python
from src.logger import get_logger

logger = get_logger(__name__)
logger.info("Model training started.")
logger.error("Failed to connect to database.")
```

### Output Example

```
2025-10-14 22:10:21,984 - INFO - Model training started.
2025-10-14 22:10:21,985 - ERROR - Failed to connect to database.
```



## 🧩 Integration Guidelines

| Module Type  | Use `CustomException` for…                       | Use `get_logger` for…                        |
| ------------ | ------------------------------------------------ | -------------------------------------------- |
| Airflow DAGs | Wrapping operator code, file I/O, or DB failures | Logging DAG run status, data transfer counts |
| ETL Scripts  | Transformation and load failures                 | Progress messages (“Loaded 6060 rows…”)      |
| Pipelines    | Model training and inference exceptions          | Metrics, timing, or validation logs          |

**Tip:** Combine both for best traceability:

```python
from src.logger import get_logger
from src.custom_exception import CustomException
import sys

logger = get_logger(__name__)

def process_data():
    try:
        logger.info("Starting data processing...")
        raise ValueError("Missing column detected.")
    except Exception as e:
        logger.error("Processing failed.")
        raise CustomException("ETL data processing error", sys) from e
```



✅ **In summary:**

* `custom_exception.py` ensures **consistent, informative error reporting**.
* `logger.py` ensures **consistent, timestamped logging**.
  Together they form the **foundation for reliability and observability** across the MLOps Titanic project.