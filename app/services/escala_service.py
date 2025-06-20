# app/services/escala_service.py
from app import db
from app.models import EscalaMensal

def get_escala_mensal(ano, mes):
    """
    Busca no banco de dados a escala para um ano e mês específicos.
    Retorna um dicionário com os turnos e os IDs dos supervisores.
    """
    escalas_salvas_raw = EscalaMensal.query.filter_by(ano=ano, mes=mes).all()
    return {escala.nome_turno: escala.supervisor_id for escala in escalas_salvas_raw}

def salvar_escala_mensal(ano, mes, dados_formulario):
    """
    Salva ou atualiza a escala de supervisores para um mês e ano.
    'dados_formulario' é um dicionário vindo do request.form.
    """
    turnos_definidos = ['Diurno Par', 'Diurno Impar', 'Noturno Par', 'Noturno Impar']
    
    try:
        for turno in turnos_definidos:
            form_field_name = f"supervisor_{turno.lower().replace(' ', '_')}"
            # Pega o ID do supervisor do formulário, default para None se não vier
            supervisor_id = dados_formulario.get(form_field_name)

            # Só processa se um supervisor foi selecionado
            if supervisor_id and supervisor_id != '0':
                supervisor_id = int(supervisor_id)
                # Procura por uma escala existente
                escala = EscalaMensal.query.filter_by(
                    ano=ano, mes=mes, nome_turno=turno
                ).first()
                
                # Se não existir, cria uma nova
                if not escala:
                    escala = EscalaMensal(ano=ano, mes=mes, nome_turno=turno)
                    db.session.add(escala)
                
                # Atribui o supervisor
                escala.supervisor_id = supervisor_id
            else:
                # Se 'Nenhum Supervisor' foi escolhido, remove a escala existente
                escala_existente = EscalaMensal.query.filter_by(ano=ano, mes=mes, nome_turno=turno).first()
                if escala_existente:
                    db.session.delete(escala_existente)
        
        db.session.commit()
        return True, f'Escala de supervisores para {mes}/{ano} atualizada com sucesso!'
    
    except Exception as e:
        db.session.rollback()
        return False, f'Erro ao salvar as alterações: {str(e)}'