"""
data_ingestion.py
-----------------
Implements the DataIngestion class responsible for extracting
the Titanic dataset from a PostgreSQL database and saving it
into the local `artifacts/raw/` directory.

This module integrates with:
- Centralised logging (`src.logger`)
- Custom exception handling (`src.custom_exception`)
- Configuration management (`config/database_config.py` and `config/paths_config.py`)

Usage
-----
Example:
    python src/data_ingestion.py

Notes
-----
- Requires a valid local or remote PostgreSQL connection defined in `config/database_config.py`.
- Automatically creates directories under `artifacts/raw/` if they do not exist.
- Splits the extracted dataset into training and test sets.
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Standard & Third-Party Imports
# -------------------------------------------------------------------
import os
import sys
import psycopg2
import pandas as pd
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# -------------------------------------------------------------------
# Internal Imports
# -------------------------------------------------------------------
from src.logger import get_logger
from src.custom_exception import CustomException
from config.database_config import DB_CONFIG
from config.paths_config import *

# -------------------------------------------------------------------
# Logger Setup
# -------------------------------------------------------------------
logger = get_logger(__name__)


# -------------------------------------------------------------------
# Class: DataIngestion
# -------------------------------------------------------------------
class DataIngestion:
    """
    Handles the ingestion of Titanic data from a PostgreSQL database.

    This includes:
    - Establishing a database connection using the provided parameters.
    - Extracting data from the `public.titanic` table.
    - Splitting the dataset into training and test sets.
    - Saving the resulting CSVs to `artifacts/raw/`.

    Parameters
    ----------
    db_params : dict
        Dictionary containing PostgreSQL connection parameters.
    output_dir : str
        Directory path where the raw CSV files will be stored.
    """

    def __init__(self, db_params: dict, output_dir: str):
        self.db_params = db_params
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"DataIngestion initialised with output directory: {self.output_dir}")

    # -------------------------------------------------------------------
    # Method: connect_to_db (psycopg2)
    # -------------------------------------------------------------------
    def connect_to_db(self):
        """
        Establishes a connection to the PostgreSQL database with psycopg2.

        Returns
        -------
        psycopg2.extensions.connection
            Active database connection object.

        Raises
        ------
        CustomException
            If the connection to the database cannot be established.
        """
        try:
            conn = psycopg2.connect(
                host=self.db_params["host"],
                port=self.db_params["port"],
                dbname=self.db_params["dbname"],
                user=self.db_params["user"],
                password=self.db_params["password"],
            )
            logger.info("Database connection established successfully (psycopg2).")
            return conn

        except Exception as e:
            logger.error(f"Error while establishing database connection: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: extract_data (SQLAlchemy)
    # -------------------------------------------------------------------
    def extract_data(self) -> pd.DataFrame:
        """
        Extracts Titanic data from the database using SQLAlchemy.

        Returns
        -------
        pd.DataFrame
            Extracted Titanic dataset from `public.titanic`.

        Raises
        ------
        CustomException
            If any error occurs while building the engine or running the query.
        """
        try:
            # Build a SQLAlchemy URL to avoid string-concatenation pitfalls
            engine_url = URL.create(
                drivername="postgresql+psycopg2",
                username=self.db_params["user"],
                password=self.db_params["password"],
                host=self.db_params["host"],
                port=self.db_params["port"],
                database=self.db_params["dbname"],
            )

            # Create engine; pre-ping ensures stale connections are detected/recycled
            engine = create_engine(engine_url, pool_pre_ping=True)

            query = "SELECT * FROM public.titanic"

            # Use a connection context for clean resource handling
            with engine.connect() as conn:
                df = pd.read_sql_query(sql=query, con=conn)

            # Explicitly dispose the engine (closes pooled connections)
            engine.dispose()

            logger.info(f"Data extracted successfully via SQLAlchemy. Shape: {df.shape}")
            return df

        except Exception as e:
            logger.error(f"Error while extracting data via SQLAlchemy: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: save_data
    # -------------------------------------------------------------------
    def save_data(self, df: pd.DataFrame) -> None:
        """
        Splits the dataset into training and test subsets,
        then saves them as CSV files in the `artifacts/raw/` directory.

        Parameters
        ----------
        df : pd.DataFrame
            Extracted Titanic dataset.

        Raises
        ------
        CustomException
            If saving or splitting fails.
        """
        try:
            train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
            train_df.to_csv(TRAIN_PATH, index=False)
            test_df.to_csv(TEST_PATH, index=False)
            logger.info(
                f"Data successfully split and saved.\n"
                f"Train: {TRAIN_PATH} ({train_df.shape}), Test: {TEST_PATH} ({test_df.shape})"
            )

        except Exception as e:
            logger.error(f"Error while saving split data: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: run
    # -------------------------------------------------------------------
    def run(self) -> None:
        """
        Executes the complete data ingestion workflow.

        Steps
        -----
        1. Extract data from the `public.titanic` table (SQLAlchemy).
        2. Split the dataset into training and test sets.
        3. Save the datasets under `artifacts/raw/`.

        Raises
        ------
        CustomException
            If any stage of the ingestion pipeline fails.
        """
        try:
            logger.info("🚀 Starting Data Ingestion Pipeline...")
            df = self.extract_data()
            self.save_data(df)
            logger.info("✅ Data Ingestion Pipeline completed successfully.")

        except Exception as e:
            logger.error(f"❌ Error during Data Ingestion Pipeline: {e}")
            raise CustomException(str(e), sys)


# -------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    data_ingestion = DataIngestion(DB_CONFIG, RAW_DIR)
    data_ingestion.run()