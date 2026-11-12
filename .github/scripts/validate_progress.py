#!/usr/bin/env python3
from pathlib import Path
import os, re, subprocess, sys, unicodedata

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "travail"
PROOFS = WORK / "preuves"


def read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def norm(s):
    decomposed = unicodedata.normalize("NFD", s)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", stripped).strip().lower()


def proof(n, minimum=30):
    p = PROOFS / f"defi{n:02d}.txt"
    return p.exists() and len(read(p).strip()) >= minimum


def git(*args):
    r = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def git_ok(*args):
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True).returncode == 0


def rel(path):
    return str(path.relative_to(ROOT)).replace("\\", "/")


def tracked(path):
    return bool(git("ls-files", "--error-unmatch", rel(path)))


def last_commit(path):
    return git("log", "-1", "--format=%H", "--", rel(path))


def branch_ref(name):
    for ref in (f"origin/{name}", name, f"refs/remotes/origin/{name}", f"refs/heads/{name}"):
        if git_ok("rev-parse", "--verify", ref):
            return ref
    return ""


def branch_contains(name, commit):
    ref = branch_ref(name)
    return bool(ref and commit and git_ok("merge-base", "--is-ancestor", commit, ref))


def identite_has_name(text):
    cleaned = norm(text)
    cleaned = re.sub(r"git\s+version\s+[^\s]+", "", cleaned)
    for boilerplate in (
        "prenom nom",
        "classe",
        "terminale sti2d sin",
        "copiez ci-dessous la ligne obtenue avec git --version",
        "version de git",
    ):
        cleaned = cleaned.replace(boilerplate, "")
    letters = re.findall(r"[a-z]", cleaned)
    return len(letters) >= 2


def has_commit_hash(text):
    candidates = re.findall(r"\b[0-9a-f]{6,40}\b", text.lower())
    if not candidates:
        return False
    all_hashes = git("log", "--all", "--format=%H").lower().splitlines()
    if not all_hashes:
        return True
    return any(any(h.startswith(c) for h in all_hashes) for c in candidates)


def valid(n):
    t = read(WORK / "index.html")
    nt = norm(t)
    css = read(WORK / "style.css")
    ncss = norm(css)

    if n == 1:
        id_txt = read(WORK / "identite.txt")
        return "git version" in id_txt.lower() and identite_has_name(id_txt)

    if n == 2:
        return (
            (WORK / "index.html").exists()
            and (WORK / "style.css").exists()
            and "<h1" in nt
            and "projet" in nt
            and "sin" in nt
            and "font-family" in ncss
        )

    if n == 3:
        return proof(3) and "mon premier projet sin" in nt

    if n == 4:
        return proof(4) and "premier commit" in nt

    if n == 5:
        return proof(5) and has_commit_hash(read(PROOFS / "defi05.txt"))

    if n == 6:
        return proof(6) and "decouverte de git diff" in nt

    if n == 7:
        return proof(7) and "erreur a supprimer" not in nt

    if n == 8:
        gi_content = read(WORK / ".gitignore") + "\n" + read(ROOT / ".gitignore")
        return (
            proof(8)
            and "secret.txt" in gi_content
            and not tracked(WORK / "secret.txt")
            and not tracked(ROOT / "secret.txt")
        )

    if n == 9:
        c = last_commit(PROOFS / "defi09.txt")
        return proof(9) and branch_contains("feature-design", c)

    if n == 10:
        c = last_commit(PROOFS / "defi10.txt")
        return (
            proof(10)
            and ("design sin" in ncss or "text-align" in ncss)
            and bool(branch_ref("feature-design"))
            and branch_contains("main", c)
        )

    if n == 11:
        return proof(11) and bool(git("remote", "get-url", "origin"))

    if n == 12:
        pf = read(WORK / "projet-final.html").lower()
        return proof(12) and "<h1" in pf and "<p" in pf

    return False


def diagnostic(n):
    p = PROOFS / f"defi{n:02d}.txt"
    if n >= 3 and not p.exists():
        wrong_names = [
            WORK / f"defi{n:02d}.txt",
            PROOFS / f"defi-{n:02d}.txt",
            PROOFS / f"defi{n}.txt",
        ]
        for w in wrong_names:
            if w.exists():
                return (
                    f"Attention au chemin/nom du fichier : vous avez créé `{rel(w)}` "
                    f"au lieu de `travail/preuves/defi{n:02d}.txt`."
                )
        return f"Le fichier `travail/preuves/defi{n:02d}.txt` est absent. Créez-le et répondez aux questions."
    if n >= 3 and len(read(p).strip()) < 30:
        return f"Le compte rendu `travail/preuves/defi{n:02d}.txt` est trop court. Répondez avec des phrases complètes."

    if n == 1:
        id_txt = read(WORK / "identite.txt")
        if "git version" in id_txt.lower() and not identite_has_name(id_txt):
            return "N'oubliez pas d'écrire votre Prénom et NOM dans `travail/identite.txt` en plus de la version de Git."
        return "Complétez `travail/identite.txt` avec votre nom et la ligne obtenue grâce à `git --version`."
    if n == 3:
        if proof(3) and "mon premier projet sin" not in norm(read(WORK / "index.html")):
            return "Votre preuve `defi03.txt` est bien présente, mais `<p>Mon premier projet SIN</p>` n'est pas dans `travail/index.html` sur GitHub. Vérifiez que vous avez bien enregistré `index.html` (Ctrl+S) puis fait `git add travail/index.html`, `git commit` et `git push`."
    if n == 4:
        if proof(4) and "premier commit" not in norm(read(WORK / "index.html")):
            return "Votre preuve `defi04.txt` est bien présente, mais `<p>Premier commit</p>` n'apparaît pas dans `travail/index.html` sur GitHub. N'oubliez pas `git add travail/index.html`, `git commit` et `git push`."
    if n == 5:
        return "Lancez `git log --oneline` et copiez bien le hash court (ex: `a1b2c3d`) et le message d'un commit dans `travail/preuves/defi05.txt`."
    if n == 8:
        if tracked(WORK / "secret.txt") or tracked(ROOT / "secret.txt"):
            return "Attention : `secret.txt` a été ajouté à Git par erreur ! Exécutez `git rm --cached travail/secret.txt`, vérifiez que `secret.txt` est dans `travail/.gitignore`, puis refaites un commit et `git push`."
    if n == 10:
        c = last_commit(PROOFS / "defi10.txt")
        if branch_contains("feature-design", c) and not branch_contains("main", c):
            return "Votre travail est bien sur `feature-design`. Il ne vous reste plus qu'à revenir sur `main` (`git switch main`), fusionner (`git merge feature-design`) et pousser (`git push`)."

    hints = {
        2: "Vérifiez `travail/index.html` (`<h1>Projet Terminale SIN</h1>`) et `travail/style.css` (`body { font-family: Arial; }`), puis assurez-vous qu'ils ont été committés et poussés.",
        3: "Vérifiez la phrase `<p>Mon premier projet SIN</p>` dans `travail/index.html` et votre compte rendu `travail/preuves/defi03.txt`.",
        4: "Vérifiez que `travail/index.html` contient `<p>Premier commit</p>` et que `travail/preuves/defi04.txt` est enregistré.",
        6: "Ajoutez `<p>Découverte de git diff</p>` dans `travail/index.html` et complétez `travail/preuves/defi06.txt`.",
        7: "La chaîne `ERREUR A SUPPRIMER` ne doit plus être présente dans `travail/index.html` après `git restore`.",
        8: "Vérifiez `travail/.gitignore` et assurez-vous que `secret.txt` n'est pas suivi par Git.",
        9: "Le compte rendu `travail/preuves/defi09.txt` doit être committé puis publié sur la branche `feature-design` (`git push -u origin feature-design`).",
        10: "Modifiez `travail/style.css` et `travail/preuves/defi10.txt` sur `feature-design`, puis fusionnez `feature-design` dans `main` et poussez `main`.",
        11: "Vérifiez `git remote -v` puis répondez aux questions dans `travail/preuves/defi11.txt`.",
        12: "Vérifiez que `travail/projet-final.html` contient un `<h1>` et un `<p>`, complétez `travail/preuves/defi12.txt`, puis faites `add`, `commit` et `push`.",
    }
    return hints.get(n, "Commencez par `git status`, relisez le défi puis vérifiez vos fichiers.")


completed = 0
for n in range(1, 13):
    if valid(n):
        completed = n
    else:
        break

lines = ["# 🎓 Terminale SIN — Progression", ""]
if completed == 0:
    lines += [
        "## 🚦 Défi 01 à réaliser",
        "",
        "Suivez l'énoncé du Défi 01 puis complétez `travail/identite.txt`.",
        "",
        f"**🛟 Aide :** {diagnostic(1)}",
    ]
elif completed >= 12:
    lines += [
        "# 🏆 Parcours terminé !",
        "",
        "🟩" * 12,
        "",
        "Vous avez validé les **12 défis**. Félicitations ! 🎉 Vous savez maintenant utiliser les bases de Git et GitHub.",
    ]
else:
    nxt = completed + 1
    percent = round(completed / 12 * 100)
    bar = "🟩" * completed + "⬜" * (12 - completed)
    bank = ROOT / ".github" / "bank" / f"defi-{nxt:02d}.md"
    bank_text = read(bank) if bank.exists() else f"⚠️ Énoncé du Défi {nxt:02d} introuvable."
    lines += [
        f"## ✅ Défis validés : {completed}/12 — {percent}%",
        "",
        bar,
        "",
        f"# 🔓 Défi {nxt:02d} à réaliser",
        "",
        bank_text,
        "",
        "---",
        "",
        f"> **🛟 Aide au diagnostic** *(si vous venez de tenter le Défi {nxt:02d} et qu'il n'est pas encore validé)* :",
        f"> {diagnostic(nxt)}",
    ]

summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    Path(summary).write_text("\n".join(lines), encoding="utf-8")
print(f"Progression détectée : {completed}/12")
sys.exit(0)
