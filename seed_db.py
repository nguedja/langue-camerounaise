import sys
sys.path.insert(0, '.')
from database import Database
from dictionnaire import structure, traductions

db = Database()
db.initialiser_langues()
db.initialiser_categories()

print("Seeding de la base de donnees...")

# Build a mapping: mot_francais -> categories
mot_categorie = {}
for niveau, cats in structure.items():
    for cat_name, mots in cats.items():
        for mot in mots:
            mot_categorie[mot] = cat_name

# Insert words
nb_inserted = 0
for niveau, cats in structure.items():
    for cat_name, mots in cats.items():
        cat = db.get_categorie_by_nom(cat_name)
        if not cat:
            print(f"  Categorie non trouvee: {cat_name}")
            continue
        cat_id = cat[0]
        for idx, mot in enumerate(mots):
            db.ajouter_mot_francais(mot, cat_id, niveau, idx + 1)
            nb_inserted += 1

print(f"  {nb_inserted} mots inseres")

# Insert translations
nb_trans = 0
conn = db.connect()
cur = conn.cursor()

# Get all mots
cur.execute("SELECT id, mot FROM mots_francais")
all_mots = cur.fetchall()

# Get all langues
cur.execute("SELECT id, nom FROM langues")
all_langues = cur.fetchall()
langue_map = {l[1].lower(): l[0] for l in all_langues}

for mot_id, mot in all_mots:
    mot_lower = mot.lower().replace("'", "'").replace("e", "e")
    # Try to find in traductions
    found = False
    for key in traductions:
        if key.lower() == mot_lower or mot_lower in key.lower():
            for langue_name, traduction in traductions[key].items():
                if langue_name in langue_map:
                    langue_id = langue_map[langue_name]
                    cur.execute(
                        "INSERT INTO traductions(mot_id, langue_id, traduction_texte, user_id, statut, date) VALUES(?,?,'system',0,'validee','2024-01-01')",
                        (mot_id, langue_id)
                    )
                    nb_trans += 1
            found = True
            break

conn.commit()
conn.close()

print(f"  {nb_trans} traductions inserées")
print("Seeding termine !")
