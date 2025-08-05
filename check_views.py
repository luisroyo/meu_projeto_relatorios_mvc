from app import create_app, db
from sqlalchemy import text

app = create_app()
app.app_context().push()

# Verificar views disponíveis
result = db.session.execute(text("SELECT table_name FROM information_schema.views WHERE table_schema = 'public'"))
views = [row[0] for row in result.fetchall()]

print("Views disponíveis:")
for view in views:
    print(f"- {view}")

# Verificar se as views específicas existem
views_necessarias = ['vw_logradouros', 'vw_colaboradores', 'vw_ocorrencias_detalhadas']

print("\nVerificando views necessárias:")
for view in views_necessarias:
    try:
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {view}"))
        count = result.fetchone()[0]
        print(f"✓ {view}: {count} registros")
    except Exception as e:
        print(f"✗ {view}: ERRO - {e}") 