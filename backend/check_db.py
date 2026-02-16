import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_inner_dir = os.path.join(current_dir, 'backend')
sys.path.append(backend_inner_dir)
from app import create_app, db
from app.models import Ronda
import sys

try:
    app = create_app()
    with app.app_context():
        count_gt_0 = Ronda.query.filter(Ronda.total_rondas_no_log > 0).count()
        count_eq_0 = Ronda.query.filter((Ronda.total_rondas_no_log == 0) | (Ronda.total_rondas_no_log == None)).count()
        print(f"Rondas > 0: {count_gt_0}")
        print(f"Rondas == 0: {count_eq_0}")
        
        last = Ronda.query.order_by(Ronda.id.desc()).first()
        if last:
            print(f"Last Ronda ID: {last.id}, Total: {last.total_rondas_no_log}")
except Exception as e:
    print(f"Error: {e}")
