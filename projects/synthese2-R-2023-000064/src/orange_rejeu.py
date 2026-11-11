"""Evalue avec Orange et exporte le workflow Canvas rejouable."""

import argparse
import base64
import inspect
import json
import pickle
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from Orange.classification import LogisticRegressionLearner, NaiveBayesLearner, RandomForestLearner
from Orange.data import ContinuousVariable, DiscreteVariable, Domain, StringVariable, Table
from Orange.data.pandas_compat import table_to_frame
from Orange.evaluation import AUC, F1, TestOnTestData
from orangewidget.utils.filedialogs import RecentPath
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import train_test_split

import preparer as preparation
from configuration import charger_configuration
from preparer import CIBLE, VARIABLES, preparer


def preparer_table(table):
    brut = table_to_frame(table, include_metas=True)
    donnees = preparer(brut)
    metas = ("CODE", "NOM", "DCI1", "UNITE_DOSAGE1", "PRESENTATION", "FORME")
    domaine = Domain(
        [ContinuousVariable(nom) for nom in VARIABLES],
        DiscreteVariable(CIBLE, values=("0", "1")),
        metas=[StringVariable(nom) for nom in metas],
    )
    return Table.from_numpy(
        domaine, donnees[list(VARIABLES)].to_numpy(dtype=float), donnees[CIBLE].to_numpy(),
        metas=brut[list(metas)].astype(str).to_numpy(dtype=object),
    )


def apprenant_foret(config):
    return RandomForestLearner(
        n_estimators=config["foret"]["arbres"], max_depth=config["foret"]["profondeur"],
        random_state=config["donnees"]["graine"],
    )


def repartir(table, graine, part_test):
    train, test = train_test_split(np.arange(len(table)), test_size=part_test,
                                   stratify=table.Y, random_state=graine)
    return table[train], table[test]


def personnel(table, graine):
    indices = np.flatnonzero(table.Y == 1)
    rang = graine % len(indices)
    return table[[indices[rang]]]


def exporter(config, source, destination, expliquer):
    destination.parent.mkdir(parents=True, exist_ok=True)
    titre = config["suivi"]["experience"]
    graine = config["donnees"]["graine"]
    part_test = config["donnees"]["part_test"]
    arbres = config["foret"]["arbres"]
    profondeur = config["foret"]["profondeur"]
    scheme = ET.Element("scheme", version="2.0", title=titre, description="V1 CNOPS, test séparé stratifié")
    nodes, links = ET.SubElement(scheme, "nodes"), ET.SubElement(scheme, "links")
    ET.SubElement(scheme, "annotations")
    ET.SubElement(scheme, "thumbnail")
    props = ET.SubElement(scheme, "node_properties")

    def noeud(nom, classe, x, y, reglages=None, projet="Orange3", titre=None):
        i = str(len(nodes))
        ET.SubElement(nodes, "node", id=i, name=nom, qualified_name=classe, project_name=projet,
                      version="", title=titre or nom, position=f"({x}.0, {y}.0)")
        if reglages is not None:
            elem = ET.SubElement(props, "properties", node_id=i, format="pickle")
            elem.text = base64.b64encode(pickle.dumps(reglages)).decode("ascii")
        return i

    def lien(a, sortie, b, entree):
        ET.SubElement(links, "link", id=str(len(links)), source_node_id=a, sink_node_id=b,
                      source_channel=sortie, sink_channel=entree, enabled="true")

    def script(titre, code, x, y):
        settings = {"__version__": 2, "scriptText": code,
                    "scriptLibrary": [{"name": titre, "script": code, "filename": None}]}
        return noeud("Python Script", "Orange.widgets.data.owpythonscript.OWPythonScript",
                     x, y, settings, titre=titre)

    file = noeud("File", "Orange.widgets.data.owfile.OWFile", 80, 190,
                 {"__version__": 2, "source": 0,
                  "active_path": RecentPath(source.name, "basedir", "../" + source.as_posix())})
    prep = script(
        "Préparer CNOPS",
        inspect.getsource(preparation) + "\n"
        "from Orange.data import ContinuousVariable, DiscreteVariable, Domain, StringVariable, Table\n"
        "from Orange.data.pandas_compat import table_to_frame\n\n"
        + inspect.getsource(preparer_table) + "\nout_data = preparer_table(in_data) if in_data is not None else None\n",
        230, 190,
    )
    lien(file, "Data", prep, "Data")
    partitions = []
    for i, (nom, y) in enumerate((("Entraînement 75 %", 130), ("Test 25 %", 265))):
        code = (
            "import numpy as np\nfrom sklearn.model_selection import train_test_split\n\n"
            + inspect.getsource(repartir) + "\n"
            + f"out_data = repartir(in_data, {graine}, {part_test})[{i}] if in_data is not None else None\n"
        )
        branche = script(nom, code, 405, y)
        lien(prep, "Data", branche, "Data")
        partitions.append(branche)
    train, test = partitions
    rf = script(
        "Forêt Orange (graine G)",
        "from Orange.classification import RandomForestLearner\n"
        + f"out_learner = RandomForestLearner(n_estimators={arbres}, max_depth={profondeur}, random_state={graine})\n"
        "out_classifier = out_learner(in_data) if in_data is not None else None\n",
        565, 75,
    )
    lien(train, "Data", rf, "Data")
    log = noeud("Logistic Regression", "Orange.widgets.model.owlogisticregression.OWLogisticRegression", 540, 365)
    nb = noeud("Naive Bayes", "Orange.widgets.model.ownaivebayes.OWNaiveBayes", 540, 465)
    scores = noeud("Test and Score", "Orange.widgets.evaluate.owtestandscore.OWTestAndScore", 735, 255,
                   {"__version__": 4, "resampling": 5})
    matrix = noeud("Confusion Matrix", "Orange.widgets.evaluate.owconfusionmatrix.OWConfusionMatrix", 920, 255)
    lien(train, "Data", scores, "Data")
    lien(test, "Data", scores, "Test Data")
    for learner in (rf, log, nb):
        lien(learner, "Learner", scores, "Learner")
    lien(scores, "Evaluation Results", matrix, "Evaluation Results")
    if expliquer:
        exemple = script("Médicament personnel", "import numpy as np\n\n" + inspect.getsource(personnel)
                         + f"\nout_data = personnel(in_data, {graine}) if in_data is not None else None\n", 415, 20)
        widget = noeud("Explain Prediction", "orangecontrib.explain.widgets.owexplainprediction.OWExplainPrediction",
                       790, 75, projet="Orange3-Explain")
        lien(prep, "Data", exemple, "Data")
        lien(exemple, "Data", widget, "Data")
        lien(train, "Data", widget, "Background Data")
        lien(rf, "Classifier", widget, "Model")
    ET.indent(scheme, space="  ")
    ET.ElementTree(scheme).write(destination, encoding="utf-8", xml_declaration=True)


def main(args):
    config = charger_configuration()
    source = Path(config["suivi"]["sources"]["v1"])
    raw = Table(str(source))
    data = preparer_table(raw)
    graine = config["donnees"]["graine"]
    train, test = repartir(data, graine, config["donnees"]["part_test"])
    rf = apprenant_foret(config)
    exporter(config, source, args.workflow, args.explain)
    if args.explain:
        from orangecontrib.explain.explainer import explain_predictions
        exemple = personnel(data, graine)
        shap, pred, transforme, _, base = explain_predictions(rf(train), exemple, train)
        contributions = dict(zip([v.name for v in transforme.domain.attributes], map(float, shap[1][0])))
        resultat = {"probabilite": float(pred[0, 1]), "base": float(base[1]),
                    "contributions": dict(sorted(contributions.items(), key=lambda x: -abs(x[1])))}
    else:
        from Orange.widgets.model.owlogisticregression import OWLogisticRegression
        logistic = LogisticRegressionLearner(
            C=OWLogisticRegression.strength_C, max_iter=OWLogisticRegression.max_iter, random_state=0
        )
        learners = [rf, logistic, NaiveBayesLearner()]
        resultats = TestOnTestData(train, test, learners)
        aucs = AUC(resultats)
        f1s = F1(resultats, target=1)
        scores = []
        for i, nom in enumerate(("Forêt aléatoire", "Régression logistique", "Naive Bayes")):
            matrix = confusion_matrix(resultats.actual, resultats.predicted[i], labels=[0, 1])
            scores.append({"apprenant": nom, "auc": float(aucs[i]), "f1": float(f1s[i]),
                           "matrice_reel_lignes_predit_colonnes": matrix.tolist(),
                           "non_rembourses_manques": int(matrix[1, 0])})
        resultat = {"source": source.as_posix(), "n_train": len(train), "n_test": len(test),
                    "classe_1_test": int(test.Y.sum()), "scores": scores}
    texte = json.dumps(resultat, ensure_ascii=False, indent=2)
    args.resultat.write_text(texte + "\n", encoding="utf-8")
    print(texte)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("workflow", type=Path)
    cli.add_argument("resultat", type=Path)
    cli.add_argument("--explain", action="store_true")
    main(cli.parse_args())
