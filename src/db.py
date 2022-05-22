from flask import current_app, g
import sqlite3
from passlib.hash import pbkdf2_sha256 as pw

class Table:
    def __init__(self, name):
        self.name = name
        self.columns_by_table = {
            "users":"(username, password)",
            "history" : "(user_id, data, time)",
        }

    def add_data(self, conn, data):
        if "password" in data.keys():
            data["password"] = pw.hash(data["password"])
        string_data = ""
        for key, value in data.items():
            string_data += f"'{value}', "
        string_data = string_data[:-2]
        c = conn.cursor()
        c.execute(f"INSERT INTO {self.name} {self.columns_by_table[self.name]} values ({string_data});")
        conn.commit()

    def value_unique(self, conn, col_name, val):
        c = conn.cursor()
        c.execute(f"SELECT {col_name} FROM {self.name}")
        vals = c.fetchall()
        for v in vals:
            if v[0] == val:
                return False
        return True

    def login_valid(self, conn, username, password):
        c = conn.cursor()
        c.execute(f"SELECT * FROM users WHERE username='{username}'")
        user = c.fetchall()
        print(user)
        if len(user) == 0:
            return False
        return pw.verify(password, user[0][1])

class Database:
    def __init__(self, name, app_path):
        self.path = f"{app_path}/data/{name}"
        self.tables = {
            "users" : Table("users"),
            "history" : Table("history"),
            "data" : Table("data")
        }
    
    def get_db(self):
        if 'db' not in g:
            g.db = sqlite3.connect(
            self.path,
            detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
        return g.db

    def close_db(self, e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def init_db(self):
        db = self.get_db()
        with current_app.open_resource('src/schema.sql') as f:
            db.executescript(f.read().decode('utf8'))

    def add_data(self, table_name, data):
        self.tables[table_name].add_data(self.get_db(), data)
    
    def value_unique(self, table_name, col_name, val):
        return self.tables[table_name].value_unique(self.get_db(), col_name, val)

    def login_valid(self, username, password):
        return self.tables["users"].login_valid(self.get_db(), username, password)
