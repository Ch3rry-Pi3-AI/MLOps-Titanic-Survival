# 📓 **Exploratory Data Analysis & Experimentation — `titanic.ipynb`**

This notebook documents the **exploratory data analysis (EDA)**, **feature engineering**, and **model experimentation** stages of the **MLOps Titanic Survival Prediction** project.
It provides an interactive environment for exploring the Titanic dataset, preprocessing passenger data, balancing classes, and developing a baseline classification model prior to full pipeline integration.



## 📁 **File Location**

```
mlops-titanic-survival-prediction/
├── notebook/
│   └── titanic.ipynb
├── src/
├── pipeline/
├── config/
└── artifacts/
```



## 🎯 **Purpose**

The notebook serves as a **research and prototyping workspace** designed to:

1. Explore the raw Titanic dataset extracted from PostgreSQL and stored under `artifacts/raw/`.
2. Perform data cleaning and preprocessing steps to handle missing values and categorical variables.
3. Engineer new features to enhance model performance (e.g. family size, cabin indicator, title extraction).
4. Address class imbalance using **SMOTE** to oversample minority classes.
5. Train and evaluate a **Random Forest Classifier** with hyperparameter tuning using **RandomizedSearchCV**.
6. Generate baseline performance metrics to guide downstream pipeline implementation.



## 🧩 **Structure Overview**

| Section                                    | Description                                                                                                      |
| :----------------------------------------- | :--------------------------------------------------------------------------------------------------------------- |
| **1. Setup**                               | Imports dependencies, configures notebook environment, and sets up directory paths.                              |
| **2. Data Loading & Quick Checks**         | Loads the Titanic dataset from `artifacts/raw/` and inspects missing values and category distributions.          |
| **3. Preprocessing & Feature Engineering** | Fills missing values, encodes categorical variables, and derives additional interaction features.                |
| **4. Class Balancing**                     | Applies **SMOTE** (Synthetic Minority Oversampling Technique) to address class imbalance in the target variable. |
| **5. Train/Test Split**                    | Splits the balanced dataset into training and testing subsets for model evaluation.                              |
| **6. Model Training**                      | Defines a **Random Forest Classifier** and performs hyperparameter tuning using Randomized Search.               |
| **7. Evaluation & Insights**               | Evaluates model performance using accuracy, classification report, confusion matrix, and feature importances.    |



## ⚙️ **Requirements**

Before running the notebook, ensure that the virtual environment is active and dependencies are installed:

```bash
uv venv
uv pip install -r requirements.txt
```

Then launch Jupyter:

```bash
jupyter notebook notebook/titanic.ipynb
```



## 🧠 **Typical Workflow**

1. Load the Titanic dataset from `artifacts/raw/titanic_train.csv`.
2. Inspect the data structure, missing values, and key categorical variables.
3. Impute missing values for **Age**, **Fare**, and **Embarked**, and encode **Sex** and **Embarked** numerically.
4. Engineer additional features such as **Family Size**, **IsAlone**, **HasCabin**, and **Title**.
5. Apply **SMOTE** to balance survival classes and mitigate model bias.
6. Split the resampled data into training and test sets.
7. Train a **Random Forest Classifier** using Randomized Search for hyperparameter optimisation.
8. Evaluate model accuracy, inspect feature importances, and document initial findings.



## 🧾 **Outputs**

| Output                  | Description                                                                 |
| :---------------------- | :-------------------------------------------------------------------------- |
| **Processed Dataset**   | Cleaned and feature-engineered Titanic data (in-memory only).               |
| **Resampled Data**      | SMOTE-balanced training and testing data splits.                            |
| **Trained Model**       | Best Random Forest model with optimised hyperparameters (in-memory).        |
| **Performance Metrics** | Accuracy score, classification report, and confusion matrix visualisation.  |
| **Feature Importances** | Ranked table showing the most influential variables in survival prediction. |



## 🧩 **Integration with MLOps Pipeline**

This notebook functions as the **experimental foundation** for production pipeline components:

* Data ingestion logic aligns with `src/data_ingestion.py`, which extracts the same Titanic dataset from PostgreSQL.
* Preprocessing and feature engineering workflows will be implemented in modular form under `src/processing/`.
* Class balancing and model training methods will integrate into the `pipeline/training_pipeline.py`.
* Evaluation metrics and feature importances inform model monitoring and retraining thresholds in future stages.

Together, these ensure a seamless transition from **notebook experimentation** to **automated, reproducible MLOps workflows**.



## ✅ **Best Practices**

* Use Markdown headings and emojis to clearly separate notebook sections (e.g. `## 🧹 Preprocessing`, `## 🧠 Modelling`).
* Always save trained model artefacts and processed data under the `artifacts/` directory.
* Keep all configuration constants (e.g. file paths, random seeds) defined in `config/paths_config.py`.
* Avoid hard-coded local paths; instead, use relative references or configuration imports.
* Document parameter tuning choices and observations in Markdown cells for reproducibility.
* Treat this notebook as a **sandbox** — final logic belongs in the pipeline modules under `src/`.
