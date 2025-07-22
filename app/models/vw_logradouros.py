from app import db

class VWLogradouros(db.Model):
    __tablename__ = 'vw_logradouros'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String) 