import sqlite3

conn = sqlite3.connect("school.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS students(
 id INTEGER,
 name TEXT,
 marks INTEGER,
 class TEXT
)
""")

data = [
 (1,"Rahul",85,"10A"),
 (2,"Aman",72,"10B"),
 (3,"Neha",90,"10A"),
 (4,"Pooja",60,"10C"),
 (5,"Rohit",95,"10B")
]

c.executemany("INSERT OR IGNORE INTO students VALUES(?,?,?,?)", data)

conn.commit()
conn.close()