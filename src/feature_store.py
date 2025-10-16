"""
feature_store.py
----------------
Implements the RedisFeatureStore class responsible for storing and retrieving
feature data in a Redis key-value store.

This module serves as a lightweight feature store for the Titanic Survival
Prediction project, enabling quick read/write access to preprocessed features
for model training and inference.

It provides both single-entity and batch operations and integrates seamlessly
with other MLOps pipeline components.

This module integrates with:
- Centralised logging (`src.logger`)
- Custom exception handling (`src.custom_exception`)

Usage
-----
Example:
    python src/feature_store.py

Notes
-----
- Requires a running Redis instance (local or remote).
- Default connection settings point to localhost on port 6379.
- Stored keys follow the naming pattern: `entity:<entity_id>:features`.
"""

from __future__ import annotations

# -------------------------------------------------------------------
# Temporary Import Path Hack (Option D)
# -------------------------------------------------------------------
# Ensures that the project root is included in sys.path so that
# imports like `from src.logger` and `from src.custom_exception`
# work when this file is executed directly as a script.
#
# ⚠️ Note:
# - This is a pragmatic, script-friendly workaround.
# - Prefer installing the package in editable mode (`pip install -e .`)
#   or running the module via `python -m src.feature_store`.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..")))

# -------------------------------------------------------------------
# Standard & Third-Party Imports
# -------------------------------------------------------------------
import redis
import json
from typing import Any, Dict, List, Optional

# -------------------------------------------------------------------
# Internal Imports
# -------------------------------------------------------------------
from src.logger import get_logger
from src.custom_exception import CustomException

# -------------------------------------------------------------------
# Logger Setup
# -------------------------------------------------------------------
logger = get_logger(__name__)


# -------------------------------------------------------------------
# Class: RedisFeatureStore
# -------------------------------------------------------------------
class RedisFeatureStore:
    """
    Handles the storage and retrieval of feature data within Redis.

    This class provides both row-level and batch-level methods for
    persisting entity feature sets, allowing efficient reuse during
    model training and inference workflows.

    Parameters
    ----------
    host : str, default="localhost"
        Redis server host.
    port : int, default=6379
        Redis server port.
    db : int, default=0
        Redis database index.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        try:
            self.client = redis.StrictRedis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
            )
            logger.info(f"RedisFeatureStore initialised: host={host}, port={port}, db={db}")

        except Exception as e:
            logger.error(f"Error while connecting to Redis: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: store_features
    # -------------------------------------------------------------------
    def store_features(self, entity_id: str, features: Dict[str, Any]) -> None:
        """
        Stores feature data for a single entity in Redis.

        Parameters
        ----------
        entity_id : str
            Unique identifier for the entity (e.g., passenger ID).
        features : dict
            Dictionary of feature names and their corresponding values.

        Raises
        ------
        CustomException
            If Redis operation fails.
        """
        try:
            key = f"entity:{entity_id}:features"
            self.client.set(key, json.dumps(features))
            logger.debug(f"Stored features for entity {entity_id} with key: {key}")

        except Exception as e:
            logger.error(f"Failed to store features for entity {entity_id}: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: get_features
    # -------------------------------------------------------------------
    def get_features(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves feature data for a single entity.

        Parameters
        ----------
        entity_id : str
            Unique identifier for the entity (e.g., passenger ID).

        Returns
        -------
        dict or None
            Dictionary of feature values if found, otherwise None.

        Raises
        ------
        CustomException
            If Redis retrieval fails.
        """
        try:
            key = f"entity:{entity_id}:features"
            features = self.client.get(key)

            if features:
                logger.debug(f"Retrieved features for entity {entity_id}")
                return json.loads(features)

            logger.debug(f"No features found for entity {entity_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving features for entity {entity_id}: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: store_batch_features
    # -------------------------------------------------------------------
    def store_batch_features(self, batch_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Stores multiple entities’ features in a batch operation.

        Parameters
        ----------
        batch_data : dict
            Mapping of entity_id → feature dictionary.

        Raises
        ------
        CustomException
            If any Redis operation fails.
        """
        try:
            for entity_id, features in batch_data.items():
                self.store_features(entity_id, features)
            logger.info(f"Batch stored {len(batch_data)} entities into Redis.")

        except Exception as e:
            logger.error(f"Batch storage failed: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: get_batch_features
    # -------------------------------------------------------------------
    def get_batch_features(self, entity_ids: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieves multiple entities’ features in a batch operation.

        Parameters
        ----------
        entity_ids : list of str
            List of entity IDs to retrieve.

        Returns
        -------
        dict
            Mapping of entity_id → feature dictionary (or None if not found).

        Raises
        ------
        CustomException
            If any Redis retrieval operation fails.
        """
        try:
            batch_features = {
                entity_id: self.get_features(entity_id) for entity_id in entity_ids
            }
            logger.info(f"Retrieved batch features for {len(entity_ids)} entities.")
            return batch_features

        except Exception as e:
            logger.error(f"Batch retrieval failed: {e}")
            raise CustomException(str(e), sys)

    # -------------------------------------------------------------------
    # Method: get_all_entity_ids
    # -------------------------------------------------------------------
    def get_all_entity_ids(self) -> List[str]:
        """
        Retrieves all entity IDs currently stored in Redis.

        Returns
        -------
        list of str
            List of entity IDs.

        Raises
        ------
        CustomException
            If Redis key retrieval fails.
        """
        try:
            keys = self.client.keys("entity:*:features")
            entity_ids = [key.split(":")[1] for key in keys]
            logger.info(f"Found {len(entity_ids)} entities in Redis.")
            return entity_ids

        except Exception as e:
            logger.error(f"Failed to fetch entity IDs from Redis: {e}")
            raise CustomException(str(e), sys)


# -------------------------------------------------------------------
# Script Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("🚀 Initialising Redis Feature Store...")
        store = RedisFeatureStore()

        # Example: storing and retrieving sample data
        sample_features = {"age": 29, "sex": "male", "fare": 72.5}
        store.store_features("1001", sample_features)
        retrieved = store.get_features("1001")

        logger.info(f"✅ Retrieved sample features: {retrieved}")

    except Exception as e:
        logger.error(f"❌ Error running feature store script: {e}")
        raise CustomException(str(e), sys)
