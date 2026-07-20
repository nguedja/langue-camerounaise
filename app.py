import os
import random
from auth import register, login, logout
from flask import Flask, render_template, request, redirect, session, jsonify
from dictionnaire import traductions, structure
from database import Database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "langues-camerounaises-secret-2024")
db = Database()

NIVEAUX_ORDRE = ["debutant", "moyen", "fort", "tres_fort"]
NIVEAUX_LABELS = {
    "debutant": "Debutant",
    "moyen": "Moyen",
    "fort": "Fort",
    "tres_fort": "Tres Fort",
}


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


@app.route("/ping")
def ping():
    return "OK", 200


@app.route("/")
def index():
    return render_template("loading.html")


@app.route("/choix")
def choix():
    session.pop("admin", None)
    if "user_id" not in session:
        return redirect("/login")
    return render_template("choix.html")


ADMIN_PASSWORD = "admin123"


@app.route("/admin-password", methods=["GET", "POST"])
def admin_password():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/login")
        else:
            return render_template("admin_password.html", error="Mot de passe incorrect")
    return render_template("admin_password.html")


@app.route("/register", methods=["GET", "POST"])
def register_view():
    return register()


@app.route("/login", methods=["GET", "POST"])
def login_view():
    return login()


@app.route("/logout")
def logout_view():
    return logout()


@app.route("/accueil")
@login_required
def accueil():
    user = db.get_user_by_id(session["user_id"])
    return render_template("accueil.html", user=user)


@app.route("/setup-langue", methods=["GET", "POST"])
@login_required
def setup_langue():
    if request.method == "POST":
        langue_id = request.form.get("langue_id")
        if langue_id:
            db.set_langue_origin(session["user_id"], int(langue_id))
            session["langue_origin"] = int(langue_id)
            return redirect("/accueil")

    langues = db.get_langues()
    return render_template("setup_langue.html", langues=langues)


@app.route("/apprendre")
@login_required
def apprendre():
    user = db.get_user_by_id(session["user_id"])
    langue_origin = None
    progression_data = None

    if user and user[6]:
        langue_origin = db.get_langue_by_id(user[6])
        if langue_origin:
            progression_data = db.get_progression(session["user_id"], langue_origin[0])

    langues = db.get_langues()
    return render_template("apprendre.html",
                           user=user,
                           langues=langues,
                           langue_origin=langue_origin,
                           progression=progression_data,
                           niveaux=NIVEAUX_ORDRE,
                           niveaux_labels=NIVEAUX_LABELS)


@app.route("/contribuer", methods=["GET", "POST"])
@login_required
def contribuer():
    user = db.get_user_by_id(session["user_id"])
    langue_origin_id = user[6] if user else None

    if not langue_origin_id:
        return redirect("/setup-langue")

    langue = db.get_langue_by_id(langue_origin_id)
    niveau = request.args.get("niveau", "debutant")

    if request.method == "POST":
        mot_id = int(request.form["mot_id"])
        traduction_texte = request.form["traduction"].strip()
        if traduction_texte:
            db.ajouter_traduction(mot_id, langue_origin_id, traduction_texte, session["user_id"])
        return redirect(f"/contribuer?niveau={niveau}")

    mots_sans = db.get_mots_sans_traduction(langue_origin_id, niveau)
    mots_avec = db.get_mots_avec_traduction(langue_origin_id, niveau)
    total_mots = len(mots_sans) + len(mots_avec)
    nb_traduit = len(mots_avec)

    return render_template("contribuer.html",
                           langue=langue,
                           niveau=niveau,
                           mots_sans_traduction=mots_sans,
                           mots_avec_traduction=mots_avec,
                           total_mots=total_mots,
                           nb_traduit=nb_traduit,
                           niveaux=NIVEAUX_ORDRE,
                           niveaux_labels=NIVEAUX_LABELS)


@app.route("/api/traduire", methods=["POST"])
@login_required
def api_traduire():
    data = request.get_json()
    mot_id = data.get("mot_id")
    traduction = data.get("traduction", "").strip()
    langue_id = data.get("langue_id")

    if not mot_id or not traduction or not langue_id:
        return jsonify({"error": "Donnees manquantes"}), 400

    traduction_id = db.ajouter_traduction(mot_id, int(langue_id), traduction, session["user_id"])
    return jsonify({"success": True, "traduction_id": traduction_id})


@app.route("/evaluer/<int:langue_id>/<niveau>", methods=["GET", "POST"])
@login_required
def evaluer(langue_id, niveau):
    langue = db.get_langue_by_id(langue_id)
    if not langue:
        return redirect("/apprendre")

    if niveau not in NIVEAUX_ORDRE:
        return redirect("/apprendre")

    progression = db.get_progression(session["user_id"], langue_id)
    niveau_max_idx = 0
    if progression:
        niveau_max = progression[3]
        if niveau_max in NIVEAUX_ORDRE:
            niveau_max_idx = NIVEAUX_ORDRE.index(niveau_max)

    niveau_actuel_idx = NIVEAUX_ORDRE.index(niveau)
    if niveau_actuel_idx > niveau_max_idx:
        return redirect(f"/evaluer/{langue_id}/{NIVEAUX_ORDRE[niveau_max_idx]}")

    mots_avec = db.get_mots_avec_traduction(langue_id, niveau)
    if len(mots_avec) < 5:
        return render_template("evaluer_attente.html",
                               langue=langue,
                               niveau=niveau,
                               nb_traduit=len(mots_avec),
                               nb_requis=5,
                               niveaux_labels=NIVEAUX_LABELS)

    if request.method == "POST":
        score = int(session.get("eval_score", 0))
        total = int(session.get("eval_total", 0))
        pourcentage = db.sauvegarder_evaluation(session["user_id"], langue_id, niveau, score, total)

        if pourcentage == 100:
            niveau_idx = NIVEAUX_ORDRE.index(niveau)
            if niveau_idx < len(NIVEAUX_ORDRE) - 1:
                nouveau_niveau = NIVEAUX_ORDRE[niveau_idx + 1]
                db.mettre_a_jour_progression(session["user_id"], langue_id, nouveau_niveau)
                return redirect(f"/evaluer/{langue_id}/{nouveau_niveau}")
            return redirect(f"/resultat-evaluation/{langue_id}/{niveau}")
        else:
            return redirect(f"/evaluer/{langue_id}/{niveau}")

    random.shuffle(mots_avec)
    quiz_mots = mots_avec[:10]
    quiz_data = []
    for mot_id, mot, traduction, categorie in quiz_mots:
        autres = [m for m in mots_avec if m[0] != mot_id]
        random.shuffle(autres)
        mauvaises = [a[2] for a in autres[:2]]
        while len(mauvaises) < 2:
            mauvaises.append("???")
        options = [traduction] + mauvaises[:2]
        random.shuffle(options)
        quiz_data.append({
            "mot_id": mot_id,
            "mot": mot,
            "options": options,
            "bonne_reponse": traduction,
        })

    session["eval_quiz"] = quiz_data
    session["eval_index"] = 0
    session["eval_score"] = 0
    session["eval_total"] = len(quiz_data)
    session["eval_langue_id"] = langue_id
    session["eval_niveau"] = niveau

    return render_template("evaluer.html",
                           langue=langue,
                           niveau=niveau,
                           quiz_data=quiz_data,
                           niveaux_labels=NIVEAUX_LABELS)


@app.route("/evaluer-suivant", methods=["POST"])
@login_required
def evaluer_suivant():
    quiz_data = session.get("eval_quiz", [])
    index = session.get("eval_index", 0)
    reponse = request.form.get("reponse", "")

    if index < len(quiz_data):
        bonne = quiz_data[index]["bonne_reponse"]
        if reponse == bonne:
            session["eval_score"] = session.get("eval_score", 0) + 1

    session["eval_index"] = index + 1

    if session["eval_index"] >= len(quiz_data):
        return redirect("/evaluer-resultat")

    return redirect("/evaluer-question")


@app.route("/evaluer-question")
@login_required
def evaluer_question():
    quiz_data = session.get("eval_quiz", [])
    index = session.get("eval_index", 0)
    langue_id = session.get("eval_langue_id")
    niveau = session.get("eval_niveau")
    langue = db.get_langue_by_id(langue_id)

    if index >= len(quiz_data):
        return redirect("/evaluer-resultat")

    question = quiz_data[index]
    return render_template("evaluer_question.html",
                           question=question,
                           index=index + 1,
                           total=len(quiz_data),
                           langue=langue,
                           niveau=niveau)


@app.route("/evaluer-resultat")
@login_required
def evaluer_resultat():
    score = session.get("eval_score", 0)
    total = session.get("eval_total", 0)
    langue_id = session.get("eval_langue_id")
    niveau = session.get("eval_niveau")
    langue = db.get_langue_by_id(langue_id)

    pourcentage = int((score / total) * 100) if total > 0 else 0
    reussi = pourcentage == 100

    return render_template("evaluer_resultat.html",
                           score=score,
                           total=total,
                           pourcentage=pourcentage,
                           reussi=reussi,
                           langue=langue,
                           niveau=niveau)


@app.route("/resultat-evaluation/<int:langue_id>/<niveau>")
@login_required
def resultat_final(langue_id, niveau):
    langue = db.get_langue_by_id(langue_id)
    return render_template("resultat_final.html",
                           langue=langue,
                           niveau=niveau,
                           niveaux_labels=NIVEAUX_LABELS)


@app.route("/progression")
@login_required
def progression():
    user = db.get_user_by_id(session["user_id"])
    langue_origin_id = user[6] if user else None

    if not langue_origin_id:
        return redirect("/setup-langue")

    langue = db.get_langue_by_id(langue_origin_id)
    prog = db.get_progression(session["user_id"], langue_origin_id)

    niveaux_info = []
    for niv in NIVEAUX_ORDRE:
        nb_mots = len(db.get_mots_avec_traduction(langue_origin_id, niv))
        eval_data = db.get_derniere_evaluation(session["user_id"], langue_origin_id, niv)
        niveaux_info.append({
            "niveau": niv,
            "label": NIVEAUX_LABELS[niv],
            "nb_mots_traduit": nb_mots,
            "derniere_eval": eval_data,
        })

    return render_template("progression.html",
                           langue=langue,
                           progression=prog,
                           niveaux_info=niveaux_info,
                           niveaux_labels=NIVEAUX_LABELS)


@app.route("/produits")
@login_required
def produits():
    return render_template("produits.html")


@app.route("/decouvrir")
@login_required
def decouvrir():
    return render_template("decouvrir.html")


@app.route("/langues")
@login_required
def langues_view():
    langues = db.get_langues()
    return render_template("langues.html", langues=langues)


@app.route("/scores")
@login_required
def scores():
    return render_template("scores.html", scores=db.recuperer_scores())


@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/")
    users = db.get_all_users()
    total_users = len(users)
    total_scores = len(db.recuperer_scores())
    return render_template("admin_dashboard.html",
                           users=users,
                           total_users=total_users,
                           total_scores=total_scores)


@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):
    if "admin" not in session:
        return redirect("/")
    db.delete_user(user_id)
    return redirect("/admin")


@app.route("/paiement/mtn", methods=["GET", "POST"])
def paiement_mtn():
    if request.method == "POST":
        montant = request.form["montant"]
        if int(montant) < 500:
            return "Le montant doit etre au moins 500 FCFA"
        return f"Paiement MTN de {montant} FCFA recu !"
    return render_template("paiement_mtn.html")


@app.route("/paiement/orange", methods=["GET", "POST"])
def paiement_orange():
    if request.method == "POST":
        montant = request.form["montant"]
        if int(montant) < 500:
            return "Le montant doit etre au moins 500 FCFA"
        return f"Paiement Orange de {montant} FCFA recu !"
    return render_template("paiement_orange.html")


@app.route("/modules")
def modules():
    modules_list = [
        {"nom": "Compter de 1 a 100", "payant": False, "url": "/langues"},
        {"nom": "Quartiers et villages", "payant": False, "url": "/langues"},
        {"nom": "Chansons et proverbes", "payant": True, "url": "/langues"},
        {"nom": "Histoire et culture", "payant": True, "url": "/langues"},
    ]
    return render_template("modules.html", modules=modules_list)


@app.route("/api/mots/<int:langue_id>/<niveau>")
@login_required
def api_mots(langue_id, niveau):
    mots = db.get_mots_avec_traduction(langue_id, niveau)
    result = []
    for mot_id, mot, traduction, categorie in mots:
        result.append({
            "mot_id": mot_id,
            "mot_francais": mot,
            "traduction": traduction,
            "categorie": categorie,
        })
    return jsonify(result)


@app.route("/api/progression/<int:langue_id>")
@login_required
def api_progression(langue_id):
    prog = db.get_progression(session["user_id"], langue_id)
    if not prog:
        return jsonify({"niveau_max": "debutant", "mots_appris": 0})
    return jsonify({
        "niveau_max": prog[3],
        "mots_appris": prog[4],
    })


def seed_database():
    from dictionnaire import structure, traductions as trads_dict

    if db.compter_mots_total() > 0:
        return

    db.initialiser_langues()
    db.initialiser_categories()

    mot_categorie = {}
    for niveau, cats in structure.items():
        for cat_name, mots in cats.items():
            for mot in mots:
                mot_categorie[mot] = cat_name

    conn = db.connect()
    cur = conn.cursor()

    for niveau, cats in structure.items():
        for cat_name, mots in cats.items():
            cat = db.get_categorie_by_nom(cat_name)
            if not cat:
                continue
            cat_id = cat[0]
            for idx, mot in enumerate(mots):
                cur.execute(
                    "INSERT INTO mots_francais(mot, categorie_id, niveau, ordre) VALUES(?,?,?,?)",
                    (mot, cat_id, niveau, idx + 1),
                )

    conn.commit()

    cur.execute("SELECT id, mot FROM mots_francais")
    all_mots = cur.fetchall()

    cur.execute("SELECT id, nom FROM langues")
    all_langues = cur.fetchall()
    langue_map = {l[1].lower(): l[0] for l in all_langues}

    for mot_id, mot in all_mots:
        mot_lower = mot.lower()
        for key in trads_dict:
            if key.lower() == mot_lower or mot_lower in key.lower():
                for langue_name, traduction in trads_dict[key].items():
                    if langue_name in langue_map:
                        langue_id = langue_map[langue_name]
                        cur.execute(
                            "INSERT INTO traductions(mot_id, langue_id, traduction_texte, user_id, statut, date) VALUES(?,?,'system',0,'validee','2024-01-01')",
                            (mot_id, langue_id),
                        )
                break

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db.initialiser_langues()
    db.initialiser_categories()
    seed_database()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
