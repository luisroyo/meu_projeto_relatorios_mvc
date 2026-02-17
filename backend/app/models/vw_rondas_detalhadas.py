from app import db

class VWRondasDetalhadas(db.Model):
    """View para rondas com informações detalhadas."""
    __tablename__ = 'vw_rondas_detalhadas'

    # IDs principais
    id = db.Column(db.Integer, primary_key=True)
    condominio_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    supervisor_id = db.Column(db.Integer)
    
    # Informações do condomínio
    condominio_nome = db.Column(db.String)
    condominio_endereco = db.Column(db.String)
    
    # Informações do usuário
    user_nome = db.Column(db.String)
    user_email = db.Column(db.String)
    user_username = db.Column(db.String)
    
    # Informações do supervisor
    supervisor_nome = db.Column(db.String)
    supervisor_email = db.Column(db.String)
    supervisor_username = db.Column(db.String)
    
    # Dados da ronda
    data_hora_inicio = db.Column(db.DateTime)
    data_hora_fim = db.Column(db.DateTime)
    data_plantao_ronda = db.Column(db.Date)
    turno_ronda = db.Column(db.String)
    escala_plantao = db.Column(db.String)
    tipo = db.Column(db.String)
    
    # Métricas
    total_rondas_no_log = db.Column(db.Integer)
    duracao_total_rondas_minutos = db.Column(db.Integer)
    primeiro_evento_log_dt = db.Column(db.DateTime)
    ultimo_evento_log_dt = db.Column(db.DateTime)
    
    # Status e processamento
    relatorio_processado = db.Column(db.Text)
    log_ronda_bruto = db.Column(db.Text)
    
    # Campos calculados (se necessário)
    duracao_horas = db.Column(db.Float)  # duracao_total_rondas_minutos / 60
    status_ronda = db.Column(db.String)  # 'em_andamento', 'finalizada', 'cancelada'
    
    def __repr__(self):
        return f'<VWRondasDetalhadas {self.id} - {self.condominio_nome} - {self.data_plantao_ronda}>' 