# tests/test_auth.py
from flask import url_for, get_flashed_messages
from app.models import User #

def test_register_page_loads(client):
    """Testa se a página de registro carrega corretamente."""
    response = client.get(url_for('auth.register')) #
    assert response.status_code == 200
    assert b"Criar Nova Conta" in response.data #

def test_successful_registration(client, db):
    """Testa o registro bem-sucedido de um usuário."""
    response = client.post(url_for('auth.register'), data={ #
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    # "Conta criada com sucesso. Aguarde aprovação do administrador."
    assert b"Conta criada com sucesso. Aguarde aprova\xc3\xa7\xc3\xa3o do administrador." in response.data #
    user = User.query.filter_by(email='new@example.com').first() #
    assert user is not None
    assert user.username == 'newuser' #
    assert not user.is_approved # O padrão é False

def test_registration_existing_email(client, test_user):
    """Testa o registro com um e-mail existente."""
    response = client.post(url_for('auth.register'), data={ #
        'username': 'anotheruser',
        'email': test_user.email, # E-mail existente
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    # "Este e-mail já está registrado."
    assert b"Este e-mail j\xc3\xa1 est\xc3\xa1 registrado." in response.data #

def test_login_page_loads(client):
    """Testa se a página de login carrega corretamente."""
    response = client.get(url_for('auth.login')) #
    assert response.status_code == 200
    assert b"Acessar Conta" in response.data #

def test_successful_login(client, test_user, db): # Adicionado db para modificar test_user
    """Testa o login bem-sucedido para um usuário aprovado."""
    # Garante que o usuário está aprovado para este teste
    test_user.is_approved = True #
    db.session.commit()
    
    response = client.post(url_for('auth.login'), data={ #
        'email': test_user.email, #
        'password': 'password' # Senha correta para test_user
    }, follow_redirects=True)
    assert response.status_code == 200
    assert f"Bem-vindo, {test_user.username}!".encode('utf-8') in response.data #
    
    # Verifica se o usuário está realmente logado acessando uma rota protegida
    index_response = client.get(url_for('main.index')) #
    assert index_response.status_code == 200 

def test_login_unapproved_user(client, db):
    """Testa a tentativa de login por um usuário não aprovado."""
    unapproved_user = User(username='unapproved', email='unapproved@example.com', is_approved=False) #
    unapproved_user.set_password('password') #
    db.session.add(unapproved_user)
    db.session.commit()

    response = client.post(url_for('auth.login'), data={ #
        'email': unapproved_user.email,
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    # "Conta ainda não aprovada."
    assert b"Conta ainda n\xc3\xa3o aprovada." in response.data #

def test_login_invalid_credentials(client, test_user):
    """Testa o login com credenciais inválidas."""
    response = client.post(url_for('auth.login'), data={ #
        'email': test_user.email, #
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    # "Login falhou. Verifique email e senha."
    assert b"Login falhou. Verifique email e senha." in response.data #

def test_logout(auth_client): # auth_client já está logado
    """Testa o logout bem-sucedido."""
    response = auth_client.get(url_for('auth.logout'), follow_redirects=True) #
    assert response.status_code == 200
    # "Logout realizado com sucesso."
    assert b"Logout realizado com sucesso." in response.data #
    
    # Verifica se o usuário foi deslogado tentando acessar uma rota protegida
    # Deve redirecionar para o login
    index_response = auth_client.get(url_for('main.index'), follow_redirects=False) #
    assert index_response.status_code == 302 # Redirecionamento
    assert url_for('auth.login') in index_response.location #

def test_login_register_when_authenticated(auth_client):
    """Testa se usuários autenticados são redirecionados das páginas de login/registro."""
    login_page_response = auth_client.get(url_for('auth.login'), follow_redirects=False) #
    assert login_page_response.status_code == 302
    assert url_for('main.index') in login_page_response.location #

    register_page_response = auth_client.get(url_for('auth.register'), follow_redirects=False) #
    assert register_page_response.status_code == 302
    assert url_for('main.index') in register_page_response.location #