# 🧠 **Exploratory Analysis — MLOps Titanic Survival Prediction**

This branch represents the **data scientist’s experimental stage**, where the **Titanic dataset** (previously ingested from a PostgreSQL database) is explored, cleaned, and analysed within a **Jupyter Notebook** environment.

The goal of this stage is to **understand passenger survival patterns**, perform **EDA and preprocessing experiments**, and develop an **early classification prototype** — before the workflow is modularised and automated by an ML engineer in the next stage.



## 🧾 **What This Stage Includes**

* ✅ Jupyter Notebook (`notebook/titanic.ipynb`) for interactive data exploration and experimentation
* ✅ Data ingestion from raw sources:

  * `titanic_train.csv` — passenger data extracted from PostgreSQL
* ✅ Initial data inspection (missing values, category distributions, duplicates)
* ✅ Preprocessing and encoding for categorical variables (`Sex`, `Embarked`)
* ✅ Feature engineering:

  * Family-based variables — `Familysize`, `Isalone`
  * Cabin indicator — `HasCabin`
  * Title extraction — `Mr`, `Mrs`, `Miss`, `Master`, `Rare`
  * Interaction features — `Pclass_Fare`, `Age_Fare`
* ✅ Handling of **class imbalance** via **SMOTE** oversampling
* ✅ Baseline **Random Forest Classifier** with **RandomizedSearchCV** for hyperparameter tuning
* ✅ Evaluation of model accuracy, feature importances, and class balance metrics

This notebook acts as a **sandbox for the data scientist** — a controlled environment to experiment freely before converting the logic into modular, production-ready scripts and pipeline stages.



## 🗂️ **Updated Project Structure**

```
mlops-titanic-survival-prediction/
├── artifacts/
│   ├── raw/                        # From previous Data Ingestion stage
│   │   └── titanic_train.csv
│   └── processed/                  # Processed datasets, feature matrices, etc.
├── notebook/
│   └── titanic.ipynb               # 🔍 Data scientist EDA & experimentation
├── config/
├── src/
├── requirements.txt
├── setup.py
└── README.md                       # 📖 You are here
```

> 💡 The notebook uses data stored in `artifacts/raw/`, generated during the **Data Ingestion** stage.
> This dataset forms the foundation for feature engineering and model development in subsequent pipeline stages.



## 🧩 **Notebook Highlights**

Within `notebook/titanic.ipynb`, you’ll find clearly structured sections covering:

1. **Setup & Imports** — loads dependencies, configures the working directory, and defines data paths.
2. **Data Loading & Quick Checks** — imports the Titanic dataset, previews it, and identifies missing values.
3. **Preprocessing & Encoding** — imputes missing data, encodes categorical variables, and standardises fields.
4. **Feature Engineering** — constructs derived features such as `Familysize`, `Isalone`, `HasCabin`, and `Title`.
5. **SMOTE Resampling** — balances survival classes to improve model generalisation.
6. **Train/Test Split** — separates data for unbiased model validation.
7. **Random Forest Modelling** — fits a classifier using Randomized Search for hyperparameter optimisation.
8. **Model Evaluation** — reports accuracy, classification metrics, and top feature importances.



## 🚀 **Next Stage — Data Processing**

In the next branch, this exploratory workflow evolves into the **Data Processing** stage — where the notebook logic is modularised into a reproducible preprocessing pipeline:

* Creation of `src/data_processing.py` for automated feature engineering, encoding, and cleaning.
* Update of `config/paths_config.py` to include processed data directories and file outputs.
* Structured artefacts saved under `artifacts/processed/` for downstream training and evaluation.
* Integration of robust logging and exception handling for traceability across environments.

This transition marks the evolution from **data science experimentation → engineered preprocessing pipeline**, bridging the gap between **research and reproducible MLOps automation**.
