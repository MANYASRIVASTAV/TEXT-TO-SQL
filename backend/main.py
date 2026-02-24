import os
import json
import sqlite3
import re

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


# ================== APP CONFIG ==================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "db/user_dbs"
SCHEMA_FILE = "schemas.json"

os.makedirs(BASE_DIR, exist_ok=True)


# ================== MODELS ==================

class CreateDB(BaseModel):
    name: str
    tables: dict


class AskQuery(BaseModel):
    db_name: str
    question: str


# ================== SCHEMA ==================

def save_schema(db, schema):

    if os.path.exists(SCHEMA_FILE):
        with open(SCHEMA_FILE) as f:
            data = json.load(f)
    else:
        data = {}

    data[db] = schema

    with open(SCHEMA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_schema(db):

    if not os.path.exists(SCHEMA_FILE):
        return None


    with open(SCHEMA_FILE) as f:
        data = json.load(f)

    return data.get(db)


# ================== DATABASE ==================

def create_database(name, tables):

    path = f"{BASE_DIR}/{name}.db"

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    for table, cols in tables.items():

        col_str = ", ".join(cols)

        sql = f"CREATE TABLE IF NOT EXISTS {table} ({col_str})"

        cur.execute(sql)

    conn.commit()
    conn.close()


def run_sql(db, sql):

    path = f"{BASE_DIR}/{db}.db"

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    try:

        cur.execute(sql)

        if sql.lower().startswith("select"):

            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]

        else:
            conn.commit()
            rows = []
            cols = []

        conn.close()

        return cols, rows

    except Exception as e:

        conn.close()

        return None, str(e)


# ================== HELPERS ==================

def find_table(schema, question):

    q = question.lower()

    for table in schema.keys():

        if table.lower() in q:
            return table

    return None


# ================== TEXT TO SQL ==================

def ai_sql(db, question):

    q = question.lower().strip()

    schema = get_schema(db)

    if not schema:
        return "SELECT 'Database not found'"

    table = find_table(schema, q)

    if not table:
        return "SELECT 'Please mention table name in question'"



    # ---------- INSERT ----------

    if q.startswith("add") or q.startswith("insert"):

        cols = schema[table]

        col_names = [c.split()[0] for c in cols]

        parts = q.split()[1:]   # remove add

        # Remove table name
        if parts[0] == table.lower():
            parts = parts[1:]


        if len(parts) != len(col_names):

            return f"SELECT 'Expected {len(col_names)} values: {', '.join(col_names)}'"


        values = []

        for v in parts:

            if v.replace(".", "").isdigit():
                values.append(v)
            else:
                values.append(f"'{v}'")


        col_str = ", ".join(col_names)
        val_str = ", ".join(values)


        return f"INSERT INTO {table} ({col_str}) VALUES ({val_str})"



    # ---------- SELECT ----------

    # ---------- SELECT ----------

    if any(w in q for w in ["show", "list", "display", "find"]):

        words = q.split()

        # try to find department name
        dept = None

        for w in words:
            if w in ["it", "hr", "cs", "finance", "sales"]:
                dept = w
                break

        # if department found
        if dept:
            return f"SELECT * FROM {table} WHERE LOWER(dept) = '{dept}'"

        return f"SELECT * FROM {table}"


    # ---------- COUNT ----------

    if "count" in q:

        return f"SELECT COUNT(*) FROM {table}"



    # ---------- DELETE ----------

    if "delete" in q or "remove" in q:

        return f"DELETE FROM {table}"



    # ---------- DEFAULT ----------

    return f"SELECT * FROM {table}"



# ================== API ==================

@app.get("/")
def home():
    return {"status": "Running 🚀"}



@app.post("/create-db")
def create_db(data: CreateDB):

    create_database(data.name, data.tables)

    save_schema(data.name, data.tables)

    return {"msg": "Database created successfully"}



@app.post("/ask")
def ask(q: AskQuery):

    sql = ai_sql(q.db_name, q.question)

    cols, data = run_sql(q.db_name, sql)

    return {
        "sql": sql,
        "columns": cols,
        "data": data
    }