# tests/test_ocorrencia_routes.py (A VERSÃO DE OURO)
from flask import url_for
from app.models import Ocorrencia, Condominio, OcorrenciaTipo, User
from datetime import datetime, timezone

# Este teste já estava passando
def test_ocorrencia_historico_page_requires_login(client):
    response = client.get(url_for('ocorrencia.listar_ocorrencias'))
    assert response.status_code == 302

# --- TESTES CORRIGIDOS ---

def test_registrar_ocorrencia_sucesso(client, db, test_user): # Usamos client e test_user
    # Logamos o usuário DENTRO do teste
    client.post(url_for('auth.login'), data={'email': test_user.email, 'password': 'password'})

    condo = Condominio(nome="Residencial Teste")
    tipo = OcorrenciaTipo(nome="Vandalismo")
    db.session.add_all([condo, tipo])
    db.session.commit()

    response = client.post(url_for('ocorrencia.registrar_ocorrencia'), data={
        'condominio_id': condo.id,
        'data_hora_ocorrencia': '2025-07-11T22:00',
        'turno': 'Noturno',
        'relatorio_final': 'Relatório de teste via pytest.',
        'status': 'Registrada',
        'ocorrencia_tipo_id': tipo.id,
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Ocorrência registrada com sucesso!'.encode('utf-8') in response.data

def test_analisar_relatorio_classifica_corretamente(client, db, test_user):
    client.post(url_for('auth.login'), data={'email': test_user.email, 'password': 'password'})

    condo = Condominio(nome="Condomínio Vila das Flores")
    tipo = OcorrenciaTipo(nome="Furtos")
    db.session.add_all([condo, tipo])
    db.session.commit()

    texto_relatorio = "Aconteceu um furto no Condomínio Vila das Flores."
    response = client.post(url_for('ocorrencia.analisar_relatorio'), json={'texto_relatorio': texto_relatorio})
    
    # O login agora funciona, então o status deve ser 200
    assert response.status_code == 200
    assert response.get_json()['sucesso'] is True

def test_usuario_nao_pode_editar_ocorrencia_de_outro(client, db, test_user, admin_user):
    client.post(url_for('auth.login'), data={'email': test_user.email, 'password': 'password'})

    tipo_existente = OcorrenciaTipo(nome="Tipo Genérico")
    db.session.add(tipo_existente)
    db.session.commit()

    ocorrencia_admin = Ocorrencia(
        relatorio_final="Relatório do Admin",
        ocorrencia_tipo_id=tipo_existente.id,
        registrado_por_user_id=admin_user.id,
        data_hora_ocorrencia=datetime.now(timezone.utc)
    )
    db.session.add(ocorrencia_admin)
    db.session.commit()

    response = client.get(url_for('ocorrencia.editar_ocorrencia', ocorrencia_id=ocorrencia_admin.id), follow_redirects=True)
    assert response.status_code == 200
    assert 'Você não tem permissão para editar esta ocorrência.'.encode('utf-8') in response.data