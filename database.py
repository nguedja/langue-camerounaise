import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_file="score.db"):
        self.db_file = db_file
        self.creer_tables()

    def connect(self):
        return sqlite3.connect(self.db_file)

    def creer_tables(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            prenom TEXT,
            email TEXT UNIQUE,
            telephone TEXT,
            password TEXT,
            langue_origin TEXT DEFAULT NULL,
            role TEXT DEFAULT 'utilisateur',
            date_inscription TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            numero TEXT,
            langue TEXT,
            niveau TEXT,
            score INTEGER,
            total INTEGER,
            date TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS langues(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE,
            code TEXT,
            region TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS categories(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            icone TEXT DEFAULT '',
            ordre INTEGER DEFAULT 0
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS mots_francais(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot TEXT,
            categorie_id INTEGER,
            niveau TEXT,
            ordre INTEGER DEFAULT 0,
            FOREIGN KEY (categorie_id) REFERENCES categories(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS traductions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mot_id INTEGER,
            langue_id INTEGER,
            traduction_texte TEXT,
            audio_url TEXT DEFAULT NULL,
            user_id INTEGER,
            votes_positifs INTEGER DEFAULT 0,
            votes_negatifs INTEGER DEFAULT 0,
            statut TEXT DEFAULT 'en_attente',
            date TEXT,
            FOREIGN KEY (mot_id) REFERENCES mots_francais(id),
            FOREIGN KEY (langue_id) REFERENCES langues(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS evaluations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            langue_id INTEGER,
            niveau TEXT,
            score INTEGER,
            total INTEGER,
            pourcentage INTEGER,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (langue_id) REFERENCES langues(id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS progression(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            langue_id INTEGER,
            niveau_max TEXT DEFAULT 'debutant',
            mots_appris INTEGER DEFAULT 0,
            date_modification TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (langue_id) REFERENCES langues(id),
            UNIQUE(user_id, langue_id)
        )
        """)

        conn.commit()
        conn.close()

    def initialiser_langues(self):
        langues = [
            ("Bangante", "bang", "Ouest"),
            ("Bassa", "bas", "Littoral"),
            ("Bafan", "baf", "Ouest"),
            ("Bandjoun", "bdj", "Ouest"),
            ("Ewondo", "ewo", "Centre"),
            ("Douala", "dou", "Littoral"),
        ]
        conn = self.connect()
        cur = conn.cursor()
        for nom, code, region in langues:
            cur.execute(
                "INSERT OR IGNORE INTO langues(nom, code, region) VALUES(?,?,?)",
                (nom, code, region),
            )
        conn.commit()
        conn.close()

    def get_langues(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM langues ORDER BY nom")
        data = cur.fetchall()
        conn.close()
        return data

    def get_langue_by_id(self, lid):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM langues WHERE id=?", (lid,))
        data = cur.fetchone()
        conn.close()
        return data

    def get_langue_by_nom(self, nom):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM langues WHERE nom=?", (nom,))
        data = cur.fetchone()
        conn.close()
        return data

    def initialiser_categories(self):
        categories = [
            ("Salutations", "👋", 1),
            ("Famille", "👨‍👩‍👧‍👦", 2),
            ("Corps humain", "🧍", 3),
            ("Nourriture", "🍽️", 4),
            ("Nombres", "🔢", 5),
            ("Couleurs", "🎨", 6),
            ("Pronoms", "📝", 7),
            ("Verbes basiques", "🏃", 8),
            ("Animaux", "🐾", 9),
            ("Vêtements", "👕", 10),
            ("Maison", "🏠", 11),
            ("Nature", "🌿", 12),
            ("Ville", "🏙️", 13),
            ("Véhicules", "🚗", 14),
            ("Professions", "👨‍⚕️", 15),
            ("Actions", "✋", 16),
            ("Expressions courantes", "💬", 17),
            ("Temps", "⏰", 18),
            ("Émotions", "❤️", 19),
            ("Liens sociaux", "🤝", 20),
            ("Qualités", "⭐", 21),
            ("Nourriture avancée", "🌽", 22),
            ("Corps avancé", "🦴", 23),
            ("Verbes intermédiaires", "📚", 24),
            ("Proverbes", "📜", 25),
            ("Contes et expressions", "📖", 26),
            ("Chants et berceuses", "🎵", 27),
            ("Conversations", "🗣️", 28),
            ("Histoire et culture", "🏛️", 29),
            ("Santé", "🏥", 30),
            ("Agriculture", "🌾", 31),
        ]
        conn = self.connect()
        cur = conn.cursor()
        for nom, icone, ordre in categories:
            cur.execute(
                "INSERT OR IGNORE INTO categories(nom, icone, ordre) VALUES(?,?,?)",
                (nom, icone, ordre),
            )
        conn.commit()
        conn.close()

    def get_categories(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories ORDER BY ordre")
        data = cur.fetchall()
        conn.close()
        return data

    def get_categorie_by_nom(self, nom):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories WHERE nom=?", (nom,))
        data = cur.fetchone()
        conn.close()
        return data

    def ajouter_mot_francais(self, mot, categorie_id, niveau, ordre=0):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO mots_francais(mot, categorie_id, niveau, ordre) VALUES(?,?,?,?)",
            (mot, categorie_id, niveau, ordre),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid

    def get_mots_par_niveau(self, niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """SELECT m.id, m.mot, m.niveau, c.nom as categorie, c.icone
               FROM mots_francais m
               JOIN categories c ON m.categorie_id = c.id
               WHERE m.niveau = ?
               ORDER BY c.ordre, m.ordre""",
            (niveau,),
        )
        data = cur.fetchall()
        conn.close()
        return data

    def get_mots_par_categorie(self, categorie_id, niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM mots_francais WHERE categorie_id=? AND niveau=? ORDER BY ordre",
            (categorie_id, niveau),
        )
        data = cur.fetchall()
        conn.close()
        return data

    def get_mot_by_id(self, mot_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM mots_francais WHERE id=?", (mot_id,))
        data = cur.fetchone()
        conn.close()
        return data

    def get_nb_mots_par_niveau(self, niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mots_francais WHERE niveau=?", (niveau,))
        count = cur.fetchone()[0]
        conn.close()
        return count

    def ajouter_traduction(self, mot_id, langue_id, traduction_texte, user_id, audio_url=None):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO traductions(mot_id, langue_id, traduction_texte, audio_url, user_id, date)
               VALUES(?,?,?,?,?,?)""",
            (mot_id, langue_id, traduction_texte, audio_url, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid

    def get_traductions_par_mot(self, mot_id, langue_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """SELECT t.*, u.prenom, u.nom
               FROM traductions t
               JOIN users u ON t.user_id = u.id
               WHERE t.mot_id=? AND t.langue_id=? AND t.statut='validee'
               ORDER BY t.votes_positifs DESC""",
            (mot_id, langue_id),
        )
        data = cur.fetchall()
        conn.close()
        return data

    def get_meilleure_traduction(self, mot_id, langue_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """SELECT t.traduction_texte, t.audio_url
               FROM traductions t
               WHERE t.mot_id=? AND t.langue_id=? AND t.statut='validee'
               ORDER BY t.votes_positifs DESC LIMIT 1""",
            (mot_id, langue_id),
        )
        data = cur.fetchone()
        conn.close()
        return data

    def ajouter_traduction_directe(self, mot_id, langue_id, traduction_texte, user_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO traductions(mot_id, langue_id, traduction_texte, user_id, statut, date)
               VALUES(?,?,?,?, 'validee', ?)""",
            (mot_id, langue_id, traduction_texte, user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        return cur.lastrowid

    def voter_traduction(self, traduction_id, positif=True):
        conn = self.connect()
        cur = conn.cursor()
        if positif:
            cur.execute("UPDATE traductions SET votes_positifs = votes_positifs + 1 WHERE id=?", (traduction_id,))
        else:
            cur.execute("UPDATE traductions SET votes_negatifs = votes_negatifs + 1 WHERE id=?", (traduction_id,))
        conn.commit()
        conn.close()

    def sauvegarder_evaluation(self, user_id, langue_id, niveau, score, total):
        pourcentage = int((score / total) * 100) if total > 0 else 0
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO evaluations(user_id, langue_id, niveau, score, total, pourcentage, date)
               VALUES(?,?,?,?,?,?,?)""",
            (user_id, langue_id, niveau, score, total, pourcentage, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        return pourcentage

    def get_derniere_evaluation(self, user_id, langue_id, niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """SELECT * FROM evaluations
               WHERE user_id=? AND langue_id=? AND niveau=?
               ORDER BY id DESC LIMIT 1""",
            (user_id, langue_id, niveau),
        )
        data = cur.fetchone()
        conn.close()
        return data

    def mettre_a_jour_progression(self, user_id, langue_id, nouveau_niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO progression(user_id, langue_id, niveau_max, date_modification)
               VALUES(?,?,?,?)
               ON CONFLICT(user_id, langue_id)
               DO UPDATE SET niveau_max=?, date_modification=?""",
            (user_id, langue_id, nouveau_niveau, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             nouveau_niveau, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

    def get_progression(self, user_id, langue_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM progression WHERE user_id=? AND langue_id=?",
            (user_id, langue_id),
        )
        data = cur.fetchone()
        conn.close()
        return data

    def set_langue_origin(self, user_id, langue_origin):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("UPDATE users SET langue_origin=? WHERE id=?", (langue_origin, user_id))
        conn.commit()
        conn.close()

    def ajouter_score(self, nom, numero, langue, niveau, score, total):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scores VALUES(NULL,?,?,?,?,?,?,?)",
            (nom, numero, langue, niveau, score, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

    def recuperer_scores(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM scores ORDER BY id DESC LIMIT 20")
        data = cur.fetchall()
        conn.close()
        return data

    def user_exists(self, email):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email=?", (email,))
        exists = cur.fetchone() is not None
        conn.close()
        return exists

    def create_user(self, nom, prenom, email, telephone, password):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(nom, prenom, email, telephone, password, date_inscription) VALUES(?,?,?,?,?,?)",
            (nom, prenom, email, telephone, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()

    def get_user_by_email(self, email):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()
        return user

    def get_user_by_id(self, user_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
        user = cur.fetchone()
        conn.close()
        return user

    def get_all_users(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = cur.fetchall()
        conn.close()
        return users

    def delete_user(self, user_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()

    def get_mots_sans_traduction(self, langue_id, niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """SELECT m.id, m.mot, c.nom as categorie
               FROM mots_francais m
               JOIN categories c ON m.categorie_id = c.id
               WHERE m.niveau = ?
               AND m.id NOT IN (
                   SELECT t.mot_id FROM traductions t
                   WHERE t.langue_id = ? AND t.statut = 'validee'
               )
               ORDER BY c.ordre, m.ordre""",
            (niveau, langue_id),
        )
        data = cur.fetchall()
        conn.close()
        return data

    def get_mots_avec_traduction(self, langue_id, niveau):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """SELECT m.id, m.mot, t.traduction_texte, c.nom as categorie
               FROM mots_francais m
               JOIN traductions t ON m.id = t.mot_id
               JOIN categories c ON m.categorie_id = c.id
               WHERE t.langue_id = ? AND m.niveau = ? AND t.statut = 'validee'
               ORDER BY c.ordre, m.ordre""",
            (langue_id, niveau),
        )
        data = cur.fetchall()
        conn.close()
        return data

    def compter_traductions_par_langue(self, langue_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM traductions WHERE langue_id=? AND statut='validee'",
            (langue_id,),
        )
        count = cur.fetchone()[0]
        conn.close()
        return count

    def compter_mots_total(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM mots_francais")
        count = cur.fetchone()[0]
        conn.close()
        return count
