"""Charge le workflow dans Orange Canvas et verifie ses signaux d'evaluation."""

import argparse
import json
import time
from pathlib import Path

from AnyQt.QtWidgets import QApplication
from Orange.canvas.config import Config
from Orange.evaluation import AUC, F1
from orangecanvas.registry import WidgetRegistry
from orangecanvas.scheme.readwrite import scheme_load
from orangewidget.workflow.widgetsscheme import WidgetsScheme
from sklearn.metrics import confusion_matrix


def main(workflow, sortie):
    app = QApplication([])
    registry = WidgetRegistry()
    Config().widget_discovery(registry).run(Config.widgets_entry_points())
    scheme = WidgetsScheme(env={"basedir": str(workflow.resolve().parent)})
    with workflow.open("rb") as fichier:
        scheme_load(scheme, fichier, registry=registry)
    widgets = {n.title: scheme.widget_for_node(n) for n in scheme.nodes}
    scheme.signal_manager.start()
    matrix = widgets["Confusion Matrix"]
    explique = widgets.get("Explain Prediction")

    def resultat_explication():
        return getattr(explique, "_OWExplainPrediction__results", None)

    fin = time.monotonic() + 45
    while (matrix.results is None or explique is not None and resultat_explication() is None) and time.monotonic() < fin:
        app.processEvents()
        time.sleep(0.03)
    if matrix.results is None or explique is not None and resultat_explication() is None:
        erreurs = {nom: [str(x) for x in widget.Error.active] for nom, widget in widgets.items()}
        fichier = widgets["File"]
        print(f"File : {fichier.loaded_file}, donnees : {fichier.data is not None}")
        for nom, widget in widgets.items():
            if hasattr(widget, "console"):
                print(nom, widget.console.toPlainText()[-1200:])
        evaluation = widgets["Test and Score"]
        print("Test and Score :", evaluation.resampling, evaluation.data is not None,
              evaluation.test_data is not None, len(evaluation.learners))
        raise RuntimeError(f"Evaluation absente : {erreurs}")
    r = matrix.results
    preuve = {"widgets": list(widgets), "liens": len(scheme.links),
              "auc": AUC(r).tolist(), "f1_classe_1": F1(r, target=1).tolist(),
              "matrices": [confusion_matrix(r.actual, p, labels=[0, 1]).tolist() for p in r.predicted]}
    if explique is not None:
        explication = resultat_explication()
        explique.target_index = 1
        explique.update_scene()
        noms = [a.name for a in explication.transformed_data.domain.attributes]
        preuve["explain_classe_1"] = {
            "probabilite": float(explication.predictions[0, 1]),
            "base": float(explication.base_value[1]),
            "contributions": dict(zip(noms, map(float, explication.values[1][0]))),
        }
    sortie.write_text(json.dumps(preuve, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Orange Canvas : {len(widgets)} widgets, {len(scheme.links)} liens, {len(r.actual)} lignes test.")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("workflow", type=Path)
    cli.add_argument("sortie", type=Path)
    args = cli.parse_args()
    main(args.workflow, args.sortie)
