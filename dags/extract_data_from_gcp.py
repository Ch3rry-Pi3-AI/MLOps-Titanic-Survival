"""
extract_data_from_gcp.py
------------------------
Airflow DAG to extract a CSV file from Google Cloud Storage (GCS) and load it
into a PostgreSQL table using pandas and SQLAlchemy.

Overview
--------
1) List objects in a specified GCS bucket (light sanity check).
2) Download the target CSV object to a shared filesystem path inside the worker.
3) Load the CSV into Postgres, replacing the target table atomically.

Why this design?
----------------
- Uses Airflow's managed connections:
  * `google_cloud_default` for GCS access
  * `postgres_default`     for Postgres via `PostgresHook`
- Hands a **SQLAlchemy Connection** (not just Engine) to `pandas.DataFrame.to_sql`
  to avoid cursor-detection quirks and to wrap writes in a transaction.
- Adds early file-existence validation and explicit log messages for observability.

Usage
-----
- Ensure Airflow connections exist:
    * Conn ID: `google_cloud_default` (with appropriate service account/ADC)
    * Conn ID: `postgres_default`     (host/db/user/password/port set)
- Place this file in your Airflow `dags/` directory.
- Trigger the DAG `extract_titanic_data` from the UI or CLI.

Notes
-----
- Set `SCHEMA` if you want a non-default schema (e.g. "public").
- The load step uses `if_exists="replace"` (idempotent for prototyping).
  Adjust to "append" as needed for production.
- For large loads consider tuning `chunksize` and `method`.
"""

# -------------------------------------------------------------------
# Standard Library Imports
# -------------------------------------------------------------------
from datetime import datetime
from pathlib import Path
from typing import Optional

# -------------------------------------------------------------------
# Third-Party Imports
# -------------------------------------------------------------------
import pandas as pd
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.gcs import GCSListObjectsOperator
from airflow.providers.google.cloud.transfers.gcs_to_local import GCSToLocalFilesystemOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
BUCKET: str = "mlops-titanic-survival-precition-bucket"
OBJECT_NAME: str = "Titanic-Dataset.csv"
LOCAL_FILE: str = "/usr/local/airflow/include/Titanic-Dataset.csv"  # shared volume path
POSTGRES_CONN_ID: str = "postgres_default"
TABLE_NAME: str = "titanic"
SCHEMA: Optional[str] = None  # e.g. "public" if you want to be explicit

# -------------------------------------------------------------------
# Task Functions
# -------------------------------------------------------------------
def load_to_sql(file_path: str) -> None:
    """
    Load the Titanic dataset CSV into a PostgreSQL table using SQLAlchemy.

    Parameters
    ----------
    file_path : str
        Local path to the Titanic CSV file downloaded from GCS.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist at the given path.
    """
    # Validate file existence early (fail fast with a clean error)
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found at: {path}")

    # Retrieve a SQLAlchemy Engine via the Airflow PostgresHook
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    engine = hook.get_sqlalchemy_engine()
    print(f"[load_to_sql] Using database URL: {engine.url}")  # safe: password masked

    # Read CSV into a DataFrame
    df = pd.read_csv(path)
    print(f"[load_to_sql] Read {len(df)} rows from: {path}")

    # IMPORTANT:
    # Pass a SQLAlchemy Connection (transactional) to pandas, not the raw Engine.
    # Using engine.begin() ensures commit/rollback semantics around the `to_sql` call.
    with engine.begin() as conn:
        df.to_sql(
            name=TABLE_NAME,
            con=conn,               # Connection, not Engine
            schema=SCHEMA,
            if_exists="replace",    # replace table for clean, idempotent loads
            index=False,
            method="multi",         # batched INSERTs
            chunksize=1_000,        # tune for your workload
        )

        # Optional post-load smoke test (prints to task logs)
        preview = pd.read_sql(f"SELECT * FROM {TABLE_NAME} LIMIT 5;", conn)
        print("[load_to_sql] Preview of loaded data (first 5 rows):")
        print(preview.to_string(index=False))

    # Release pooled connections proactively
    engine.dispose()
    print(f"[load_to_sql] Successfully loaded {len(df)} rows into table '{TABLE_NAME}'")

# -------------------------------------------------------------------
# DAG Definition
# -------------------------------------------------------------------
with DAG(
    dag_id="extract_titanic_data",
    start_date=datetime(2023, 1, 1),
    schedule=None,      # modern replacement for schedule_interval=None
    catchup=False,
    tags=["titanic", "gcs", "postgres"],
) as dag:

    # Step 1: List available files in the bucket (observability)
    list_files = GCSListObjectsOperator(
        task_id="list_files",
        bucket=BUCKET,
        gcp_conn_id="google_cloud_default",
    )

    # Step 2: Download the dataset from GCS to a local shared volume
    download_file = GCSToLocalFilesystemOperator(
        task_id="download_file",
        bucket=BUCKET,
        object_name=OBJECT_NAME,
        filename=LOCAL_FILE,
        gcp_conn_id="google_cloud_default",
    )

    # Step 3: Load the CSV into PostgreSQL
    load_data = PythonOperator(
        task_id="load_to_sql",
        python_callable=load_to_sql,
        op_kwargs={"file_path": LOCAL_FILE},
    )

    # Orchestration: list → download → load
    list_files >> download_file >> load_data