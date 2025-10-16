"""
model_training.py
-----------------
Implements the ModelTraining class responsible for loading engineered features
from the Redis Feature Store, splitting into train/test sets, performing
hyperparameter tuning with Randomised Search on a RandomForestClassifier,
evaluating accuracy, and persisting the trained model to disk.

This module integrates with:
- Centralised logging (`src.logger`)
- Custom exception handling (`src.custom_exception`)
- Feature store abstraction (`src.feature_store.RedisFeatureStore`)

Usage
-----
Example:
    python src/model_training.py

Notes
-----
- Assumes features have already been written to Redis under keys of the form
  `entity:<PassengerId>:features`, including the target field 'Survived'.
- Trained model is saved under `artifacts/models/random_forest_model.pkl`.
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Temporary Import Path Hack (Option D)
# -------------------------------------------------------------------
# Ensure the project root (parent of this file's directory) is on sys.path
# so that `import src.*` and `import config.*` work when running this file
# as a script: `python src/model_training.py`.
#
# ⚠️ Note:
# - This is a pragmatic, script-friendly workaround.
# - Prefer installing the package in editable mode (`pip install -e .`)
#   or running as a module (`python -m src.model_training`) in the long run.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))

# -------------------------------------------------------------------
# Standard & Third-Party Imports
# -------------------------------------------------------------------
import os
import pickle
from typing import Iterable, List, Dict, Any, Tuple

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split, RandomizedSearchCV

# -------------------------------------------------------------------
# Internal Imports
# -------------------------------------------------------------------
from src.logger import get_logger
from src.custom_exception import CustomException
from src.feature_store import RedisFeatureStore

# -------------------------------------------------------------------
# Logger Setup
# -------------------------------------------------------------------
logger = get_logger(__name__)


# -------------------------------------------------------------------
# Class: ModelTraining
# -------------------------------------------------------------------
class ModelTraining:
    """
    Trains a RandomForest model on features sourced from the Redis Feature Store.

    Parameters
    ----------
    feature_store : RedisFeatureStore
        Feature store instance used to fetch engineered features.
    model_save_path : str, default="artifacts/models/"
        Directory in which the trained model artefact will be stored.

    Attributes
    ----------
    model : RandomForestClassifier | None
        Trained model instance once fitted.
    """

    def __init__(self, feature_store: RedisFeatureStore, model_save_path: str = "artifacts/models/") -> None:
        self.feature_store = feature_store
        self.model_save_path = model_save_path
        self.model: RandomForestClassifier | None = None

        # Create artefact directory if it doesn't exist
        os.makedirs(self.model_save_path, exist_ok=True)
        logger.info("ModelTraining initialised.")

    # -------------------------------------------------------------------
    # Method: load_data_from_redis
    # -------------------------------------------------------------------
    def load_data_from_redis(self, entity_ids: Iterable[str]) -> List[Dict[str, Any]]:
        """
        Loads per-entity feature dictionaries from Redis.

        Parameters
        ----------
        entity_ids : Iterable[str]
            Iterable of entity identifiers (PassengerId as strings).

        Returns
        -------
        list of dict
            A list of feature dictionaries (each expected to contain 'Survived').

        Raises
        ------
        CustomException
            If retrieval fails.
        """
        try:
            logger.info("Extracting data from Redis...")
            data: List[Dict[str, Any]] = []

            for entity_id in entity_ids:
                features = self.feature_store.get_features(entity_id)
                if features:
                    data.append(features)
                else:
                    logger.warning(f"Features not found for entity_id={entity_id}")

            logger.info(f"Fetched {len(data)} feature rows from Redis.")
            return data

        except Exception as e:
            logger.error(f"Error while loading data from Redis: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: prepare_data
    # -------------------------------------------------------------------
    def prepare_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Splits entity IDs into train/test, fetches features from Redis,
        and constructs X/y matrices.

        Returns
        -------
        X_train : pd.DataFrame
        X_test  : pd.DataFrame
        y_train : pd.Series
        y_test  : pd.Series

        Raises
        ------
        CustomException
            If data preparation fails.
        """
        try:
            entity_ids = self.feature_store.get_all_entity_ids()
            if not entity_ids:
                raise ValueError("No entity IDs found in the Feature Store. Populate it before training.")

            train_entity_ids, test_entity_ids = train_test_split(entity_ids, test_size=0.2, random_state=42)

            train_data = self.load_data_from_redis(train_entity_ids)
            test_data = self.load_data_from_redis(test_entity_ids)

            train_df = pd.DataFrame(train_data)
            test_df = pd.DataFrame(test_data)

            # Separate features/target
            X_train = train_df.drop(columns=["Survived"])
            X_test = test_df.drop(columns=["Survived"])
            y_train = train_df["Survived"]
            y_test = test_df["Survived"]

            logger.info(f"Prepared training data with {X_train.shape[0]} rows and {X_train.shape[1]} features.")
            logger.debug(f"Feature columns: {list(X_train.columns)}")
            return X_train, X_test, y_train, y_test

        except Exception as e:
            logger.error(f"Error while preparing data: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: hyperparameter_tuning
    # -------------------------------------------------------------------
    def hyperparameter_tuning(self, X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
        """
        Runs Randomised Search over a small hyperparameter grid for RandomForest.

        Parameters
        ----------
        X_train : pd.DataFrame
            Training features.
        y_train : pd.Series
            Training target.

        Returns
        -------
        RandomForestClassifier
            Best estimator found by RandomizedSearchCV.

        Raises
        ------
        CustomException
            If tuning fails.
        """
        try:
            param_distributions = {
                "n_estimators": [100, 200, 300],
                "max_depth": [10, 20, 30],
                "min_samples_split": [2, 5],
                "min_samples_leaf": [1, 2],
            }

            rf = RandomForestClassifier(random_state=42)
            random_search = RandomizedSearchCV(
                rf,
                param_distributions=param_distributions,
                n_iter=10,
                cv=3,
                scoring="accuracy",
                random_state=42,
                n_jobs=-1,
            )
            random_search.fit(X_train, y_train)

            best_params = random_search.best_params_
            logger.info(f"Best parameters: {best_params}")

            best_model: RandomForestClassifier = random_search.best_estimator_
            return best_model

        except Exception as e:
            logger.error(f"Error during hyperparameter tuning: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: train_and_evaluate
    # -------------------------------------------------------------------
    def train_and_evaluate(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> float:
        """
        Tunes, fits, evaluates, and saves the RandomForest model.

        Returns
        -------
        float
            Accuracy on the held-out test set.

        Raises
        ------
        CustomException
            If training or evaluation fails.
        """
        try:
            best_rf = self.hyperparameter_tuning(X_train, y_train)

            # Fit on full training set (RandomizedSearchCV already fitted internally,
            # but we keep this explicit step for clarity/consistency).
            best_rf.fit(X_train, y_train)

            y_pred = best_rf.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            logger.info(f"✅ Test Accuracy: {accuracy:.4f}")

            # Persist model
            self.model = best_rf
            self.save_model(best_rf)

            return accuracy

        except Exception as e:
            logger.error(f"Error during model training/evaluation: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: save_model
    # -------------------------------------------------------------------
    def save_model(self, model: RandomForestClassifier) -> None:
        """
        Serialises and saves the trained model to disk.

        Parameters
        ----------
        model : RandomForestClassifier
            Fitted model to be persisted.

        Raises
        ------
        CustomException
            If saving fails.
        """
        try:
            model_filename = os.path.join(self.model_save_path, "random_forest_model.pkl")
            with open(model_filename, "wb") as f:
                pickle.dump(model, f)
            logger.info(f"📦 Model saved at: {model_filename}")

        except Exception as e:
            logger.error(f"Error while saving model: {e}")
            raise CustomException(str(e), _sys)

    # -------------------------------------------------------------------
    # Method: run
    # -------------------------------------------------------------------
    def run(self) -> None:
        """
        Executes the complete model training pipeline:

        Steps
        -----
        1. Prepare data (split IDs, fetch features, build X/y).
        2. Hyperparameter tuning for RandomForest.
        3. Fit best model and evaluate on test set.
        4. Save trained model artefact.

        Raises
        ------
        CustomException
            If any stage of the pipeline fails.
        """
        try:
            logger.info("🚀 Starting Model Training pipeline...")
            X_train, X_test, y_train, y_test = self.prepare_data()
            _ = self.train_and_evaluate(X_train, y_train, X_test, y_test)
            logger.info("🏁 End of Model Training pipeline.")

        except Exception as e:
            logger.error(f"❌ Pipeline failure: {e}")
            raise CustomException(str(e), _sys)


# -------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("🔧 Initialising Feature Store and running Model Training...")
        store = RedisFeatureStore()
        trainer = ModelTraining(store)
        trainer.run()
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise CustomException(str(e), _sys)