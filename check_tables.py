from database import engine
from sqlalchemy import text

conn = engine.connect()
result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
tables = [row[0] for row in result.fetchall()]
print("Tablas disponibles:", tables)
conn.close()
