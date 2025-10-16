"""
feature_processing.py
---------------------
Implements the DataProcessing class responsible for loading, preprocessing,
balancing, and feature-storing Titanic data.

This stage prepares engineered features and pushes them into a lightweight
Redis-backed feature store for fast retrieval during model training and
inference.

This module integrates with:
- Centralised logging (`src.logger`)
- Custom exception handling (`src.custom_exception`)
- Feature store abstraction (`src.feature_store.RedisFeatureStore`)
- Path configuration (`config.paths_config`)

Usage
-----
Example:
    python src/feature_processing.py

Notes
-----
- Assumes train/test CSVs exist at paths configured in `config/paths_config.py`.
- Uses SMOTE to address class imbalance in the training data.
- Feature keys in Redis follow: `entity:<PassengerId>:features`.
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Temporary Import Path Hack (Option D)
# -------------------------------------------------------------------
# Ensure the project root (parent of this file's directory) is on sys.path
# so that `import src.*` and `import config.*` work when running this file
# as a script: `python src/feature_processing.py`.
#
# ⚠️ Note:
# - This is a pragmatic, script-friendly workaround.
# - Prefer installing the package in editable mode (`pip install -e .`)
#   or running as a module (`python -m src.feature_processing`) in the long run.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))

# -------------------------------------------------------------------
# Standard & Third-Party Imports
# -------------------------------------------------------------------
import pandas as pd
from imblearn.over_sampling import SMOTE
from typing import Any, Dict, Optional, List

# -------------------------------------------------------------------
# Internal Imports
# -------------------------------------------------------------------
from src.feature_store import RedisFeatureStore
from src.logger import get_logger
from src.custom_exception import CustomException
from config.paths_config import *  # e.g., TRAIN_PATH, TEST_PATH

# -------------------------------------------------------------------
# Logger Setup
# -------------------------------------------------------------------
logger = get_logger(__name__)


# -------------------------------------------------------------------
# Class: DataProcessing
# -------------------------------------------------------------------
class DataProcessing:
    """
    Handles data loading, preprocessing/feature engineering, class-imbalance
    handling, and writing engineered features to the Redis feature store.

    Parameters
    ----------
    train_data_path : str
        File path to the training CSV (e.g., `artifacts/raw/titanic_train.csv`).
    test_data_path : str
        File path to the test CSV (e.g., `artifacts/raw/titanic_test.csv`).
    feature_store : RedisFeatureStore
        An instance of the RedisFeatureStore for persisting features.

    Attributes
    ----------
    data : pd.DataFrame | None
        Loaded training data.
    test_data : pd.DataFrame | None
        Loaded test data (optional use).
    X_resampled : pd.DataFrame | None
        Resampled (SMOTE) feature matrix.
    y_resampled : pd.Series | None
        Resampled (SMOTE) target vector.
    """

    def __init__(
        self,
        train_data_path: str,
        test_data_path: str,
        feature_store: RedisFeatureStore,
    ) -> None:
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path

        self.data: Optional[pd.DataFrame] = None
        self.test_data: Optional[pd.DataFrame] = None

        self.X_resampled: Optional[pd.DataFrame] = None
        self.y_resampled: Optional[pd.Series] = None

        self.feature_store = feature_store
        logger.info("DataProcessing initialised.")

    # -------------------------------------------------------------------
    # Method: load_data
    # -------------------------------------------------------------------
    def load_data(self) -> None:
        """
        Loads training and test datasets from CSV.

        Raises
        ------
        CustomException
            If reading either CSV fails.
        """
        try:
            self.data = pd.read_csv(self.train_data_path)
            self.test_data = pd.read_csv(self.test_data_path)
            logger.info(
                f"Training data loaded from '{self.train_data_path}' (shape={self.data.shape}); "
                f"Test data loaded from '{self.test_data_path}' (shape={self.test_data.shape})."
            )
        except Exception as e:
            logger.error(f"Error while reading data: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: preprocess_data
    # -------------------------------------------------------------------
    def preprocess_data(self) -> None:
        """
        Performs feature engineering and basic imputations on the training data.

        Steps include:
        - Impute 'Age', 'Embarked', and 'Fare'.
        - Encode 'Sex' (male→0, female→1) and 'Embarked' (category codes).
        - Create engineered features: FamilySize, IsAlone, HasCabin, Title,
          and interactions Pclass_Fare, Age_Fare.

        Raises
        ------
        CustomException
            If preprocessing fails or required columns are missing.
        """
        try:
            if self.data is None:
                raise ValueError("Training data not loaded. Call `load_data()` first.")

            df = self.data

            # Basic imputations
            df["Age"] = df["Age"].fillna(df["Age"].median())
            df["Embarked"] = df["Embarked"].fillna(df["Embarked"].mode()[0])
            df["Fare"] = df["Fare"].fillna(df["Fare"].median())

            # Encoding
            df["Sex"] = df["Sex"].map({"male": 0, "female": 1})
            df["Embarked"] = df["Embarked"].astype("category").cat.codes

            # Engineered features
            df["Familysize"] = df["SibSp"] + df["Parch"] + 1
            df["Isalone"] = (df["Familysize"] == 1).astype(int)
            df["HasCabin"] = df["Cabin"].notnull().astype(int)

            # Extract Title from Name; map to ordinal buckets (unknown→'Rare')
            df["Title"] = (
                df["Name"]
                .str.extract(r" ([A-Za-z]+)\.", expand=False)
                .map({"Mr": 0, "Miss": 1, "Mrs": 2, "Master": 3, "Rare": 4})
                .fillna(4)
            )

            # Simple interactions
            df["Pclass_Fare"] = df["Pclass"] * df["Fare"]
            df["Age_Fare"] = df["Age"] * df["Fare"]

            self.data = df
            logger.info("Data preprocessing complete.")

        except Exception as e:
            logger.error(f"Error while preprocessing data: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: handle_imbalance_data
    # -------------------------------------------------------------------
    def handle_imbalance_data(self) -> None:
        """
        Applies SMOTE to the engineered training features to address class imbalance.

        Uses the following feature columns:
        ['Pclass', 'Sex', 'Age', 'Fare', 'Embarked', 'Familysize',
         'Isalone', 'HasCabin', 'Title', 'Pclass_Fare', 'Age_Fare']

        Raises
        ------
        CustomException
            If SMOTE fails or required columns are missing.
        """
        try:
            if self.data is None:
                raise ValueError("Training data not loaded/preprocessed.")

            feature_cols = [
                "Pclass",
                "Sex",
                "Age",
                "Fare",
                "Embarked",
                "Familysize",
                "Isalone",
                "HasCabin",
                "Title",
                "Pclass_Fare",
                "Age_Fare",
            ]

            X = self.data[feature_cols]
            y = self.data["Survived"]

            smote = SMOTE(random_state=42)
            X_resampled, y_resampled = smote.fit_resample(X, y)

            self.X_resampled = pd.DataFrame(X_resampled, columns=feature_cols)
            self.y_resampled = pd.Series(y_resampled, name="Survived")

            logger.info(
                "Class imbalance handled with SMOTE "
                f"(original n={len(X)}, resampled n={len(self.X_resampled)})."
            )

        except Exception as e:
            logger.error(f"Error while handling imbalanced data: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: store_feature_in_redis
    # -------------------------------------------------------------------
    def store_feature_in_redis(self) -> None:
        """
        Writes engineered training features (row-by-row) to the Redis feature store.

        The stored payload per entity includes engineered numerical values
        and the target ('Survived') for convenience.

        Raises
        ------
        CustomException
            If writing to the feature store fails.
        """
        try:
            if self.data is None:
                raise ValueError("Training data not loaded/preprocessed.")

            batch_data: Dict[str, Dict[str, Any]] = {}

            for _, row in self.data.iterrows():
                entity_id = str(row["PassengerId"])
                features: Dict[str, Any] = {
                    "Age": row["Age"],
                    "Fare": row["Fare"],
                    "Pclass": row["Pclass"],
                    "Sex": row["Sex"],
                    "Embarked": row["Embarked"],
                    "Familysize": row["Familysize"],
                    "Isalone": row["Isalone"],
                    "HasCabin": row["HasCabin"],
                    "Title": row["Title"],
                    "Pclass_Fare": row["Pclass_Fare"],
                    "Age_Fare": row["Age_Fare"],
                    "Survived": row["Survived"],
                }
                batch_data[entity_id] = features

            self.feature_store.store_batch_features(batch_data)
            logger.info(f"Pushed {len(batch_data)} entities to the Redis feature store.")

        except Exception as e:
            logger.error(f"Error while storing features in Redis: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: retrive_feature_redis_store (kept for backward-compat)
    # -------------------------------------------------------------------
    def retrive_feature_redis_store(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single entity's features from Redis. (Legacy name preserved.)

        Parameters
        ----------
        entity_id : Any
            Entity identifier (e.g., PassengerId). Will be stringified.

        Returns
        -------
        dict | None
            The feature dictionary if found; otherwise None.
        """
        return self.retrieve_feature_redis_store(entity_id)

    # -------------------------------------------------------------------
    # Method: retrieve_feature_redis_store (preferred)
    # -------------------------------------------------------------------
    def retrieve_feature_redis_store(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single entity's features from Redis. (Preferred name.)

        Parameters
        ----------
        entity_id : Any
            Entity identifier (e.g., PassengerId). Will be stringified.

        Returns
        -------
        dict | None
            The feature dictionary if found; otherwise None.
        """
        try:
            features = self.feature_store.get_features(str(entity_id))
            if features:
                logger.debug(f"Features retrieved for entity_id={entity_id}.")
                return features
            logger.debug(f"No features found for entity_id={entity_id}.")
            return None
        except Exception as e:
            logger.error(f"Error retrieving features for entity_id={entity_id}: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: run
    # -------------------------------------------------------------------
    def run(self) -> None:
        """
        Executes the complete data processing pipeline:

        Steps
        -----
        1. Load train/test CSVs.
        2. Preprocess and engineer features.
        3. Address class imbalance with SMOTE (training features).
        4. Store engineered features in the Redis feature store.

        Raises
        ------
        CustomException
            If any stage of the pipeline fails.
        """
        try:
            logger.info("🚀 Starting Data Processing pipeline...")
            self.load_data()
            self.preprocess_data()
            self.handle_imbalance_data()
            self.store_feature_in_redis()
            logger.info("✅ Data Processing pipeline completed successfully.")
        except Exception as e:
            logger.error(f"❌ Error during Data Processing pipeline: {e}")
            raise CustomException(str(e), _sys)


# -------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("🔧 Initialising Redis feature store and running pipeline...")
        store = RedisFeatureStore()
        processor = DataProcessing(TRAIN_PATH, TEST_PATH, store)
        processor.run()

        # Quick sanity check fetch (example PassengerId)
        example_id = 332
        fetched = processor.retrive_feature_redis_store(entity_id=example_id)
        logger.info(f"🔎 Retrieved features for PassengerId={example_id}: {fetched}")

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise CustomException(str(e), _sys)