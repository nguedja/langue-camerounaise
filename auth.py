from flask import render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database

db = Database()

def register():
    if request.method == "POST":
        nom = request.form["nom"]
        prenom = request.form["prenom"]
        email = request.form["email"]
        telephone = request.form["telephone"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        if db.user_exists(email):
            return render_template("auth/register.html", error="Email déjà utilisé")

        db.create_user(nom, prenom, email, telephone, password_hash)
        return redirect("/login")

    return render_template("auth/register.html")


def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.get_user_by_email(email)

        if user and check_password_hash(user[5], password):
            session["user_id"] = user[0]
            session["user_nom"] = user[1]
            session["user_prenom"] = user[2]

            # ✅ Si on vient du mode admin (mot de passe spécial validé)
            if "admin" in session:
                return redirect("/admin")
            if "admin" not in session:# ✅ Sinon utilisateur normal
                return redirect("/accueil")

        return render_template("auth/login.html", error="Identifiants incorrects")

    return render_template("auth/login.html")

def logout():
    session.clear()
    return redirect("/login")
