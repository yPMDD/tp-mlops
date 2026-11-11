"""Explications et mesures sur la version V1 de production."""

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import PartialDependenceDisplay, permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

from configuration import charger_configuration
from medicament_personnel import selection_personnelle
from preparer import CIBLE, VARIABLES, lire_classeur, preparer, separer


@dataclass
class Contexte:
    config: dict
    modele: object
    train: pd.DataFrame
    test: pd.DataFrame
    identite: dict
    personnel: pd.DataFrame
    repertoire: Path

    @property
    def graine(self):
        return self.config["donnees"]["graine"]

    @property
    def reglages(self):
        return self.config["audit"]

    @property
    def X(self):
        return self.test[list(VARIABLES)]

    @property
    def y(self):
        return self.test[CIBLE]

    def enregistrer(self, numero, resultat):
        chemin = self.repertoire / f"f{numero}-resultat.json"
        chemin.write_text(json.dumps(resultat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def ouvrir(repertoire):
    config = charger_configuration()
    suivi = config["suivi"]
    mlflow.set_tracking_uri(suivi["uri"])
    version = mlflow.MlflowClient().get_model_version_by_alias(suivi["modele_rf"], "production")
    if version.tags.get("version_donnees") != "v1":
        raise ValueError("L'audit demande la foret de production V1.")
    modele = mlflow.sklearn.load_model(f"models:/{suivi['modele_rf']}/{version.version}")
    donnees = preparer(lire_classeur(Path(suivi["sources"]["v1"])))
    train, test = separer(donnees, config["donnees"]["graine"], config["donnees"]["part_test"])
    identite, personnel = selection_personnelle(config, "v1")
    return Contexte(config, modele, train, test, identite, personnel, repertoire)


def f1(ctx):
    resultat = permutation_importance(
        ctx.modele, ctx.X, ctx.y, scoring="f1",
        n_repeats=ctx.reglages["repetitions_permutation"], random_state=ctx.graine,
    )
    perm = pd.Series(resultat.importances_mean, index=VARIABLES).sort_values(ascending=False)
    mdi = pd.Series(ctx.modele.feature_importances_, index=VARIABLES).sort_values(ascending=False)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), layout="constrained")
    for ax, scores, titre in zip(axes, (perm, mdi), ("Permutation sur le test", "MDI de la forêt")):
        scores.sort_values().plot.barh(ax=ax, color="#176a73")
        ax.set_title(titre)
    fig.savefig(ctx.repertoire / "f1-importances.png", dpi=160)
    plt.close(fig)
    return {"permutation": perm.to_dict(), "mdi": mdi.to_dict(),
            "repetitions": ctx.reglages["repetitions_permutation"]}


def f2(ctx):
    variables = ["nb_meme_dci", "ppv"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    graph = PartialDependenceDisplay.from_estimator(
        ctx.modele, ctx.X.astype({"nb_meme_dci": "float64"}), variables,
        kind="both", response_method="predict_proba",
        subsample=ctx.reglages["ice_exemples"], grid_resolution=ctx.reglages["points_pdp"],
        random_state=ctx.graine, ax=axes,
    )
    fig.savefig(ctx.repertoire / "f2-pdp-ice.png", dpi=160)
    plt.close(fig)
    resume = {}
    for variable, r in zip(variables, graph.pd_results):
        grille, moyenne, individuel = r["grid_values"][0], r["average"][0], r["individual"][0]
        delta = individuel[:, -1] - individuel[:, 0]
        resume[variable] = {
            "grille": grille.tolist(), "pdp": moyenne.tolist(),
            "delta_ice_quantiles": np.quantile(delta, [0.1, 0.5, 0.9]).tolist(),
        }
    return resume


def f3(ctx):
    brut = lire_classeur(Path(ctx.config["suivi"]["sources"]["v1"]))
    dci = brut.loc[brut["CODE"].eq(ctx.identite["CODE"]), "DCI1"].iloc[0]
    p = float(ctx.modele.predict_proba(ctx.personnel)[0, 1])
    classe = int(p >= ctx.reglages["seuil_prediction"])
    return {**ctx.identite, "dci": dci, "entrees": ctx.personnel.to_dict(orient="records")[0],
            "probabilite": p, "classe_predite": classe, "classe_reelle": 1}


def f4(ctx):
    import shap

    exp = shap.TreeExplainer(ctx.modele)(ctx.personnel)
    valeurs, base = exp.values[0, :, 1], float(exp.base_values[0, 1])
    p = float(ctx.modele.predict_proba(ctx.personnel)[0, 1])
    if not np.isclose(base + valeurs.sum(), p, atol=1e-6):
        raise ValueError("La somme SHAP ne reproduit pas la prediction.")
    exp1 = shap.Explanation(values=valeurs, base_values=base, data=ctx.personnel.iloc[0].to_numpy(),
                            feature_names=list(VARIABLES))
    shap.plots.waterfall(exp1, show=False)
    plt.savefig(ctx.repertoire / "f4-shap.png", dpi=160, bbox_inches="tight")
    plt.close()
    contributions = sorted(zip(VARIABLES, map(float, valeurs)), key=lambda x: -abs(x[1]))
    return {"base": base, "contributions": dict(contributions), "somme": float(valeurs.sum()),
            "base_plus_somme": float(base + valeurs.sum()), "probabilite": p}


def f6(ctx):
    original = ctx.personnel.copy()
    p = lambda x: float(ctx.modele.predict_proba(x)[0, 1])
    statut = original.copy()
    statut["generique"] = 1 - statut["generique"]
    prix = original.copy()
    prix["ppv"] *= 1 - ctx.reglages["variation_ppv"]
    prix["ecart_br"] = prix["ppv"] - prix["prix_br"]
    return {"original": p(original), "statut_inverse": p(statut),
            "nouveau_statut": int(statut["generique"].iloc[0]),
            "ppv_initial": float(original["ppv"].iloc[0]), "nouveau_ppv": float(prix["ppv"].iloc[0]),
            "nouvel_ecart_br": float(prix["ecart_br"].iloc[0]), "ppv_modifie": p(prix)}


def f7(ctx):
    from lime.lime_tabular import LimeTabularExplainer

    matrice = []
    for i in range(ctx.reglages["essais_lime"]):
        seed = ctx.graine + i
        exp = LimeTabularExplainer(
            ctx.train[list(VARIABLES)].to_numpy(), feature_names=list(VARIABLES),
            class_names=["remboursé", "non remboursé"], random_state=seed,
            categorical_features=[VARIABLES.index(x) for x in ("generique", "injectable", "comprime")],
        ).explain_instance(
            ctx.personnel.iloc[0].to_numpy(),
            lambda a: ctx.modele.predict_proba(pd.DataFrame(a, columns=VARIABLES)),
            labels=(1,), num_features=len(VARIABLES), num_samples=ctx.reglages["voisins_lime"],
        )
        matrice.append({"graine": seed, "r2_local": float(exp.score),
                        "poids": {VARIABLES[j]: float(poids) for j, poids in exp.local_exp[1]}})
    signes = {nom: ["+" if r["poids"][nom] > 0 else "-" if r["poids"][nom] < 0 else "0" for r in matrice]
              for nom in VARIABLES}
    return {"essais": matrice, "signes": signes,
            "stables": [n for n, s in signes.items() if len(set(s)) == 1],
            "variables_changeantes": [n for n, s in signes.items() if len(set(s)) > 1]}


def f8(ctx):
    from fairlearn.metrics import MetricFrame, false_positive_rate, selection_rate

    groupe = ctx.X["generique"].map({0: "Princeps", 1: "Générique"})
    sans = [x for x in VARIABLES if x != "generique"]
    modele_sans = clone(ctx.modele).fit(ctx.train[sans], ctx.train[CIBLE])
    resume = {}
    for nom, prediction in (("avec_generique", ctx.modele.predict(ctx.X)),
                            ("sans_generique", modele_sans.predict(ctx.X[sans]))):
        frame = MetricFrame(metrics={"taux_classe_1": selection_rate, "taux_fausses_alertes": false_positive_rate},
                            y_true=ctx.y, y_pred=prediction, sensitive_features=groupe)
        resume[nom] = {"par_groupe": frame.by_group.to_dict(orient="index"),
                       "ecart_absolu": frame.difference().to_dict()}
    return resume


def f9(ctx):
    colonnes = [n for n in VARIABLES if n not in ("prix_br", "ecart_br")]
    sans = clone(ctx.modele).fit(ctx.train[colonnes], ctx.train[CIBLE])
    return {"f1_reference": f1_score(ctx.y, ctx.modele.predict(ctx.X)),
            "f1_sans_prix_br_ecart_br": f1_score(ctx.y, sans.predict(ctx.X[colonnes]))}


def f10(ctx):
    X = ctx.train[list(VARIABLES)]
    y = ctx.train[CIBLE]
    log = make_pipeline(StandardScaler(), LogisticRegression(
        random_state=ctx.graine, max_iter=ctx.config["suivi"]["max_iter_logistique"]
    )).fit(X, y)
    tree = DecisionTreeClassifier(max_depth=ctx.config["orchestration"]["profondeur_echec"],
                                  random_state=ctx.graine).fit(X, y)
    indice = VARIABLES.index("generique")
    coef = float(log[-1].coef_[0, indice])
    return {
        "f1_foret": f1_score(ctx.y, ctx.modele.predict(ctx.X)),
        "f1_logistique": f1_score(ctx.y, log.predict(ctx.X)),
        "f1_arbre": f1_score(ctx.y, tree.predict(ctx.X)),
        "coef_generique_standardise": coef, "rapport_cotes_par_ecart_type": float(np.exp(coef)),
        "rapport_cotes_de_0_a_1": float(np.exp(coef / log[0].scale_[indice])),
        "regles_arbre": export_text(tree, feature_names=list(VARIABLES)),
    }


QUESTIONS = {1: f1, 2: f2, 3: f3, 4: f4, 6: f6, 7: f7, 8: f8, 9: f9, 10: f10}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("questions", type=int, nargs="+", choices=tuple(QUESTIONS))
    cli.add_argument("--sortie", type=Path, default=Path("reports"))
    args = cli.parse_args()
    ctx = ouvrir(args.sortie)
    for numero in args.questions:
        ctx.enregistrer(numero, QUESTIONS[numero](ctx))
        print(f"F{numero} enregistre.", flush=True)
