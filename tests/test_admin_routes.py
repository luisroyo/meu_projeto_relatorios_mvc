# tests/test_admin_routes.py
from flask import url_for, get_flashed_messages
from app.models import User, Colaborador
from app import db
from datetime import date

# (Outras fixtures são injetadas automaticamente pelo pytest a partir de conftest.py)

def test_admin_dashboard_unauthenticated(client):
    response = client.get(url_for('admin.dashboard'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('auth.login') in response.location

def test_admin_dashboard_non_admin(auth_client):
    response_redirect = auth_client.get(url_for('admin.dashboard'), follow_redirects=True)
    assert response_redirect.status_code == 200
    assert url_for('main.index') in response_redirect.request.path
    # **INSPECIONE E AJUSTE AQUI** (Falhou no último output) [cite: 70]
    # Mensagem flash original: "Acesso negado. Esta área é restrita a administradores."
    # print(response_redirect.data.decode('utf-8')) # Descomente para inspecionar
    # Verifique se a renderização HTML é "Acesso negado. Esta &aacute;rea &eacute; restrita a administradores."
    expected_message = "Acesso negado. Esta área é restrita a administradores.".encode("utf-8")
    # Se o HTML renderizar com entidades, use a linha abaixo e ajuste conforme o HTML real:
    # expected_message = "Acesso negado. Esta &aacute;rea &eacute; restrita a administradores.".encode("utf-8")
    assert expected_message in response_redirect.data

def test_admin_dashboard_as_admin(admin_auth_client):
    response = admin_auth_client.get(url_for('admin.dashboard'), follow_redirects=False)
    assert response.status_code == 302
    assert url_for('admin.admin_tools') in response.location

def test_admin_tools_page_loads_for_admin(admin_auth_client):
    response = admin_auth_client.get(url_for('admin.admin_tools'))
    assert response.status_code == 200
    assert b"Ferramentas Administrativas" in response.data

def test_manage_users_page_loads_for_admin(admin_auth_client, test_user):
    response = admin_auth_client.get(url_for('admin.manage_users'))
    assert response.status_code == 200
    assert "Gerenciar Usuários".encode('utf-8') in response.data
    assert test_user.username.encode('utf-8') in response.data

def test_approve_user(admin_auth_client, db, test_user):
    test_user.is_approved = False
    db.session.commit()
    response = admin_auth_client.post(url_for('admin.approve_user', user_id=test_user.id), follow_redirects=True)
    assert response.status_code == 200
    approved_user = db.session.get(User, test_user.id)
    assert approved_user.is_approved
    # Mensagem flash: f'Usuário {user.username} aprovado com sucesso.'
    expected_message = f'Usuário {test_user.username} aprovado com sucesso.'.encode('utf-8')
    # Considere entidades HTML se "Usuário" virar "Usu&aacute;rio":
    # expected_message = f'Usu&aacute;rio {test_user.username} aprovado com sucesso.'.encode('utf-8')
    assert expected_message in response.data

def test_revoke_user(admin_auth_client, db, test_user):
    test_user.is_approved = True
    db.session.commit()
    response = admin_auth_client.post(url_for('admin.revoke_user', user_id=test_user.id), follow_redirects=True)
    assert response.status_code == 200
    revoked_user = db.session.get(User, test_user.id)
    assert not revoked_user.is_approved
    # Mensagem flash: f'Aprovação de {user.username} foi revogada.'
    expected_message = f"Aprovação de {test_user.username} foi revogada.".encode('utf-8')
    # Considere entidades HTML para Aprova&ccedil;&atilde;o:
    # expected_message = f"Aprova&ccedil;&atilde;o de {test_user.username} foi revogada.".encode('utf-8')
    assert expected_message in response.data

def test_revoke_self_approval_fails_flash(client, admin_user, db):
    with client:
        client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
        response_post = client.post(url_for('admin.revoke_user', user_id=admin_user.id))
        assert response_post.status_code == 302
        flashed_messages = get_flashed_messages(with_categories=True)
        assert len(flashed_messages) > 0
        found_message = any(
            category == 'danger' and "Você não pode revogar sua própria aprovação." in message #
            for category, message in flashed_messages
        )
        assert found_message, f"Mensagem flash esperada não encontrada. Encontradas: {flashed_messages}"
        current_admin_user = db.session.get(User, admin_user.id)
        assert current_admin_user.is_approved

def test_toggle_admin_status(admin_auth_client, db, test_user):
    initial_admin_status = test_user.is_admin
    test_user.is_approved = True 
    db.session.commit()
    response = admin_auth_client.post(url_for('admin.toggle_admin', user_id=test_user.id), follow_redirects=True)
    assert response.status_code == 200
    updated_user = db.session.get(User, test_user.id)
    assert updated_user.is_admin is not initial_admin_status
    # print(response.data.decode('utf-8')) # Descomente para inspecionar
    if updated_user.is_admin:
        expected_message_promoted = f'Usuário {test_user.username} foi promovido a administrador com sucesso.'.encode('utf-8') #
        assert expected_message_promoted in response.data
        optional_message_approved_auto = f'Usuário {test_user.username} também foi aprovado automaticamente ao se tornar admin.'.encode('utf-8') #
        if optional_message_approved_auto not in response.data:
            print(f"[Aviso no teste] Mensagem de aprovação automática para '{test_user.username}' não encontrada (pode ser normal se já estava aprovado ou se a lógica mudou).")
        assert updated_user.is_approved
    else:
        expected_message_rebaixado = f'Usuário {test_user.username} foi rebaixado de administrador com sucesso.'.encode('utf-8') #
        assert expected_message_rebaixado in response.data

def test_toggle_self_admin_status_fails_flash(client, admin_user, db):
    with client:
        client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
        response_post = client.post(url_for('admin.toggle_admin', user_id=admin_user.id))
        assert response_post.status_code == 302
        flashed_messages = get_flashed_messages(with_categories=True)
        assert len(flashed_messages) > 0
        found_message = any(
            category == 'warning' and "Você não pode alterar seu próprio status de administrador." in message #
            for category, message in flashed_messages
        )
        assert found_message, f"Mensagem flash esperada não encontrada. Encontradas: {flashed_messages}"
        current_admin_user = db.session.get(User, admin_user.id)
        assert current_admin_user.is_admin

def test_delete_user(admin_auth_client, db, test_user):
    user_id_to_delete = test_user.id
    username_to_delete = test_user.username 
    response = admin_auth_client.post(url_for('admin.delete_user', user_id=user_id_to_delete), follow_redirects=True)
    assert response.status_code == 200
    deleted_user = db.session.get(User, user_id_to_delete)
    assert deleted_user is None
    # print(response.data.decode('utf-8')) # Descomente para inspecionar
    expected_message = f'Usuário {username_to_delete} deletado com sucesso.'.encode('utf-8') #
    assert expected_message in response.data

def test_delete_self_fails_flash(client, admin_user, db):
    with client:
        client.post(url_for('auth.login'), data={'email': admin_user.email, 'password': 'adminpass'}, follow_redirects=True)
        response_post = client.post(url_for('admin.delete_user', user_id=admin_user.id))
        assert response_post.status_code == 302
        flashed_messages = get_flashed_messages(with_categories=True)
        assert len(flashed_messages) > 0
        found_message = any(
            category == 'danger' and "Você não pode deletar sua própria conta." in message #
            for category, message in flashed_messages
        )
        assert found_message, f"Mensagem flash esperada não encontrada. Encontradas: {flashed_messages}"
        current_admin_user = db.session.get(User, admin_user.id)
        assert current_admin_user is not None

def test_api_processar_justificativa_invalid_payload(admin_auth_client):
    response = admin_auth_client.post(url_for('admin.api_processar_justificativa'), json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "Dados não fornecidos." in data['erro'] or "Dados inválidos" in data['erro'] #


# --- Testes para CRUD de Colaboradores ---

def test_listar_colaboradores_page_loads(admin_auth_client):
    response = admin_auth_client.get(url_for('admin.listar_colaboradores'))
    assert response.status_code == 200
    # print(response.data.decode('utf-8'))
    assert "Gerenciar Colaboradores".encode('utf-8') in response.data #

def test_listar_colaboradores_com_dados(admin_auth_client, test_colaborador):
    response = admin_auth_client.get(url_for('admin.listar_colaboradores'))
    assert response.status_code == 200
    assert test_colaborador.nome_completo.encode('utf-8') in response.data
    if test_colaborador.matricula:
        assert test_colaborador.matricula.encode('utf-8') in response.data

def test_listar_colaboradores_sem_dados(admin_auth_client, db):
    Colaborador.query.delete()
    db.session.commit()
    response = admin_auth_client.get(url_for('admin.listar_colaboradores'))
    assert response.status_code == 200
    # **INSPECIONE E AJUSTE AQUI** (Falhou no último output)
    # print(response.data.decode('utf-8'))
    # Mensagem do template: "Nenhum colaborador cadastrado ainda."
    assert "Nenhum colaborador cadastrado ainda.".encode('utf-8') in response.data

def test_adicionar_colaborador_get_page(admin_auth_client):
    response = admin_auth_client.get(url_for('admin.adicionar_colaborador'))
    assert response.status_code == 200
    # print(response.data.decode('utf-8'))
    # Título do template: "Adicionar Novo Colaborador"
    assert "Adicionar Novo Colaborador".encode('utf-8') in response.data

def test_adicionar_colaborador_post_success(admin_auth_client, db):
    dados_colaborador = {
        'nome_completo': "Maria Nova Testadora",
        'matricula': "67890",
        'cargo': "Supervisora de Testes",
        'status': "Ativo",
        'data_admissao': "2023-01-15",
    }
    count_before = Colaborador.query.count()
    response_post = admin_auth_client.post(url_for('admin.adicionar_colaborador'), data=dados_colaborador) 
    assert response_post.status_code == 302
    assert url_for('admin.listar_colaboradores') in response_post.location
    count_after = Colaborador.query.count()
    assert count_after == count_before + 1
    novo_colaborador = Colaborador.query.filter_by(matricula="67890").first()
    assert novo_colaborador is not None
    assert novo_colaborador.nome_completo == "Maria Nova Testadora"
    assert novo_colaborador.data_admissao == date(2023, 1, 15)
    response_redirected = admin_auth_client.get(response_post.location)
    assert response_redirected.status_code == 200
    # **INSPECIONE E AJUSTE AQUI** (Falhou no último output)
    # print(response_redirected.data.decode('utf-8'))
    # Mensagem flash: f'Colaborador "{novo_colaborador.nome_completo}" adicionado com sucesso!'
    expected_message = f'Colaborador "{novo_colaborador.nome_completo}" adicionado com sucesso!'.encode('utf-8')
    # Considere entidades HTML para aspas: f'Colaborador &quot;{novo_colaborador.nome_completo}&quot; adicionado com sucesso!'.encode('utf-8')
    assert expected_message in response_redirected.data

def test_adicionar_colaborador_post_dados_invalidos(admin_auth_client, db):
    dados_invalidos = {
        'nome_completo': "", 
        'matricula': "00000",
        'cargo': "Cargo Inválido",
        'status': "Ativo",
        'data_admissao': "2023-01-01",
    }
    count_before = Colaborador.query.count()
    response = admin_auth_client.post(url_for('admin.adicionar_colaborador'), data=dados_invalidos, follow_redirects=True)
    assert response.status_code == 200
    # **INSPECIONE E AJUSTE AQUI** (Falhou no último output)
    # print(response.data.decode('utf-8'))
    # Mensagem de erro do form: "Nome completo é obrigatório."
    expected_error_message = "Nome completo é obrigatório.".encode('utf-8')
    # Considere entidades HTML: "Nome completo &eacute; obrigat&oacute;rio.".encode('utf-8')
    assert expected_error_message in response.data 
    count_after = Colaborador.query.count()
    assert count_after == count_before

def test_adicionar_colaborador_post_matricula_duplicada(admin_auth_client, test_colaborador, db):
    dados_duplicados = {
        'nome_completo': "Outro Nome Teste",
        'matricula': test_colaborador.matricula, 
        'cargo': "Outro Cargo Teste",
        'status': "Ativo",
        'data_admissao': "2023-02-20",
    }
    count_before = Colaborador.query.count()
    response = admin_auth_client.post(url_for('admin.adicionar_colaborador'), data=dados_duplicados, follow_redirects=True)
    assert response.status_code == 200
    # **INSPECIONE E AJUSTE AQUI** (Falhou no último output)
    # print(response.data.decode('utf-8'))
    # Mensagem de erro do form: 'Esta matrícula já está em uso. Por favor, escolha outra.'
    expected_error_message = "Esta matrícula já está em uso. Por favor, escolha outra.".encode('utf-8')
    # Considere entidades HTML: "Esta matr&iacute;cula j&aacute; est&aacute; em uso. Por favor, escolha outra.".encode('utf-8')
    assert expected_error_message in response.data
    count_after = Colaborador.query.count()
    assert count_after == count_before