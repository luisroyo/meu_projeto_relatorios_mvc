from app import db
from datetime import datetime, timezone, time, timedelta
from sqlalchemy import func
from typing import Optional

class RondaEsporadica(db.Model):
    """Modelo para rondas esporádicas realizadas via PWA."""
    __tablename__ = "ronda_esporadica"
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relacionamentos
    condominio_id = db.Column(db.Integer, db.ForeignKey("condominio.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    
    # Dados do plantão
    data_plantao = db.Column(db.Date, nullable=False, index=True)
    escala_plantao = db.Column(db.String(100), nullable=False)  # "06h às 18h" ou "18h às 06h"
    turno = db.Column(db.String(50), nullable=True)  # "Diurno", "Noturno"
    
    # Horários de entrada/saída
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_saida = db.Column(db.Time, nullable=True)
    
    # Observações e status
    observacoes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="em_andamento", index=True)  # em_andamento, finalizada, cancelada
    
    # Logs e relatórios
    log_bruto = db.Column(db.Text, nullable=True)
    relatorio_processado = db.Column(db.Text, nullable=True)
    
    # Métricas
    duracao_minutos = db.Column(db.Integer, default=0)
    total_rondas = db.Column(db.Integer, default=0)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    data_modificacao = db.Column(db.DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relacionamentos
    condominio = db.relationship("Condominio", backref="rondas_esporadicas")
    user = db.relationship("User", foreign_keys=[user_id], backref="rondas_esporadicas_criadas")
    supervisor = db.relationship("User", foreign_keys=[supervisor_id], backref="rondas_esporadicas_supervisionadas")
    
    exportado = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self) -> str:
        return f'<RondaEsporadica {self.id} - {self.condominio.nome if self.condominio else "N/A"} - {self.data_plantao}>'
    
    @property
    def duracao_formatada(self):
        """Retorna a duração formatada em horas e minutos."""
        if not self.duracao_minutos:
            return "0h 0min"
        
        horas = self.duracao_minutos // 60
        minutos = self.duracao_minutos % 60
        return f"{horas}h {minutos}min"
    
    @property
    def hora_entrada_formatada(self):
        """Retorna a hora de entrada formatada."""
        if self.hora_entrada:
            return self.hora_entrada.strftime("%H:%M")
        return "N/A"
    
    @property
    def hora_saida_formatada(self):
        """Retorna a hora de saída formatada."""
        if self.hora_saida:
            return self.hora_saida.strftime("%H:%M")
        return "N/A"
    
    def calcular_duracao(self):
        """Calcula a duração em minutos entre entrada e saída."""
        if not self.hora_entrada or not self.hora_saida:
            return 0
        
        # Converter para datetime para facilitar cálculo
        entrada = datetime.combine(self.data_plantao, self.hora_entrada)
        saida = datetime.combine(self.data_plantao, self.hora_saida)
        
        # Se a saída for menor que entrada, significa que passou da meia-noite
        if saida < entrada:
            saida = datetime.combine(self.data_plantao + timedelta(days=1), self.hora_saida)
        
        duracao = saida - entrada
        return int(duracao.total_seconds() / 60)
    
    def finalizar_ronda(self, hora_saida: time, observacoes: Optional[str] = None):
        """Finaliza a ronda com hora de saída e observações."""
        self.hora_saida = hora_saida
        self.status = "finalizada"
        if observacoes:
            self.observacoes = observacoes
        self.duracao_minutos = self.calcular_duracao()
        self.data_modificacao = datetime.now(timezone.utc)
    
    def adicionar_observacao(self, observacao: str):
        """Adiciona uma observação ao log da ronda."""
        if self.observacoes:
            self.observacoes += f"\n{observacao}"
        else:
            self.observacoes = observacao
        self.data_modificacao = datetime.now(timezone.utc) 