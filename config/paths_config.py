"""
paths_config.py
---------------
Centralised file and directory path configuration for the
MLOps Titanic Survival Prediction project.

This module defines all key paths used throughout the pipeline —
including raw data locations and processed data directories.
By consolidating path references in one place, the pipeline remains
modular, maintainable, and free from hardcoded path errors.

Usage
-----
Example:
    from config.paths_config import RAW_DIR, TRAIN_PATH, TEST_PATH, PROCESSED_DIR

Notes
-----
- All paths are defined relative to the project root.
- Directories are created dynamically where necessary.
"""

# -------------------------------------------------------------------
# Standard Library Imports
# -------------------------------------------------------------------
import os


# -------------------------------------------------------------------
# 🚢 DATA INGESTION
# -------------------------------------------------------------------
RAW_DIR = "artifacts/raw"

# Raw input CSVs
TRAIN_PATH = os.path.join(RAW_DIR, "titanic_train.csv")
TEST_PATH = os.path.join(RAW_DIR, "titanic_test.csv")


# -------------------------------------------------------------------
# 🧮 DATA PROCESSING
# -------------------------------------------------------------------
PROCESSED_DIR = "artifacts/processed"