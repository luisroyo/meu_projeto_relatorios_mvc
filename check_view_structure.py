from app import create_app, db
from sqlalchemy import text

app = create_app()
app.app_context().push()

# Verificar estrutura da view vw_logradouros
result = db.session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'vw_logradouros' ORDER BY ordinal_position"))
columns = result.fetchall()

print("Estrutura da view vw_logradouros:")
for column in columns:
    print(f"- {column[0]}: {column[1]}")

# Verificar alguns dados
print("\nPrimeiros 3 registros:")
result = db.session.execute(text("SELECT * FROM vw_logradouros LIMIT 3"))
rows = result.fetchall()
for row in rows:
    print(row) 