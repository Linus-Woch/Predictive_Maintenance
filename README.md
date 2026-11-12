# Predictive Maintenance: Turbofan Remaining Useful Life

Estimating how many operating cycles a turbofan engine has left before failure, using its sensor history and operating settings.

This project uses NASA's simulated C-MAPSS data to explore remaining useful life (RUL) prediction. The main workflow trains an XGBoost regressor on **FD004**, which includes six operating conditions and two fault modes. Earlier notebooks record the learning process on **FD001**, from data exploration and simple baselines to classification, feature engineering, and stronger regression models.

## Start here

- **[Training notebook](TRAIN.ipynb):** data preparation, operating-condition clustering, normalization, history features, parameter search, and model export.
- **[Prediction notebook](PREDICT.ipynb):** load the saved model, predict RUL at each test engine's last observed cycle, and evaluate against the supplied labels.
- **[Prediction results](rul_comparison.csv):** actual and predicted RUL for each test engine.
- **[Learning notebooks](learning_notebooks/):** the exploratory work leading up to the main workflow.

## Current results

The saved XGBoost model produces the following results on the **248 engines in the bundled FD004 test file**, with one prediction per engine at its final observed cycle. Targets are uncapped RUL; predictions are clipped at zero.

| Metric | Value |
|---|---:|
| Mean absolute error (MAE) | 21.74 cycles |
| Root mean squared error (RMSE) | 33.05 cycles |
| Mean signed error, prediction minus actual | +12.91 cycles |
| R² | 0.632 |

These values were reproduced from the saved `models.joblib` artifact and match `rul_comparison.csv`. The positive signed error indicates average overestimation of remaining life; individual errors can be larger in either direction.

The training notebook also reports a **four-fold cross-validation RMSE of 46.34 cycles**. That score evaluates every validation cycle, whereas the test results above evaluate one endpoint per engine. They describe different evaluation populations. Preprocessing is currently fitted before cross-validation, so the CV score has the limitation described below.

## Data and prediction task

The source is the [NASA C-MAPSS Jet Engine Simulated Data dataset](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data). Training histories continue until failure; test histories stop before failure. Each value in `RUL_FD004.txt` gives the remaining cycles at the last recorded observation for the corresponding test engine.

Each raw data row has 26 whitespace-separated fields:

| Fields | Contents |
|---|---|
| 1–2 | Engine ID and operating cycle |
| 3–5 | Three operating settings |
| 6–26 | Twenty-one sensor measurements |

The bundled FD004 files contain **249 training engines / 61,249 rows** and **248 test engines / 41,214 rows**. These counts come from the files themselves; the train/test trajectory counts are reversed in the supplied dataset readme.

For a training engine, the target at a given cycle is:

```text
RUL = engine's final recorded training cycle − current cycle
```

The output is measured in operating cycles, not calendar time. Raw data and dataset documentation are included in [CMAPSSData/](CMAPSSData/).

## Method

1. **Identify operating regimes.** Standardize the three operating settings and cluster them into six regimes with KMeans.
2. **Select sensors.** Remove sensors whose mean within-regime standard deviation is at most `0.0001`. The current model retains 17 sensors.
3. **Normalize within regimes.** Fit a separate sensor scaler per regime using training observations from each engine's first 20 cycles. Treating those cycles as a healthy reference is a modeling assumption.
4. **Build history features.** For each retained sensor, calculate trailing means and standard deviations over 5, 15, and 30 observations; lag-based slopes; an exponentially weighted mean with span 20; and deviations from the smoothed and initial reference values. Calculations stay within engine boundaries and use observations available through the current cycle.
5. **Select model parameters.** Run `RandomizedSearchCV` over 40 XGBoost parameter combinations, using four-fold `GroupKFold` with engine IDs as groups and negative RMSE as the score. The selected estimator is refitted on all training rows.
6. **Save and predict.** Store the model, selected columns, and fitted preprocessing objects together. Prediction reuses those objects and the same feature function before selecting each engine's final row.

The current model uses **225 input features**: 17 sensor readings, 204 derived features, three settings, and cycle count. Engine ID and RUL are excluded from model inputs.

The saved model's selected parameters are:

```text
n_estimators=100       learning_rate=0.05
max_depth=5           min_child_weight=30
subsample=0.7         colsample_bytree=0.7
reg_lambda=10         reg_alpha=5
```

## Run locally

The saved artifact and prediction workflow were checked with **Python 3.14.7** and the package versions below. Use a matching environment when loading the serialized model; this is a recorded working environment, not a dependency lockfile.

From the repository root, create and activate a virtual environment. The activation command below is for macOS/Linux.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install numpy==2.5.4 pandas==3.1.0 scikit-learn==1.9.1 \
    xgboost==3.4.1 joblib==1.6.0 matplotlib==3.11.2 \
    jupyterlab==4.6.5 ipykernel==7.4.0 requests==2.34.2
python -m jupyterlab
```

Select the virtual environment's Python kernel in JupyterLab or your notebook editor.

### Predict with the saved model

Open `PREDICT.ipynb` from the repository root and run its cells in order. The notebook loads `models.joblib`, reads `CMAPSSData/test_FD004.txt`, and writes `rul_comparison.csv`. It then prints evaluation metrics using `CMAPSSData/RUL_FD004.txt`.

No training run is needed to use the included artifact. Running prediction overwrites the comparison CSV.

The CSV contains:

| Column | Meaning |
|---|---|
| `engine_id` | Engine identifier |
| `cycle` | Last observed operating cycle |
| `predicted_RUL` | Estimated remaining operating cycles |
| `actual_RUL` | Supplied RUL at that observation |

The loader expects the original C-MAPSS format with all 21 sensor channels. Inference needs ordered engine histories to construct the temporal features; an isolated sensor snapshot is not equivalent. The prediction notebook also reads actual labels for comparison, so it currently serves as a benchmark evaluation workflow rather than an unlabeled upload interface.

### Retrain

Open `TRAIN.ipynb` from the repository root, restart its kernel, and run all cells in order. The search performs **160 validation fits plus one final refit**, then overwrites `models.joblib`. Run `PREDICT.ipynb` afterward to regenerate results for that artifact.

The search uses all available CPUs while each XGBoost fit requests four threads. Runtime and memory use depend on the machine; adjust the parallelism settings if needed. Changing the search, features, or dependencies can change the exported model and results.

### Explore the learning notebooks

Run the numbered notebooks in [learning_notebooks/](learning_notebooks/) in order, with that directory as the kernel's working directory. Notebook 02 generates the fitting/validation CSVs used later, and notebook 06 generates the featured exports used by notebook 07. The included exports allow those later notebooks to be inspected without regenerating everything first.

These notebooks preserve intermediate experiments and informal notes. Their FD001 results, classification targets, and evaluation populations should be distinguished from the main FD004 regression results.

## Repository layout

| Path | Purpose |
|---|---|
| `TRAIN.ipynb` | Main FD004 training and parameter search |
| `PREDICT.ipynb` | FD004 prediction, CSV export, and evaluation |
| `preprocessing.py` | Raw-file loading and application of saved preprocessing |
| `features.py` | Per-engine history feature construction |
| `models.joblib` | Saved model and preprocessing bundle |
| `rul_comparison.csv` | Per-engine prediction comparison |
| `CMAPSSData/` | Original data files and source documentation |
| `learning_notebooks/` | Seven FD001 learning notebooks and their exports |
| `_misc/` | Earlier planning material |
| `AI_USAGE.md` | Repository policy for AI assistance |

## Limitations and next steps

- **Preprocessing leakage in cross-validation:** the settings scaler, KMeans model, sensor selection, and sensor scalers are fitted on all training engines before `GroupKFold` splits the regressor inputs. The folds separate engines during regressor fitting, but preprocessing has already seen the validation engines. Refitting learned preprocessing inside each fold is needed to validate the complete workflow.
- **Validation differs from inference:** search scores all validation cycles, including early-life observations with high RUL. The prediction notebook scores one endpoint per truncated test history. Validation using truncated engine histories would align model selection more closely with this task.
- **Test results have been inspected during development:** they are descriptive results for the current artifact. Further model selection should use training-engine validation rather than repeatedly optimizing against official test scores.
- **Overestimation remains material:** the current model overestimates RUL on average. Error analysis by RUL range and the frequency and size of overestimates would be useful before exploring asymmetric scoring or quantile predictions.
- **Scope is simulated engine data:** the first-20-cycle reference assumption and feature definitions have not been validated on real equipment. Predictions do not establish maintenance safety or transferability to other machines.

## References and AI assistance

Dataset: [NASA C-MAPSS Jet Engine Simulated Data](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data).

Reference: A. Saxena, K. Goebel, D. Simon, and N. Eklund, *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation*, International Conference on Prognostics and Health Management, 2008. The [paper](CMAPSSData/Damage%20Propagation%20Modeling.pdf) and [dataset readme](CMAPSSData/readme.txt) are included for context.

AI assistance was used for conceptual explanations, debugging, and code/methodology review. AI-assisted contributions include this README, attributed notebook summary tables, and the evaluation block explicitly labeled in `PREDICT.ipynb`. The maintainer is responsible for the methodology, implementation, independent verification, and conclusions. See [AI_USAGE.md](AI_USAGE.md) for the project's policy.
