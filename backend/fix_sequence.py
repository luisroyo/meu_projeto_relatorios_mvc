from app import db, create_app
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Reseting 'ronda_id_seq'...")
    try:
        # Get Max ID
        result = db.session.execute(text("SELECT MAX(id) FROM ronda"))
        max_id = result.scalar() or 0
        print(f"Max ID found: {max_id}")
        
        # Reset Sequence
        # Note: In Postgres, sequence name is usually table_id_seq by default.
        # We need to act carefully.
        sql = text(f"SELECT setval('ronda_id_seq', {max_id + 1}, false)")
        db.session.execute(sql)
        db.session.commit()
        print(f"Sequence reset to {max_id + 1}. done.")
    except Exception as e:
        print(f"Error: {e}")
