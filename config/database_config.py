"""
database_config.py
------------------
Centralised database configuration for the
MLOps Titanic Survival Prediction project.

This module stores connection parameters for the PostgreSQL database
used throughout the data pipeline — including host, port, user, and
authentication details. Centralising this information ensures consistent
database access across all modules and prevents hardcoded credentials
from being scattered throughout the codebase.

Usage
-----
Example:
    from config.database_config import DB_CONFIG
    import psycopg2

    connection = psycopg2.connect(**DB_CONFIG)

Notes
-----
- These credentials are for local development only.
- For production, use environment variables or secret management tools
  (e.g., `.env`, Vault, or Airflow connections) instead of storing
  plaintext credentials in source code.
"""

# -------------------------------------------------------------------
# 🗄️ DATABASE CONNECTION CONFIGURATION
# -------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "postgres",
    "dbname": "postgres",
}