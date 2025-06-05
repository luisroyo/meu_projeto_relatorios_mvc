# tests/test_forms.py
from app.forms import RegistrationForm, LoginForm, ColaboradorForm
from app.models import User # Importe o User para criar instâncias se necessário para mocks mais complexos
# Não precisa importar 'app' diretamente aqui se você usar as fixtures corretas

# Nota: A fixture 'db' já garante que app.app_context() está ativo e _db.create_all() foi chamado.

def test_registration_form_valid(app, db): # Adicione a fixture 'db'
    # O app.test_request_context é bom para quando o form precisa de um contexto de request
    # mas a inicialização do BD deve ser garantida pela fixture 'db' e 'app'
    with app.test_request_context('/register', method='POST'):
        form = RegistrationForm(data={
            'username': 'testuserform',
            'email': 'form@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        # Para testar a validação do formulário unitariamente, sem depender de um BD real,
        # é comum "simular" (mock) as chamadas ao banco de dados.
        # Se você quer testar a lógica do formulário *com* interação real (porém controlada) com o BD de teste,
        # então o BD precisa estar configurado.
        
        # Opção A: Teste de formulário mais puro (mockando a query)
        # com patch('app.forms.User.query') as mock_query:
        #     mock_query.filter_by.return_value.first.return_value = None # Simula usuário não existente
        #     assert form.validate() is True

        # Opção B: Teste que permite a query real no BD de teste (garantido pela fixture db)
        # Neste caso, as funções validate_username e validate_email vão rodar contra o BD de teste.
        # Certifique-se de que nenhum usuário com 'testuserform' ou 'form@example.com' existe antes de validar.
        assert form.validate() is True # Isso agora vai rodar as queries no BD de teste vazio.

def test_registration_form_missing_username(app, db): # Adicione 'db'
    with app.test_request_context('/register', method='POST'):
        form = RegistrationForm(data={
            'email': 'form@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        assert form.validate() is False
        assert 'username' in form.errors
        assert "Este campo é obrigatório." in form.errors['username']

def test_registration_form_password_mismatch(app, db): # Adicione 'db'
    with app.test_request_context('/register', method='POST'):
        form = RegistrationForm(data={
            'username': 'testuserform',
            'email': 'form@example.com',
            'password': 'password123',
            'confirm_password': 'password321'
        })
        assert form.validate() is False # As validações de username e email vão rodar
        assert 'confirm_password' in form.errors
        assert "As senhas devem ser iguais." in form.errors['confirm_password']

# ... outros testes de formulário ...
# Ajuste os testes de LoginForm e ColaboradorForm de forma similar, adicionando a fixture 'db'
# se eles fizerem consultas ao banco de dados durante a validação.

def test_login_form_valid(app, db): # Adicione 'db'
    with app.test_request_context('/login', method='POST'):
        form = LoginForm(data={'email': 'test@example.com', 'password': 'password'})
        assert form.validate() is True

def test_login_form_invalid_email(app, db): # Adicione 'db'
    with app.test_request_context('/login', method='POST'):
        form = LoginForm(data={'email': 'not-an-email', 'password': 'password'})
        assert form.validate() is False
        assert 'email' in form.errors
        assert "Endereço de e-mail inválido." in form.errors['email']

def test_colaborador_form_valid(app, db): # Adicione 'db'
     with app.test_request_context('/admin/colaboradores/novo', method='POST'):
        form = ColaboradorForm(data={
            'nome_completo': 'João da Silva',
            'cargo': 'Vigilante',
            'status': 'Ativo'
        })
        # Se validate_matricula faz query, o BD de teste precisa estar pronto.
        # Se a matrícula for única e você estiver testando a validação,
        # certifique-se de que não há um Colaborador com essa matrícula no BD de teste.
        assert form.validate() is True

def test_colaborador_form_missing_nome(app, db): # Adicione 'db'
    with app.test_request_context('/admin/colaboradores/novo', method='POST'):
        form = ColaboradorForm(data={
            'cargo': 'Vigilante',
            'status': 'Ativo'
        })
        assert form.validate() is False
        assert 'nome_completo' in form.errors
        assert "Nome completo é obrigatório." in form.errors['nome_completo']