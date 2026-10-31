# Notebook roadmap — NASA C-MAPSS FD001

This roadmap describes the intended notebook structure and learning sequence. Create notebooks as you reach each step; future entries are plans, not completed work. The maintainer implements and verifies the code.

[AGENTS.md](AGENTS.md) remains the project roadmap, and [AI_USAGE.md](AI_USAGE.md) governs AI assistance. This organizational document was drafted by Codex at the maintainer's explicit request. It does not change either policy.

## Where we are now

- `01_understanding_the_data.ipynb` exists and contains the initial exploration.
- `02_rul_targets.ipynb` exists and currently contains training/test label preparation, the engine split, and the first constant RUL baseline.
- The next organizational step is to move the existing baseline section into `03_rul_baseline.ipynb`.
- After that, continue with `04_classification_models.ipynb`.

These statements describe the saved notebook contents, not a claim that every methodological or documentation check is complete.

## Overview

All notebooks live in `notebooks/`. Notebook numbers indicate working order; they are not phase numbers.

| Notebook | Project phase | Main question |
|---|---|---|
| `01_understanding_the_data.ipynb` | 1 | What does FD001 contain, and how do engines and sensors behave? |
| `02_rul_targets.ipynb` | 1 | What are the correct RUL labels, and how do we split engines for development? |
| `03_rul_baseline.ipynb` | 2 | How well does a constant RUL prediction perform? |
| `04_classification_models.ipynb` | 2 | How do we define an alert, and can simple classifiers improve on a dummy baseline? |
| `05_simple_rul_regression.ipynb` | 3 | Can simple regressors estimate remaining cycles better than the constant baseline? |
| `06_past_only_features.ipynb` | 4 | How can we summarize sensor history without looking into the future? |
| `07_stronger_rul_models.ipynb` | 4 | Do Random Forest and gradient boosting improve validation performance? |
| `08_rul_final_evaluation.ipynb` | 5 | How does the selected regressor generalize, and where does it fail? |
| `09_classification_final_evaluation.ipynb` | 5 | How does the selected classifier balance missed alerts and false alarms? |
| `10_sequence_model_extension.ipynb` — optional | 6 | Does a sequence model offer a meaningful improvement over the established models? |

## 01 — Understand the data

**Inputs:** original training FD001 file and downloaded dataset documentation.

**Contents:**

- Explain engine IDs, cycles, operating settings, sensors, and the simulated nature of the data.
- Inspect shape, data types, missingness, distinct engines, and cycle histories, including ordering, duplicates, and gaps.
- Summarize engine lifetimes and their distribution.
- Plot selected sensor trajectories across engines and record observations.
- Identify constant sensors and inspect operating settings.

**Outcome:** an understandable data overview and documented checks. Exploration suggests hypotheses; it does not prove predictive usefulness. Later decisions to remove features must use only the fitting partition.

## 02 — RUL targets and split

**Inputs:** original training/test FD001 files and official `RUL_FD001.txt`.

**Contents:**

- Construct training RUL from each engine's final cycle and check examples manually.
- Explain that official test labels refer to each engine's final recorded test cycle; document their engine mapping.
- Document earlier test-cycle labels as derived values if retaining the existing per-cycle test RUL calculation.
- Check labels for missing values, impossible values, and correct boundary cases.
- Define uncapped RUL in cycles, unless a later explicitly documented experiment introduces a cap.

- Split unique training engine IDs into fitting and validation groups: currently 80/20 with seed `8`.
- Check engine disjointness and full row coverage; save the fitting and validation engine IDs for later notebooks.

**Existing local exports:** `outputs/RUL_TRAIN_FD001.csv` and `outputs/RUL_TEST_FD001.csv`.

**Outcome:** validated labels, prepared data, and a saved engine split. Modeling experiments belong in the following notebooks.

## 03 — Constant RUL baseline

**Inputs:** prepared training data with RUL and the saved fitting/validation engine IDs from notebook 02.

**Contents:**

- Load the prepared training data and reconstruct the fitting and validation DataFrames from the saved IDs.
- Define the initial evaluation protocol: uncapped RUL in cycles, one prediction per validation row, evaluated across all validation cycles.
- Calculate the median RUL using only fitting rows and predict that value for every validation row.
- Calculate individual errors, MAE, and RMSE; verify a few examples manually.
- Explain the metrics, their units, and what a sensor-independent baseline establishes.
- Record the prediction constant, results, engine split, and evaluation protocol for later comparisons.

**Outcome:** a standalone, reproducible regression benchmark that later regressors must be compared against under the same protocol.

## 04 — Classification baseline and simple models

**Inputs:** prepared training data with RUL and the saved fitting/validation engine IDs from notebook 02.

**Contents:**

- Define the alert target: `1` when actual RUL is at or below a chosen cycle threshold; otherwise `0`.
- Start with 30 cycles and also examine 50 cycles. These are project choices, not NASA maintenance requirements.
- Check label examples, class counts, and class percentages separately for fitting and validation.
- Explain a majority-class predictor and fit a `DummyClassifier` using fitting labels before training more capable classifiers.
- Evaluate the dummy baseline with a confusion matrix, precision, recall, F1, and class support. Discuss why accuracy alone can mislead.
- Define which prediction-time inputs the model can use; exclude RUL and every alert-label column from features.
- Understand at least one algorithm conceptually before applying its library implementation.
- Start with logistic regression; optionally compare k-nearest neighbors.
- Compare a decision-tree classifier with the dummy and simple classifiers.
- Fit scaling and other learned preprocessing only on fitting rows, preferably through a pipeline.
- Compare validation confusion matrices, precision, recall, F1, and, where appropriate, precision-recall curves or PR-AUC with its convention specified.
- Distinguish the cycle threshold defining the target from a probability threshold used to turn model probabilities into alerts.
- Explain false positives, false negatives, and the trade-offs of changing the cycle threshold. Never choose the cycle threshold using official test labels.

**Outcome:** classification baselines for the label definitions, a documented comparison with simple classifiers, and a candidate selected using validation results. Keep regression metrics in the regression notebooks.

## 05 — Simple RUL regression

**Inputs:** training data with RUL and the saved split from notebook 02, plus the regression baseline and evaluation protocol from notebook 03.

**Contents:**

- Define the feature set, prediction unit, and validation rows before comparing models.
- Train linear regression or Ridge, a kNN regressor, and a decision-tree regressor.
- Fit preprocessing only on the fitting partition.
- Compare MAE/RMSE with the constant baseline under the same evaluation protocol.
- Discuss underfitting, overfitting, and how errors differ across engines and RUL ranges.

**Outcome:** the first regression models that use inputs to predict different RUL values for different observations.

## 06 — Past-only features

**Inputs:** training histories and the existing engine split.

**Contents:**

- Explore lags, trailing rolling means/standard deviations, slopes, and selected sensor combinations.
- Explain what information each feature uses and when it becomes available.
- Check that windows stay within engine boundaries and use no future readings.
- Define how to handle initial cycles with insufficient history.
- Check a small example manually and document the feature definitions.

**Outcome:** an author-implemented, reproducible way to build history features. Keep targets separate from feature construction. Regression comparisons using these features belong in notebook 07.

## 07 — Stronger RUL models

**Inputs:** fitting/validation histories, features from notebook 06, and earlier regression benchmarks.

**Contents:**

- Train Random Forest, followed by a gradient-boosting regressor.
- Compare raw-input and engineered-feature approaches on consistent validation rows.
- Conduct a limited, reproducible hyperparameter search using fitting/validation engines only.
- Record useful failures as well as successes and discuss feature-importance limitations.
- Select the final regression configuration and freeze features, preprocessing, and evaluation choices before official testing.

**Outcome:** a selected regressor with documented validation evidence. Stronger classification models are an optional later extension, not a requirement for this notebook.

## 08 — Final RUL evaluation

**Inputs:** the frozen regression configuration, validation results, and official test histories/labels.

**Contents:**

- State the final fitting procedure, including whether the chosen configuration is refitted on all official training engines.
- Evaluate the frozen model and relevant baselines on the same final recorded test cycles.
- Report MAE/RMSE, errors by RUL range and engine, and examples of severe under/overestimation.
- Optionally report the NASA asymmetric score after verifying and documenting its exact definition.
- Discuss uncertainty, maintenance consequences, and limitations of simulated benchmark evidence.

**Outcome:** final regression results and figures for the README. Do not use official test results to retune the model.

## 09 — Final classification evaluation

**Inputs:** the frozen classifier, alert and probability thresholds, and official final-cycle test labels.

**Contents:**

- Derive final-cycle test alert labels using the cycle thresholds established during development.
- Evaluate the selected classifier and dummy baseline with the same examples and label definitions.
- Report confusion matrices, precision, recall, F1, support, and appropriate probability-based metrics.
- Discuss missed imminent failures, false alarms, and the limits of the chosen alert rule.
- Optionally compare direct classification with thresholding the selected regressor's predictions; fix this comparison before examining test results.

**Outcome:** final classification results and interpretation, kept separate from the regression metrics.

## 10 — Optional sequence model

Start only after the tabular baselines and their evaluation are stable.

Use this notebook for an LSTM or another sequence regressor: window construction, causal inputs, engine-separated evaluation, and comparison with the established regression baselines. Develop using fitting/validation engines. If official test results have already influenced this extension, disclose that exposure rather than presenting another test evaluation as untouched.

## Small migration from the current notebooks

This is organizational work for the maintainer to carry out; editing this roadmap does not move notebook code.

1. Keep `01_understanding_the_data.ipynb` in place.
2. Keep training/test RUL preparation, manual label checks, split construction, and split checks in `02_rul_targets.ipynb`.
3. Save the fitting and validation engine IDs from notebook 02 so every modeling notebook can reuse identical membership.
4. Move the median-prediction section, error calculation, MAE/RMSE, and interpretation from notebook 02 into `03_rul_baseline.ipynb`. Add its own explicit data/split loading so it runs independently.
5. Run notebooks 02 and 03 from fresh kernels and verify that the baseline results are preserved.
6. Create `04_classification_models.ipynb` when beginning the classification task. Its dummy baseline and simple classifiers share one notebook, with the baseline completed first.

## Rules that keep the notebooks connected

- **Independent execution:** each notebook runs from a fresh kernel using explicit inputs. No dependency on another notebook's in-memory variables.
- **Shared split:** notebook 02 saves the engine IDs; all modeling notebooks reload them. During migration, reproducing the split requires the same ordered IDs, proportion, and seed `8`, followed by a membership check.
- **Explicit dependencies:** notebook 02 provides data and the split to modeling notebooks; 03 establishes the regression benchmark for 05 and 07; 04 contains the classification baseline and simple models; 06 supplies features to 07; 08 and 09 report final regression and classification results, respectively.
- **Targets stay out of inputs:** RUL, alerts, final lifetime, and values derived from future information cannot be model features. Prediction columns used for reporting must not accidentally become features either.
- **Evaluation unit:** the current baseline evaluates all validation cycles. Official final testing evaluates one final recorded cycle per test engine. Label these results separately; their scores are not directly comparable. If a test-like truncated validation protocol is introduced, define it before model selection and reevaluate all compared baselines/models under it. Using only training engines' failure rows would make all regression targets zero.
- **Preprocessing and feature selection:** make learned decisions using the fitting partition only. Initial whole-training-set plots remain exploratory; they do not authorize selecting features from validation data.
- **Common notebook layout:** purpose and inputs; assumptions and protocol; author's implementation; checks; results; interpretation and next step.
- **Reproducibility:** record seeds, versions, thresholds, units, row/engine counts, and meaningful unsuccessful experiments. Later, move repeated logic into author-written `src/` code when that is a useful learning step.
- **Local outputs:** keep raw data and derived data exports local by default; verify redistribution permission before publishing dataset material.

## Work outside notebooks

Phase 0 setup and acquisition instructions belong in the README and dependency files. The final README should explain the problem, simulated data, reproduction steps, protocols, result tables, figures, and limitations, with truthful AI disclosure. Phase 6 delivery can be an author-written inference CLI, API, or app in `src/`, supported by author-owned checks in `tests/`; it does not require another notebook. FD002–FD004 remain optional until FD001 is reproducible.
