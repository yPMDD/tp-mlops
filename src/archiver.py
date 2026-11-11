"""Cree le ZIP de remise avec le code et son historique Git."""

import argparse
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *map(str, args)], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def main(destination):
    racine = Path.cwd().resolve()
    if git(racine, "status", "--porcelain"):
        raise ValueError("Le depot de remise doit etre propre avant la creation de l'archive.")
    if destination.resolve().is_relative_to(racine):
        raise ValueError("Creer le ZIP a cote du depot.")
    runtime = racine / ".runtime"
    runtime.mkdir(exist_ok=True)
    if not runtime.resolve().is_relative_to(racine):
        raise ValueError("Repertoire temporaire hors projet.")
    with tempfile.TemporaryDirectory(prefix="remise-", dir=runtime) as temporaire:
        temp = Path(temporaire).resolve()
        if not temp.is_relative_to(runtime.resolve()):
            raise ValueError("Destination temporaire hors projet.")
        clone = temp / racine.name
        git(racine, "clone", "--no-local", "--branch", "main", racine, clone)
        if git(racine, "for-each-ref", "--format=%(refname)", "refs/exps").strip():
            git(clone, "fetch", "--no-tags", racine, "+refs/exps/*:refs/exps/*")
        git(clone, "remote", "remove", "origin")
        git(clone, "fsck", "--no-reflogs")
        tags = set(git(clone, "tag", "--list").splitlines())
        if not {"donnees-v1", "donnees-v2"} <= tags:
            raise ValueError("Tags DVC absents du clone de remise.")
        avec = git(clone, "ls-files", "-z").split("\0")
        suivis = [clone / nom for nom in avec if nom]
        meta = [
            f for f in (clone / ".git").rglob("*") if f.is_file()
            and f.relative_to(clone / ".git").parts[0] not in {"logs", "hooks"}
            and f.name not in {"FETCH_HEAD", "ORIG_HEAD"}
        ]
        for fichier in suivis:
            rel = fichier.relative_to(clone)
            if fichier.suffix.lower() in {".xlsx", ".pkl", ".joblib"} or rel.parts[0] in {".venv", ".runtime"}:
                raise ValueError(f"Fichier de donnees ou environnement suivi : {rel}")
        with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as zipf:
            for fichier in suivis + meta:
                zipf.write(fichier, fichier.relative_to(temp).as_posix())
        with ZipFile(destination) as zipf:
            requis = {"compte-rendu.pdf", ".git/HEAD", "orange/remboursement.ows",
                      "nodered/remboursement.json", "MODEL_CARD.md", "dvc.lock", "reports/git-log.txt"}
            fichiers = {str(Path(p).relative_to(racine.name)).replace("\\", "/") for p in zipf.namelist()}
            if not requis <= fichiers or zipf.testzip() is not None:
                raise ValueError("Verification de l'archive non satisfaite.")
        print(f"ZIP verifie : {len(suivis)} fichiers suivis, {len(meta)} fichiers Git, tags {sorted(tags)}.")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("destination", type=Path)
    main(cli.parse_args().destination)
