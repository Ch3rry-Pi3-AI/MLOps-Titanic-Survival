# ETL Pipeline — GCP ➜ Airflow (Astro) ➜ Postgres ➜ DBeaver

This branch is the **second stage** of the project (after `00_project_setup`).
It builds a **working ETL pipeline** that:

1. **Stores** the Titanic CSV in a **Google Cloud Storage (GCS) bucket**
2. **Pulls** it into an **Astro Airflow** environment
3. **Loads** it into **PostgreSQL** running inside the Astro stack
4. **Verifies** the load with `psql` and explores it using **DBeaver**

Everything below is written to be **copy-paste runnable on Windows**. Mac/Linux users can adapt the commands accordingly.



## 📦 Project Structure (tree)

```text
mlops-titanic-survival-prediction/
├─ .astro/
│  └─ config.yaml                       # Astro env config (not tracked by git by default)
├─ dags/
│  ├─ .airflowignore
│  ├─ exampledag.py
│  └─ extract_data_from_gcp.py          # DAG that lists, downloads, and loads CSV to Postgres
├─ include/
│  └─ gcp-key.json                      # ← Your downloaded GCP service-account key (rename to this)
├─ img/
├─ artifacts/
├─ config/
├─ pipeline/
├─ plugins/
├─ src/
├─ tests/
├─ venv/                                 # Local venv (ignored by git)
├─ .dockerignore
├─ .env
├─ .gitignore
├─ .python-version
├─ airflow_settings.yaml
├─ Dockerfile                            # Root Dockerfile for Astro image build
├─ packages.txt
├─ pyproject.toml
├─ README.md                             # You are here
└─ requirements.txt
```



## 🧭 High-Level Flow

1. **Create a GCS bucket** and **Service Account**; download the **JSON key**
2. **Copy** the key to `include/gcp-key.json`
3. **Install Docker Desktop** and **Astro CLI**, initialise the project, and **start** the local Airflow stack
4. In Airflow UI, **create connections**:

   * `google_cloud_default` ➜ points at `include/gcp-key.json`
   * `postgres_default` ➜ points at the Postgres container inside the Astro stack
5. **Trigger** the `extract_titanic_data` DAG
6. **Verify** with `psql` and **inspect** with **DBeaver**



## ☁️ Step 1 — Google Cloud Platform setup

### 1.1 Create a GCS bucket

* In the GCP Console, create a new **Cloud Storage bucket** for this project.
* **Untick** **“Enforce public access prevention on this bucket”**.

![Create Bucket](img/etl/create_bucket.png)

### 1.2 Create a Service Account & key (JSON)

* Navigation Menu → **IAM & Admin** → **Service Accounts** → **+ Create service account**
* Give it a sensible name and continue.

![Create Service Account](img/etl/create_service_account.png)

* To the right of your new service account: **⋮ → Manage keys → Add key → Create new key → JSON**.
* Download the JSON file.

![Download Private Key](img/etl/private_key.png)

### 1.3 Grant the Service Account access to the bucket

* Go back to **Cloud Storage → Buckets**
* On your project bucket: **⋮ → Edit access → + Add principal**
* Choose your **service account** and add roles:

  * **Storage Object Admin**
  * **Storage Object Viewer**

### 1.4 Upload the Titanic CSV to the bucket

* Click into your bucket and **Upload** the data file (e.g. `Titanic-Dataset.csv`).
* Example public source for the Titanic CSV (alternative to Kaggle):
  **[datasciencedojo/datasets – titanic.csv](https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv)**
  Save it locally first if you prefer, then upload to GCS.

> Your DAG expects the object name `Titanic-Dataset.csv`. If your uploaded file name differs, update `OBJECT_NAME` in the DAG accordingly.



## 🐳 Step 2 — Prerequisites on your machine

### 2.1 Install and run Docker Desktop

* Download & install: **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**
* **Start Docker Desktop** and ensure it’s running before using Astro.

### 2.2 Install the Astro CLI (Windows instructions)

* Astro CLI docs: **[Get started with Astro CLI](https://www.astronomer.io/docs/astro/cli/get-started-cli)**
* Open **PowerShell (not in a venv)** and run:

```powershell
winget install Astronomer.Astro
```

* If the command isn’t found after install, **close PowerShell and reopen it**. Then check:

```powershell
astro version
```

* If that fails, reinstall:

```powershell
winget uninstall Astronomer.Astro
winget install Astronomer.Astro
```

* Get the actual `astro.exe` path (for the shim later):

```powershell
Get-Command astro | Format-List Source,Path
```

Example output:

```
C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe
```

### 2.3 Make `astro` work **inside** your Python venv (Windows)

Activate your project venv:

```powershell
& C:/Users/HP/OneDrive/Documents/Projects/MLOps/MLOps-Titanic-Survival-Prediction/venv/Scripts/Activate.ps1
```

Create small **shim** launchers so `astro` is available while the venv is active. Replace `$ASTRO` with your exact path from above:

```powershell
$ASTRO = 'C:\Users\HP\AppData\Local\Microsoft\WinGet\Packages\Astronomer.Astro_Microsoft.Winget.Source_8wekyb3d8bbwe\astro.exe'
Set-Content -Path ".\venv\Scripts\astro.cmd" -Value "@echo off`r`n`"$ASTRO`" %*"
Set-Content -Path ".\venv\Scripts\astro.ps1" -Value "& `"$ASTRO`" $args"
```

Close PowerShell completely, reopen it, **activate the venv again**, then verify:

```powershell
astro version
```

You should see something like:

```
(venv) ...> Astro CLI Version: 1.36.0
```

> **Note:** Astro is a **system-level** tool that manages **Dockerised Airflow**. It’s not a Python package.
> The shim simply makes it convenient to call `astro` while your venv is active.



## 🛠️ Step 3 — Initialise Astro in this repo

From the project root:

```powershell
astro dev init
```

Type `y` when prompted. This creates:

* `.astro/` directory
* `dags/` and `include/` folders
* `.dockerignore`, `Dockerfile`, `packages.txt`, etc.

### 3.1 Place your GCP key in `include/`

Copy the **downloaded service-account JSON** into `include/` and **rename it** to:

```
include/gcp-key.json
```

> This path is **mounted** into the Airflow container and referenced by the Airflow GCP connection.

### 3.2 Set the Astro config

Open `.astro/config.yaml` and **replace contents** with:

```yaml
project:
  name: ml-ops-titanic-survival-prediction

deployments:
  - name: dev
    executor: celery
    image:
      name: ${IMAGE_NAME:-mlops-titanic:dev}
    env: dev
    volumes:
      - ./include:/usr/local/airflow/include
```

> **Why this matters:** `.astro/config.yaml` is typically **git-ignored**, so teammates won’t have it by default.
> The `volumes` entry **mounts** your local `include/` into the Airflow container at `/usr/local/airflow/include`, which is where the DAG and connection expect the GCP key and any local files.

### 3.3 Root Dockerfile (already present)

```dockerfile
ARG RUNTIME_VERSION=3.1-2
FROM astrocrpublic.azurecr.io/runtime:${RUNTIME_VERSION}
COPY requirements.txt /requirements.txt
```

This uses Astronomer’s Runtime base image and copies `requirements.txt` for dependency installation during the image build.



## 🚀 Step 4 — Start the local Airflow stack

Ensure **Docker Desktop** is running, then from the repo root:

```powershell
astro dev start
```

This builds and starts the Airflow environment and opens the **Airflow UI** in your browser.



## 🔗 Step 5 — Configure Airflow connections

In the **Airflow UI**: **Admin → Connections → + Add a connection**.

### 5.1 GCP connection (`google_cloud_default`)

Fill in as per the screenshot:

![Airflow GCP Connection](img/etl/airflow_gcp_connection.png)

In **Extra** (JSON), paste:

```json
{
  "key_path": "/usr/local/airflow/include/gcp-key.json",
  "scopes": [
    "https://www.googleapis.com/auth/cloud-platform"
  ]
}
```

Save.

### 5.2 Postgres connection (`postgres_default`)

Fill in as per the screenshot:

![Airflow Postgres Connection](img/etl/airflow_postgres_connection.png)

For the **Host**, open **Docker Desktop**, click your **Astro project** container group, expand to see services, and click the **postgres** container:

![Find Postgres Host](img/etl/postgres_host.png)

Copy the **container name** (e.g. `ml-ops-titanic-survival-prediction_1ce71e-postgres-1`) and use that as the host in the connection form.
Use port `5432`, user `postgres`, password `postgres`, database `postgres` (defaults for the Astro local stack).

Save.



## 📜 Step 6 — The DAG you’ll run

`dags/extract_data_from_gcp.py`:

* **Lists** objects in your GCS bucket
* **Downloads** `Titanic-Dataset.csv` into the mounted volume at `/usr/local/airflow/include/Titanic-Dataset.csv`
* **Loads** it into Postgres table `public.titanic` using a **transactional SQLAlchemy Connection** (via `PostgresHook`)

You should now see the DAG in **Airflow → DAGs**:

![DAG visible](img/etl/dag.png)

Click **Trigger DAG**, then **Trigger**. On success:

![DAG success](img/etl/dag_success.png)



## 🧪 Step 7 — Verify with `psql` inside the container

Open a shell into the webserver container:

```powershell
astro dev bash
```

Now connect to Postgres (substitute your **postgres container name** in `-h`):

```bash
PGPASSWORD=postgres psql -h ml-ops-titanic-survival-prediction_1ce71e-postgres-1 -p 5432 -U postgres -d postgres
```

You should see a `postgres=#` prompt. Try:

```sql
SELECT * FROM public.titanic LIMIT 5;
```

Expected sample style:

```
 PassengerId | Survived | Pclass |                        Name                         |  Sex   | Age | SibSp | Parch |      Ticket      |  Fare   | Cabin | Embarked
-------------+----------+--------+-----------------------------------------------------+--------+-----+-------+-------+------------------+---------+-------+----------
           1 |        0 |      3 | Braund, Mr. Owen Harris                             | male   |  22 |     1 |     0 | A/5 21171        |    7.25 |       | S
           2 |        1 |      1 | Cumings, Mrs. John Bradley (Florence Briggs Thayer) | female |  38 |     1 |     0 | PC 17599         | 71.2833 | C85   | C
           3 |        1 |      3 | Heikkinen, Miss. Laina                              | female |  26 |     0 |     0 | STON/O2. 3101282 |   7.925 |       | S
           4 |        1 |      1 | Futrelle, Mrs. Jacques Heath (Lily May Peel)        | female |  35 |     1 |     0 | 113803           |    53.1 | C123  | S
           5 |        0 |      3 | Allen, Mr. William Henry                            | male   |  35 |     0 |     0 | 373450           |    8.05 |       | S
(5 rows)
```

For table details:

```sql
\d+ public.titanic;
```

When done:

```sql
\q
exit
```

You’ll return to your host shell.



## 🐘 Step 8 — Inspect locally with DBeaver

1. Download & install **DBeaver**: **[dbeaver.io/download](https://dbeaver.io/download/)**

![DBeaver Install](img/etl/dbeaver_install.png)

2. Open DBeaver → **Database** → **New Database Connection** → **PostgreSQL**

![New Connection](img/etl/dbeaver_new_connection.png)

3. Set **Password** to `postgres`, and click **Test Connection**. If drivers are missing, choose to **Install** when prompted.

![DBeaver Config](img/etl/dbeaver_postgres_config.png)

![Test Connection](img/etl/dbeaver_test_connection.png)

4. Click **OK** then **Finish**. You should see your connection:

![DBeaver Connected](img/etl/dbeaver_postgres_db.png)

Expand: **Databases → postgres → Schemas → public → Tables** and find `titanic`.

Open **SQL Editor** (top bar) → **Open SQL script** and run:

```sql
SELECT *
FROM public.titanic;
```

Press **Ctrl + Enter** to execute. You should see the rows in the results grid.



## 🧩 Key Files (for reference)

* **DAG**: `dags/extract_data_from_gcp.py` (lists ➜ downloads ➜ loads)
* **Astro config**: `.astro/config.yaml` (mounted `include/` path, project name, image name)
* **GCP key**: `include/gcp-key.json` (your service-account JSON, not tracked by git)
* **Dockerfile**: root `Dockerfile` (Astronomer Runtime base + installs `requirements.txt`)



## ✅ You’re Done

You now have a **repeatable ETL** from **GCS → Airflow → Postgres**, verified via `psql`, and browsable in **DBeaver**.

**Next step:** Data ingestion using **psycopg2** (we’ll build on this table and build richer ingestion/transform routines).