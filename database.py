import sqlite3
from datetime import datetime
class Database:
    def __init__(self, db_file="score.db"):
        self.db_file = db_file
        self.creer_table()

    def connect(self):
        return sqlite3.connect(self.db_file)

    def creer_table(self):
        conn = self.connect()
        cur = conn.cursor()
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
        CREATE TABLE IF NOT EXISTS users(
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           nom TEXT,
           prenom TEXT,
           email TEXT UNIQUE,
           telephone TEXT,
           password TEXT
        )
        """)

        conn.commit()
        conn.close()

    def ajouter_score(self, nom, numero, langue, niveau, score, total):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO scores VALUES(NULL,?,?,?,?,?,?,?)
        """, (
            nom, numero, langue, niveau,
            score, total,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
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
      cur.execute("""
      INSERT INTO users VALUES(NULL,?,?,?,?,?)
      """, (nom, prenom, email, telephone, password))
      conn.commit()
      conn.close()


    def get_user_by_email(self, email):
      conn = self.connect()
      cur = conn.cursor()
      cur.execute("SELECT * FROM users WHERE email=?", (email,))
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


