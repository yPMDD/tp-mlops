# MLOps course workspace

This repository is the single project workspace for the course. Keep the fraud-detection files at the repository root: their relative paths are shared across TPs 1-4 and 6-9, and TP9 packages the existing `models/model.pkl`.

## Which folder to use

- **Fraud-detection track — TPs 1-4 and 6-9:** work from this repository root (`tp-mlops`). The shared inputs are `data/transactions.csv` and `models/model.pkl`; code, DVC stages, reports, captures, and the TP9 `fraude-api` directory live alongside them.
- **Medicines synthesis — TP5:** work from `projects/medicaments`. It is a separate dataset and modeling exercise, preserved there with its original relative paths and prior outputs. Do not use its model or data for the fraud track.
- **Handouts:** the chosen outer-folder copies are in `docs/handouts`. Different TP1-TP3 copies from the former repository root are preserved under `docs/handouts/archive/repository-copies`.

## Existing state and cautions

- The fraud repository already has Git history for TPs 1-7. TP8 files and outputs were present as local uncommitted work at consolidation time.
- TP5 files from the outer folder are a useful first attempt, not a completed TP5 submission. Its current training code uses Random Forest and three input columns, while the handout requires at least four algorithms from three families, at least seven numeric features including two engineered features, and a three-stage pipeline with a 0.75 acceptance threshold.
- The medicines workbook in `projects/medicaments` has 5,917 data rows and matches the handout's column, target-count, and missing-dosage checks. Its current size and MD5 differ from the handout's published size and MD5; verify the source file and its license/date before finalizing the TP5 report.
- The TP8 report records Orange probability 0.78 and H2O probability 0.897 for Mme Benali; the TP8 handout's checkpoints are 0.91 and 0.975. Preserve that discrepancy in the TP8 evidence until reconciled. The Python forest checkpoint is 0.8899.
- The former outer-folder MLflow database and artifact directory were moved with the medicines files. That database contains experiments from more than TP5, so keep it separate from the repository-root MLflow database; do not merge the stores.
- The DVC remote is configured at the machine-local path `C:\dvcstore`. Preserve that store and the local DVC cache. Its status check needs follow-up because the read-only audit returned `unable to open database file`.
- The project virtual environment is local and should not be moved or committed.

## Progress and evidence

See [docs/PROJECT_MAP.md](docs/PROJECT_MAP.md) for the TP-by-TP relationship, current evidence, and outstanding checks.
