# Serviço para gerenciar rondas em tempo real conforme são registradas
from datetime import datetime, time, date, timezone
from typing import List, Dict, Optional, Tuple
from app.models.ronda_esporadica import RondaEsporadica
from app.models.condominio import Condominio
from app.models.user import User
from app import db
from app.services.ronda_utils import (
    identificar_plantao, 
    inferir_turno, 
    verificar_ronda_em_andamento,
    obter_condominio_por_id,
    obter_ronda_por_id
)
import json


class RondaTempoRealService:
    """
    Serviço para gerenciar rondas em tempo real.
    Permite registrar entrada/saída em múltiplos condomínios e gerar relatórios por plantão.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user = User.query.get(user_id)
        if not self.user:
            raise ValueError(f"Usuário {user_id} não encontrado")
    
    def iniciar_ronda(self, condominio_id: int, hora_entrada: time, observacoes: str = None) -> dict:
        """
        Inicia uma nova ronda e retorna um dicionário com os dados.
        """
        try:
            condominio = obter_condominio_por_id(condominio_id)
            if not condominio:
                raise ValueError(f"Condomínio {condominio_id} não encontrado")
            
            data_atual = date.today()
            if hora_entrada >= time(18, 0) or hora_entrada < time(6, 0):
                data_plantao = data_atual
            else:
                data_plantao = data_atual
            
            plantao = identificar_plantao(hora_entrada)
            turno = inferir_turno(plantao)
            
            ronda = RondaEsporadica(
                condominio_id=condominio_id,
                user_id=self.user_id,
                data_plantao=data_plantao,
                escala_plantao=plantao,
                turno=turno,
                hora_entrada=hora_entrada,
                status="em_andamento",
                observacoes=observacoes
            )
            
            db.session.add(ronda)
            db.session.flush()  # Envia a transação para o DB e obtém o ID
            import logging
            logging.warning(f'Ronda criada: id={ronda.id}, user_id={ronda.user_id}, condominio_id={ronda.condominio_id}, data_plantao={ronda.data_plantao}')

            # Captura os dados enquanto o objeto está 'vivo' na sessão
            ronda_data = {
                'id': ronda.id,
                'condominio_id': ronda.condominio_id,
                'condominio_nome': condominio.nome,
                'hora_entrada': ronda.hora_entrada_formatada,
                'status': ronda.status,
                'plantao': ronda.escala_plantao,
                'turno': ronda.turno,
                'data_plantao': ronda.data_plantao.strftime('%d/%m/%Y')
            }
            
            db.session.commit()  # Finaliza a transação
            return ronda_data
            
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"Erro ao iniciar ronda: {str(e)}", exc_info=True)
            raise e
    
    def finalizar_ronda(self, ronda_id: int, hora_saida: time, observacoes: str = None) -> dict:
        """
        Finaliza uma ronda em andamento e retorna um dicionário com os dados.
        """
        try:
            ronda = obter_ronda_por_id(ronda_id)
            if not ronda:
                raise ValueError(f"Ronda {ronda_id} não encontrada")
            
            if ronda.user_id != self.user_id:
                raise ValueError("Você só pode finalizar suas próprias rondas")
            
            if ronda.status != "em_andamento":
                raise ValueError("Só é possível finalizar rondas em andamento")
            
            ronda.finalizar_ronda(hora_saida, observacoes)
            condominio_nome = ronda.condominio.nome if ronda.condominio else f"Condomínio {ronda.condominio_id}"
            db.session.flush()

            ronda_data = {
                'id': ronda.id,
                'condominio_id': ronda.condominio_id,
                'condominio_nome': condominio_nome,
                'hora_entrada': ronda.hora_entrada_formatada,
                'hora_saida': ronda.hora_saida_formatada,
                'duracao_minutos': ronda.duracao_minutos,
                'duracao_formatada': ronda.duracao_formatada,
                'status': ronda.status,
                'plantao': ronda.escala_plantao,
                'turno': ronda.turno
            }
            
            db.session.commit()
            return ronda_data
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    def listar_rondas_em_andamento(self) -> List[RondaEsporadica]:
        """
        Lista todas as rondas em andamento do usuário.
        """
        return RondaEsporadica.query.filter_by(
            user_id=self.user_id,
            status="em_andamento"
        ).order_by(RondaEsporadica.data_criacao.desc()).all()
    
    def listar_rondas_por_plantao(self, data_plantao: date = None) -> Dict[Tuple, List[RondaEsporadica]]:
        """
        Lista todas as rondas finalizadas agrupadas por (condominio, data_plantao, plantao).
        """
        query = RondaEsporadica.query.filter_by(
            user_id=self.user_id,
            status="finalizada"
        )
        
        if data_plantao:
            query = query.filter_by(data_plantao=data_plantao)
        
        rondas = query.order_by(
            RondaEsporadica.condominio_id,
            RondaEsporadica.data_plantao,
            RondaEsporadica.hora_entrada
        ).all()
        
        # Agrupar por condomínio e plantão
        grupos = {}
        for ronda in rondas:
            plantao = identificar_plantao(ronda.hora_entrada)
            chave = (ronda.condominio_id, ronda.data_plantao, plantao)
            if chave not in grupos:
                grupos[chave] = []
            grupos[chave].append(ronda)
        
        return grupos
    
    def gerar_relatorio_plantao(self, data_plantao: date = None) -> List[str]:
        """
        Gera relatório formatado de todas as rondas do plantão.
        Retorna lista de strings, uma para cada condomínio.
        """
        grupos = self.listar_rondas_por_plantao(data_plantao)
        relatorios = []
        
        for (condominio_id, data_plantao, plantao), rondas in grupos.items():
            condominio = Condominio.query.get(condominio_id)
            nome_condominio = condominio.nome if condominio else f"Condomínio {condominio_id}"
            
            relatorio = self._formatar_relatorio_condominio(
                rondas, nome_condominio, data_plantao, plantao
            )
            relatorios.append(relatorio)
        
        return relatorios
    
    def _formatar_relatorio_condominio(self, rondas: List[RondaEsporadica], 
                                     nome_condominio: str, data_plantao: date, 
                                     plantao: str) -> str:
        """
        Formata relatório de um condomínio específico conforme modelo solicitado.
        """
        # Ordenar rondas por hora de entrada
        rondas_ordenadas = sorted(rondas, key=lambda x: x.hora_entrada)
        
        linhas = [
            f"Plantão {data_plantao.strftime('%d/%m/%Y')} ({plantao}h)",
            f"Residencial: {nome_condominio}",
            ""
        ]
        
        total_rondas = 0
        for ronda in rondas_ordenadas:
            if ronda.hora_entrada and ronda.hora_saida:
                # Calcular duração em minutos
                duracao_minutos = ronda.duracao_minutos or ronda.calcular_duracao()
                
                linhas.append(
                    f"\tInício: {ronda.hora_entrada.strftime('%H:%M')}  – "
                    f"Término: {ronda.hora_saida.strftime('%H:%M')} ({duracao_minutos} min)"
                )
                total_rondas += 1
        
        linhas.append("")
        linhas.append(f"✅ Total: {total_rondas} rondas completas no plantão")
        
        return "\n".join(linhas)
    
    def obter_estatisticas_plantao(self, data_plantao: date = None) -> Dict:
        """
        Retorna estatísticas do plantão atual.
        """
        grupos = self.listar_rondas_por_plantao(data_plantao)
        
        total_condominios = len(grupos)
        total_rondas = sum(len(rondas) for rondas in grupos.values())
        
        # Calcular tempo total
        tempo_total_minutos = 0
        for rondas in grupos.values():
            for ronda in rondas:
                duracao = ronda.duracao_minutos or ronda.calcular_duracao()
                if isinstance(duracao, (int, float)):
                    tempo_total_minutos += duracao
        
        return {
            "total_condominios": total_condominios,
            "total_rondas": total_rondas,
            "tempo_total_minutos": tempo_total_minutos,
            "tempo_total_formatado": f"{tempo_total_minutos // 60}h {tempo_total_minutos % 60}min"
        }
    
    def cancelar_ronda(self, ronda_id: int) -> bool:
        """
        Cancela uma ronda em andamento.
        """
        ronda = obter_ronda_por_id(ronda_id)
        if not ronda:
            return False
        
        if ronda.user_id != self.user_id:
            return False
        
        if ronda.status != "em_andamento":
            return False
        
        ronda.status = "cancelada"
        db.session.commit()
        return True
    
    def obter_condominios_disponiveis(self) -> List[Condominio]:
        """
        Retorna lista de condomínios disponíveis para registro de rondas.
        """
        return Condominio.query.order_by(Condominio.nome).all() 

    def condominios_com_ronda_em_andamento(self):
        from app.models.condominio import Condominio
        rondas = RondaEsporadica.query.filter_by(
            user_id=self.user_id,
            status='em_andamento'
        ).all()
        ids = {r.condominio_id for r in rondas}
        return [
            {'id': c.id, 'nome': c.nome}
            for c in Condominio.query.filter(Condominio.id.in_(ids)).all()
        ]

    def condominios_com_ronda_realizada_plantao(self):
        from app.models.condominio import Condominio
        from datetime import date
        hoje = date.today()
        rondas = RondaEsporadica.query.filter(
            RondaEsporadica.user_id == self.user_id,
            RondaEsporadica.data_plantao == hoje,
            RondaEsporadica.status.in_(['em_andamento', 'finalizada'])
        ).all()
        ids = {r.condominio_id for r in rondas}
        return [
            {'id': c.id, 'nome': c.nome}
            for c in Condominio.query.filter(Condominio.id.in_(ids)).all()
        ] 

    def listar_rondas_do_condominio_plantao(self, condominio_id):
        from app.models.condominio import Condominio
        from datetime import date
        hoje = date.today()
        condominio = Condominio.query.get(condominio_id)
        # Descobre o plantão atual do usuário para este condomínio (data_plantao e escala_plantao)
        ronda = RondaEsporadica.query.filter_by(
            user_id=self.user_id,
            condominio_id=condominio_id
        ).order_by(RondaEsporadica.data_plantao.desc(), RondaEsporadica.hora_entrada.desc()).first()
        if not ronda:
            return {
                'condominio_nome': condominio.nome if condominio else '',
                'data_plantao': '',
                'escala_plantao': '',
                'rondas': [],
                'total_completas': 0
            }
        data_plantao = ronda.data_plantao
        escala_plantao = ronda.escala_plantao
        rondas = RondaEsporadica.query.filter_by(
            user_id=self.user_id,
            condominio_id=condominio_id,
            data_plantao=data_plantao,
            escala_plantao=escala_plantao
        ).order_by(RondaEsporadica.hora_entrada.asc()).all()
        lista = [
            {
                'id': r.id,
                'hora_entrada': r.hora_entrada_formatada,
                'hora_saida': r.hora_saida_formatada,
                'status': r.status,
                'duracao': r.duracao_formatada,
                'duracao_minutos': r.duracao_minutos,
                'observacoes': r.observacoes or '',
            }
            for r in rondas
        ]
        total_completas = sum(1 for r in rondas if r.hora_saida)
        return {
            'condominio_nome': condominio.nome if condominio else '',
            'data_plantao': data_plantao.strftime('%d/%m/%Y') if data_plantao else '',
            'escala_plantao': escala_plantao or '',
            'rondas': lista,
            'total_completas': total_completas
        } 

    def plantao_anterior_pendente_exportacao(self):
        from app.models.condominio import Condominio
        from sqlalchemy import and_
        # Busca todos os plantões do usuário, ordenados do mais recente para o mais antigo
        plantao_rondas = (
            RondaEsporadica.query
            .filter(RondaEsporadica.user_id == self.user_id)
            .filter(RondaEsporadica.status == 'finalizada')
            .order_by(RondaEsporadica.data_plantao.desc(), RondaEsporadica.escala_plantao.desc())
            .all()
        )
        if not plantao_rondas:
            return None
        # Agrupa por (data_plantao, escala_plantao)
        plantoes = {}
        for r in plantao_rondas:
            key = (r.data_plantao, r.escala_plantao)
            if key not in plantoes:
                plantoes[key] = []
            plantoes[key].append(r)
        # Ordena os plantões por data/escala (mais recente primeiro)
        plantao_keys = sorted(plantoes.keys(), reverse=True)
        if len(plantao_keys) < 2:
            return None  # Não há plantão anterior
        # O plantão anterior é o segundo mais recente
        data_plantao, escala_plantao = plantao_keys[1]
        rondas = plantoes[(data_plantao, escala_plantao)]
        # Agrupa por condomínio
        condominios = {}
        for r in rondas:
            if r.condominio_id not in condominios:
                cond = Condominio.query.get(r.condominio_id)
                condominios[r.condominio_id] = {
                    'id': r.condominio_id,
                    'nome': cond.nome if cond else f'Condomínio {r.condominio_id}',
                    'rondas': []
                }
            condominios[r.condominio_id]['rondas'].append({
                'id': r.id,
                'hora_entrada': r.hora_entrada_formatada,
                'hora_saida': r.hora_saida_formatada,
                'duracao': r.duracao_formatada,
                'observacoes': r.observacoes or '',
            })
        return {
            'data_plantao': data_plantao.strftime('%d/%m/%Y'),
            'escala_plantao': escala_plantao,
            'condominios': list(condominios.values())
        } 

    def marcar_plantao_anterior_como_exportado(self):
        # Busca o plantão anterior pendente
        info = self.plantao_anterior_pendente_exportacao()
        if not info or not info.get('data_plantao') or not info.get('escala_plantao'):
            return False
        data_plantao = info['data_plantao']
        escala_plantao = info['escala_plantao']
        # Marca todas as rondas desse plantão como exportadas
        rondas = RondaEsporadica.query.filter_by(
            user_id=self.user_id,
            data_plantao=data_plantao,
            escala_plantao=escala_plantao,
            status='finalizada',
            exportado=False
        ).all()
        if not rondas:
            return False
        for r in rondas:
            r.exportado = True
        db.session.commit()
        return True 