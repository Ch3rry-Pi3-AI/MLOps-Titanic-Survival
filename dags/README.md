# `dags/` README — ETL DAG: `extract_data_from_gcp.py`

A compact guide to the DAG that powers the **GCS ➜ Airflow ➜ Postgres** load in this branch.

## What this DAG does

1. **Lists** objects in a GCS bucket (`GCSListObjectsOperator`).
2. **Downloads** `Titanic-Dataset.csv` from GCS to the shared container volume at `/usr/local/airflow/include/` (`GCSToLocalFilesystemOperator`).
3. **Loads** the CSV into **PostgreSQL** table `titanic` using **pandas + SQLAlchemy Connection** obtained from `PostgresHook`.

It is **manual-trigger only** (`schedule=None`, `catchup=False`) and tagged `["titanic", "gcs", "postgres"]`.

## File map

```text
dags/
├─ .airflowignore
├─ exampledag.py
└─ extract_data_from_gcp.py   # This DAG
```

## Configure these constants (top of the file)

```python
BUCKET = "mlops-titanic-survival-precition-bucket"   # your GCS bucket
OBJECT_NAME = "Titanic-Dataset.csv"                  # object to pull
LOCAL_FILE = "/usr/local/airflow/include/Titanic-Dataset.csv"
POSTGRES_CONN_ID = "postgres_default"
TABLE_NAME = "titanic"
SCHEMA = None  # use "public" to be explicit if you prefer
```

## Required Airflow connections

Create these in **Airflow UI → Admin → Connections**:

* **`google_cloud_default`**
  Extra JSON must point to the mounted key:

  ```json
  {
    "key_path": "/usr/local/airflow/include/gcp-key.json",
    "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
  }
  ```

  Make sure your **service-account key** file is placed at:

  ```
  include/gcp-key.json
  ```

  (This folder is mounted into the container at `/usr/local/airflow/include` via `.astro/config.yaml`.)

* **`postgres_default`**
  Host should be the **Postgres container name** from Docker Desktop (e.g. `ml-ops-titanic-survival-prediction_XXXXXX-postgres-1`), port `5432`, user `postgres`, password `postgres`, database `postgres`.

## How to run

1. Start the stack:

   ```bash
   astro dev start
   ```
2. Open **Airflow UI** → **DAGs** → `extract_titanic_data` → **Trigger DAG**.
3. On success you’ll have table **`public.titanic`** in the embedded Postgres.

## Quick verification

Shell into the container and query Postgres:

```bash
astro dev bash
PGPASSWORD=postgres psql -h <postgres-container-name> -p 5432 -U postgres -d postgres -c "SELECT * FROM public.titanic LIMIT 5;"
```

## Implementation notes

* The load step uses:

  ```python
  engine = PostgresHook(POSTGRES_CONN_ID).get_sqlalchemy_engine()
  with engine.begin() as conn:
      df.to_sql(TABLE_NAME, con=conn, schema=SCHEMA, if_exists="replace", index=False, method="multi", chunksize=1000)
  ```

  Passing a **transactional SQLAlchemy Connection** avoids the common

  > “pandas only supports SQLAlchemy connectable …”
  > error and ensures atomic writes.
* If your GCS object name or bucket differs, update `OBJECT_NAME` / `BUCKET`.

## Common issues & fixes

* **`FileNotFoundError: CSV file not found`**
  Ensure the GCS object exists and the path is downloaded to `/usr/local/airflow/include/…`. The volume mount must be present in `.astro/config.yaml`.
* **Permission or 403 from GCS**
  Confirm the service account has **Storage Object Viewer** (and Admin if needed) on the bucket and that `google_cloud_default` points to the correct `gcp-key.json`.
* **Can’t connect to Postgres**
  Double-check the **container name** used as the host, and that the stack is running.

That’s it—this DAG is your thin, reliable bridge from **GCS** to **Postgres** for the Titanic dataset.