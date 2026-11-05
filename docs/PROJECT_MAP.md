# TP map and current evidence

## How the TPs connect

| TP | Track | How it relates to the project |
|---|---|---|
| 1 | Fraud | Creates the shared 5,000-row synthetic transactions dataset; introduces MLflow experiments and model aliases. |
| 2 | Fraud | Splits, trains, evaluates, and validates the same model through a parameterized pipeline. |
| 3 | Fraud | Packages the reference forest, registers versions, and demonstrates aliases and serving. `models/model.pkl` is the reference used by later fraud TPs. |
| 4 | Fraud | Adds DVC data history, a cached three-stage pipeline, and experiment comparisons. |
| 5 | Medicines | A separate synthesis project using the CNOPS medicines workbook. It reuses MLOps concepts, not the fraud dataset or fraud model. |
| 6 | Fraud | Compares H2O AutoML and FLAML on the fraud data and registers/serves both models. |
| 7 | Fraud | Orchestrates the DVC pipeline with Prefect and connects triggers/monitoring with Node-RED. |
| 8 | Fraud | Explains and audits the TP3 forest, then compares Orange and H2O explanations and adds a Prefect guard. |
| 9 | Fraud | Packages the existing TP3 forest in FastAPI/Docker and deploys it to a local kind Kubernetes cluster. |

## Status from the workspace audit

- **TP1-4:** project code, data pointer, DVC pipeline, reports, and Git history are in this repository. The historical commits remain available.
- **TP5:** all outer-folder files were moved to `projects/medicaments` without rewriting their code. Existing reports and MLflow records are preserved, but the implementation does not meet the handout's required algorithms, feature count/engineering, or pipeline/validation criteria.
- **TP6-7:** scripts, captures, and synthesis reports are preserved in `src/`, `captures/`, and `reports/`.
- **TP8:** scripts, workflow, plots, model card, and synthesis are preserved. Orange and H2O probabilities recorded in the synthesis do not match the handout's checkpoints and remain to be reconciled.
- **TP9:** completed. The API uses the committed TP3 model copied into `fraude-api/models/model.pkl` (8,148,153 bytes), which returns the handout's 0.8899. Docker and kind/Kubernetes runs, cache timings, scale/auto-repair, v2.0 rollout, v2.1 failure/rollback, captures, and report are preserved. Commit: `ab83669`. The source is restored to VERSION 1.0; Docker image `fraude-api:1.0` is retained for later TPs. The pre-existing staged deletion of the root `models/model.pkl` remains outside the TP9 commit and should be reviewed separately.

## Consolidation record

The outer MLOps folder had no Git repository. Its 102 files were moved into this repository and SHA-256 checked against a pre-move manifest at `docs/migration/outer-folder-source-manifest.json`. The former root now contains only this canonical repository. The three TP1-TP3 PDFs previously stored at this repository's root were moved, unchanged, to `docs/handouts/archive/repository-copies/` because they are not byte-identical to the selected handouts.

The migration did not reset the fraud Git worktree or discard its pre-existing staged changes and untracked TP8 work. Review `git status` before staging or committing anything.
