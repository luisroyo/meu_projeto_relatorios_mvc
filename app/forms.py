# app/forms.py

from flask_wtf import FlaskForm
from wtforms.validators import Optional # Importação correta
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# Se você tiver validações que precisam acessar o modelo User (ex: checar se email já existe),
# você precisará importá-lo. Ajuste o caminho se necessário.
# from .models import User # Se models.py está no mesmo nível (app/models.py)
# Ou, se for mais seguro para evitar importações circulares, passe a app ou db para uma função
# ou faça a query dentro da rota após a validação básica. Por ora, vamos supor que o User pode ser importado.
# Para evitar problemas de importação circular se 'User' não for estritamente necessário aqui para as validações
# que você está usando ativamente, você pode comentar o import e as funções validate_username/validate_email.
from app.models import Colaborador, User # Se você tiver validações que usam o modelo User

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', 
                           validators=[DataRequired(message="Este campo é obrigatório."), 
                                       Length(min=4, max=25, message="Nome de usuário deve ter entre 4 e 25 caracteres.")])
    email = StringField('Email', 
                        validators=[DataRequired(message="Este campo é obrigatório."), 
                                    Email(message="Endereço de e-mail inválido.")])
    password = PasswordField('Senha', 
                             validators=[DataRequired(message="Este campo é obrigatório."), 
                                         Length(min=6, message="Senha deve ter pelo menos 6 caracteres.")])
    confirm_password = PasswordField('Confirmar Senha', 
                                     validators=[DataRequired(message="Este campo é obrigatório."), 
                                                 EqualTo('password', message="As senhas devem ser iguais.")])
    submit = SubmitField('Registrar', render_kw={"class": "btn btn-primary w-100"})

    # Validações customizadas (exemplos, descomente e ajuste se User estiver importado e for usar)
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este e-mail já está registrado. Por favor, escolha outro ou faça login.')

class LoginForm(FlaskForm):
    email = StringField('Email', 
                        validators=[DataRequired(message="Este campo é obrigatório."), 
                                    Email(message="Endereço de e-mail inválido.")])
    password = PasswordField('Senha', validators=[DataRequired(message="Este campo é obrigatório.")])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Login', render_kw={"class": "btn btn-primary w-100"})

class TestarRondasForm(FlaskForm):
    # O campo 'nome_condominio' terá suas 'choices' populadas dinamicamente na rota.
    # A primeira tupla é (valor_interno, rótulo_exibido).
    nome_condominio = SelectField(
        'Nome do Condomínio', 
        choices=[],  # Será preenchido na rota. Pode iniciar com [('', '-- Selecione um Condomínio --')]
        validators=[DataRequired(message="Selecione um condomínio.")]
    )
    
    # Campo para digitar o nome do condomínio se "Outro" for selecionado
    nome_condominio_outro = StringField(
        'Se "Outro", qual o nome?',
        validators=[Length(max=150, message="Nome do condomínio pode ter no máximo 150 caracteres.")] # Validador opcional
    ) 
    
    data_plantao = DateField(
        'Data do Plantão', 
        format='%Y-%m-%d', # Formato que o DateField espera e como ele renderiza
        validators=[DataRequired(message="Insira a data do plantão.")]
    )
    
    escala_plantao = SelectField(
        'Escala do Plantão', 
        choices=[ # Você pode manter estas fixas ou torná-las dinâmicas também se necessário
            ('', '-- Selecione uma Escala --'),
            ('18h às 06h', '18h às 06h'),
            ('06h às 18h', '06h às 18h')
        ], 
        validators=[DataRequired(message="Selecione a escala.")]
    )
    
    log_bruto_rondas = TextAreaField(
        'Log Bruto das Rondas', 
        validators=[DataRequired(message="Insira o log bruto das rondas.")],
        render_kw={"rows": 10, "class": "form-control"}
    )
    
    submit = SubmitField('Processar Relatório de Ronda', render_kw={"class": "btn btn-primary"})

    # Validador customizado para o campo 'nome_condominio_outro'
    def validate_nome_condominio_outro(self, field):
        # Verifica se a opção "Outro" foi selecionada no campo 'nome_condominio'
        # E se este campo 'nome_condominio_outro' está vazio.
        if self.nome_condominio.data == 'Outro' and not field.data:
            raise ValidationError('Por favor, especifique o nome do condomínio se "Outro" foi selecionado.')
        # Adicionalmente, pode verificar se não é apenas espaços em branco
        if self.nome_condominio.data == 'Outro' and field.data and not field.data.strip():
            raise ValidationError('O nome do condomínio (Outro) não pode ser apenas espaços em branco.')
# NOVO FORMULÁRIO PARA CADASTRO DE COLABORADOR
class ColaboradorForm(FlaskForm):
    nome_completo = StringField(
        'Nome Completo',
        validators=[DataRequired(message="Nome completo é obrigatório."),
                    Length(min=3, max=150)]
    )
    cargo = StringField(
        'Cargo',
        validators=[DataRequired(message="Cargo é obrigatório."),
                    Length(min=2, max=100)]
    )
    matricula = StringField(
        'Matrícula (Opcional)',
        validators=[Optional(), Length(max=50)] # Opcional, mas se preenchido, tem um limite
    )
    data_admissao = DateField(
        'Data de Admissão (Opcional)',
        format='%Y-%m-%d',
        validators=[Optional()]
    )
    status = SelectField(
        'Status',
        choices=[
            ('Ativo', 'Ativo'),
            ('Inativo', 'Inativo'),
            ('Férias', 'Férias'),
            ('Licença', 'Licença')
            # Adicione outros status conforme necessário
        ],
        validators=[DataRequired(message="Status é obrigatório.")],
        default='Ativo'
    )
    submit = SubmitField('Salvar Colaborador', render_kw={"class": "btn btn-primary"})

    # Validação customizada para matrícula (se precisar ser única)
    def validate_matricula(self, matricula_field):
        if matricula_field.data: # Só valida se algo foi digitado
            colaborador_existente = Colaborador.query.filter_by(matricula=matricula_field.data).first()
            # Se estiver editando, precisa permitir que a matrícula seja a mesma do colaborador atual.
            # Isso requer passar o ID do colaborador para o formulário, o que complica um pouco para um form de criação.
            # Para um formulário simples de *criação*, a validação abaixo é suficiente.
            # Para edição, você ajustaria para: if colaborador_existente and colaborador_existente.id != self.id_do_colaborador_em_edicao.data:
            if colaborador_existente:
                raise ValidationError('Esta matrícula já está em uso. Por favor, verifique.')
# NOVO FORMULÁRIO PARA FORMATAR RELATÓRIO PARA E-MAIL
class FormatEmailReportForm(FlaskForm):
    raw_report = TextAreaField(
        'Relatório Bruto (Colar aqui o texto gerado pela IA)', 
        validators=[DataRequired(message="Por favor, cole o relatório bruto.")],
        render_kw={"rows": 15, "class": "form-control", "placeholder": "Cole o relatório bruto da IA aqui..."}
    )
    include_greeting = BooleanField(
        'Incluir Saudação Formal (Ex: "Prezados(as),")',
        default=True # Mantém o padrão que você definiu
    )
    custom_greeting = TextAreaField(
        'Saudação Personalizada (Opcional - sobrescreve a padrão se preenchido)',
        render_kw={"rows": 2, "class": "form-control form-control-sm", "placeholder": "Ex: Caros Colegas,"}
    )
    include_closing = BooleanField(
        'Incluir Despedida Padrão (Ex: "Atenciosamente, Sua Equipe")',
        default=True # Mantém o padrão
    )
    custom_closing = TextAreaField(
        'Despedida Personalizada (Opcional - sobrescreve a padrão se preenchido)',
        render_kw={"rows": 2, "class": "form-control form-control-sm", "placeholder": "Ex: Com os melhores cumprimentos,"}
    )
    submit = SubmitField('Formatar Relatório para E-mail', render_kw={"class": "btn btn-primary btn-lg"})
