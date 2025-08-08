from app import db

class VWColaboradores(db.Model):
    __tablename__ = 'vw_colaboradores'

    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String)
    cargo = db.Column(db.String)
    matricula = db.Column(db.String)
    data_admissao = db.Column(db.Date)
    status = db.Column(db.String)
    data_criacao = db.Column(db.DateTime)
    data_modificacao = db.Column(db.DateTime) 