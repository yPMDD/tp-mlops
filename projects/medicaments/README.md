# TP5 medicines synthesis — preserved draft

This is the outer-folder medicines project, moved here with its files and relative layout intact. Run its original scripts from this directory if needed. The existing files are historical work and have not been rewritten or rerun during consolidation.

## Known gaps against the TP5 handout

- `src/train_pipeline.py` trains a Random Forest, which the handout prohibits.
- The current model uses three original columns; the handout requires at least seven numeric features, including two engineered features.
- The current `MLproject` points to a single training script; the handout requires separate preparation, training, and evaluation stages plus a parameterized F1 acceptance rule.
- The source workbook matches the expected record and target counts, but its measured size (480,176 bytes) and MD5 (`B061049E15097F513AE34026DE907CCE`) differ from the handout's values. The previous report states the handout's values, so verify the source and correct the report before submission.

The original captures, spreadsheet, cleaned CSV, report variants, and outer-folder MLflow database/artifacts are retained. The database contains experiments from multiple TPs; it is kept separate from the fraud project's tracking store.
