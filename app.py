import os
from auth import register, login, logout
from flask import Flask, render_template, request, redirect, session
from dictionnaire import langues
from quizz_manager import QuizManager
from database import Database

app = Flask(__name__)
app.secret_key = "secret123"
db = Database()
@app.route("/ping")
def ping():
    return "OK", 200
@app.route("/")
def index():
    return render_template("loading.html")
@app.route("/choix")
def choix():
    session.pop("admin", None)   # 🔥 Désactive admin si présent
    if "user_id" not in session:
        redirect ("/login.html")
    return render_template("choix.html")

ADMIN_PASSWORD = "admin123"   # 🔐 mot de passe admin


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
def accueil():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("accueil.html")

@app.route("/apprendre")
def apprendre():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("apprendre.html")

@app.route("/produits")
def produits():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("produits.html")

@app.route("/decouvrir")
def decouvrir():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("decouvrir.html")



@app.route("/langues")
def langues_view():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("langues.html", langues=langues.keys())

@app.route("/niveaux/<langue>")
def niveaux(langue):
    if "user_id" not in session:
        return redirect("/login")
    return render_template(
        "niveaux.html",
        langue=langue,
        niveaux=langues[langue].keys()
    )

@app.route("/demarrer/<langue>/<niveau>")
def demarrer(langue, niveau):
    if "user_id" not in session:
        return redirect("/login")
    quiz = QuizManager(langues[langue][niveau])
    session["quiz"] = quiz.questions
    session["index"] = 0
    session["score"] = 0
    session["langue"] = langue
    session["niveau"] = niveau
    return redirect("/question")

@app.route("/question", methods=["GET", "POST"])
def question():
    if "user_id" not in session:
        return redirect("/login")
    questions = session["quiz"]
    index = session["index"]

    if index >= len(questions):
        return redirect("/resultat")

    question, options = questions[index]
    bonne = options[0]
    options = options.copy()

    import random
    random.shuffle(options)

    if request.method == "POST":
        choix = request.form["reponse"]
        if choix == bonne:
            session["score"] += 1
            session["feedback"] = ("ok", bonne)
        else:
            session["feedback"] = ("ko", bonne)

        session["index"] += 1
        return redirect("/feedback")

    return render_template(
    "question.html",
    question=question,
    options=options
)

@app.route("/feedback")
def feedback():
    if "user_id" not in session:
        return redirect("/login")
    etat, bonne = session["feedback"]

    langue = session["langue"]
    niveau = session["niveau"]

    audio_path = f"audio/{langue}/{niveau}/{bonne}.mp3"

    return render_template(
        "feedback.html",
        etat=etat,
        bonne=bonne,
        audio_path=audio_path
    )


@app.route("/resultat", methods=["GET", "POST"])
def resultat():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "POST":
        db.ajouter_score(
            request.form["nom"],
            request.form["numero"],
            session["langue"],
            session["niveau"],
            session["score"],
            len(session["quiz"])
        )
        return redirect("/scores")

    return render_template(
        "resultat.html",
        score=session["score"],
        total=len(session["quiz"])
    )

@app.route("/scores")
def scores():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("scores.html", scores=db.recuperer_scores())
@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/")

    users = db.get_all_users()
    total_users = len(users)
    total_scores = len(db.recuperer_scores())

    return render_template(
        "admin_dashboard.html",
        users=users,
        total_users=total_users,
        total_scores=total_scores
    )
@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):
    if "admin" not in session:
        return redirect("/")

    db.delete_user(user_id)
    return redirect("/admin")
# Pages paiement
@app.route("/paiement/mtn", methods=["GET", "POST"])
def paiement_mtn():
    if request.method == "POST":
        montant = request.form["montant"]
        if int(montant) < 500:
            return "Le montant doit être au moins 500 FCFA"
        # Ici: intégrer la logique MTN MoMo si nécessaire
        return f"Paiement MTN de {montant} FCFA reçu !"
    return render_template("paiement_mtn.html")


@app.route("/paiement/orange", methods=["GET", "POST"])
def paiement_orange():
    if request.method == "POST":
        montant = request.form["montant"]
        if int(montant) < 500:
            return "Le montant doit être au moins 500 FCFA"
        # Ici: intégrer la logique Orange Money si nécessaire
        return f"Paiement Orange de {montant} FCFA reçu !"
    return render_template("paiement_orange.html")

# Page modules
@app.route("/modules")
def modules():
    # Exemple simple: modules pour toutes les langues
    modules = [
         {"nom": "Compter de 1 à 100", "payant": False, "url": "/langues"},
        {"nom": "Quartiers et villages", "payant": False, "url": "/langues"},
        {"nom": "Chansons et proverbes", "payant": True, "url": "/langues"},
        {"nom": "Histoire et culture", "payant": True, "url": "/langues"},
         {"nom": "Compter de 1 à 100", "payant": False, "url": "/langues"},
        {"nom": "Quartiers et villages", "payant": False, "url": "/langues"},
        {"nom": "Chansons et proverbes", "payant": True, "url": "/langues"},
        {"nom": "Histoire et culture", "payant": True, "url": "/langues"},
         {"nom": "Compter de 1 à 100", "payant": False, "url": "/langues"},
        {"nom": "Quartiers et villages", "payant": False, "url": "/langues"},
        {"nom": "Chansons et proverbes", "payant": True, "url": "/langues"},
        {"nom": "Histoire et culture", "payant": True, "url": "/langues"},
    ]
    return render_template("modules.html", modules=modules)
# Paiement MTN pour module payant
@app.route("/paiement_mtn_module/<int:module_id>", methods=["GET","POST"])
def paiement_mtn_module(module_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    module = db.get_module_by_id(module_id)
    error = None
    if request.method == "POST":
        montant = int(request.form["montant"])
        if montant < 500:
            error = "Le montant minimal est de 500 FCFA."
        else:
            db.create_paiement(user_id, module_id, montant, statut="valide")
            return redirect(f"/module_detail/{module.langue}/{module.niveau}/{module.nom_module}")
    return render_template("paiement_mtn_module.html", module=module, error=error)

# Paiement Orange pour module payant
@app.route("/paiement_orange_module/<int:module_id>", methods=["GET","POST"])
def paiement_orange_module(module_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    module = db.get_module_by_id(module_id)
    error = None
    if request.method == "POST":
        montant = int(request.form["montant"])
        if montant < 500:
            error = "Le montant minimal est de 500 FCFA."
        else:
            db.create_paiement(user_id, module_id, montant, statut="valide")
            return redirect(f"/module_detail/{module.langue}/{module.niveau}/{module.nom_module}")
    return render_template("paiement_orange_module.html", module=module, error=error)

# Page module détaillée
@app.route("/module_detail/<langue>/<niveau>/<nom_module>")
def module_detail(langue, niveau, nom_module):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    module = db.get_module(langue, niveau, nom_module)
    if module.payant:
        paiement = db.get_paiement(user_id, module.id)
        if not paiement or paiement.statut != "valide":
            return redirect(f"/paiement_choix/{module.id}")  # page qui propose MTN ou Orange
    return render_template("module_detail.html", module=module)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render fournit le port
    app.run(host="0.0.0.0", port=port, debug=True)


