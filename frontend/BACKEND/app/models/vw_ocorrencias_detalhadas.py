from app import db

class VWOcorrenciasDetalhadas(db.Model):
    __tablename__ = 'vw_ocorrencias_detalhadas'

    id = db.Column(db.Integer, primary_key=True)
    data_hora_ocorrencia = db.Column(db.DateTime)
    status = db.Column(db.String)
    turno = db.Column(db.String)
    endereco_especifico = db.Column(db.String)
    tipo = db.Column(db.String)
    condominio = db.Column(db.String)
    registrado_por = db.Column(db.String)
    supervisor = db.Column(db.String) 