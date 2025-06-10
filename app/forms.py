# app/forms.py

from flask_wtf import FlaskForm
from wtforms.validators import Optional
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import Colaborador, User

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
    nome_condominio = SelectField('Nome do Condomínio', choices=[], validators=[DataRequired(message="Selecione um condomínio.")])
    nome_condominio_outro = StringField('Se "Outro", qual o nome?', validators=[Length(max=150)])
    data_plantao = DateField('Data do Plantão', format='%Y-%m-%d', validators=[DataRequired(message="Insira a data do plantão.")])
    escala_plantao = SelectField(
        'Escala do Plantão',
        choices=[('', '-- Selecione uma Escala --'), ('18h às 06h', '18h às 06h'), ('06h às 18h', '06h às 18h')],
        validators=[DataRequired(message="Selecione a escala.")]
    )
    log_bruto_rondas = TextAreaField(
        'Log Bruto das Rondas',
        validators=[DataRequired(message="Insira o log bruto das rondas.")],
        render_kw={"rows": 10, "class": "form-control"}
    )
    submit = SubmitField('Processar Relatório de Ronda', render_kw={"class": "btn btn-primary"})

    def validate_nome_condominio_outro(self, field):
        if self.nome_condominio.data == 'Outro' and not field.data.strip():
            raise ValidationError('Por favor, especifique o nome do condomínio se "Outro" foi selecionado.')

class ColaboradorForm(FlaskForm):
    nome_completo = StringField('Nome Completo', validators=[DataRequired(message="Nome completo é obrigatório."), Length(min=3, max=150)])
    cargo = StringField('Cargo', validators=[DataRequired(message="Cargo é obrigatório."), Length(min=2, max=100)])
    matricula = StringField('Matrícula (Opcional)', validators=[Optional(), Length(max=50)])
    data_admissao = DateField('Data de Admissão (Opcional)', format='%Y-%m-%d', validators=[Optional()])
    status = SelectField(
        'Status',
        choices=[('Ativo', 'Ativo'), ('Inativo', 'Inativo'), ('Férias', 'Férias'), ('Licença', 'Licença')],
        validators=[DataRequired(message="Status é obrigatório.")],
        default='Ativo'
    )
    submit = SubmitField('Salvar Colaborador', render_kw={"class": "btn btn-primary"})

    def validate_matricula(self, matricula_field):
        if matricula_field.data:
            colaborador_existente = Colaborador.query.filter_by(matricula=matricula_field.data).first()
            if colaborador_existente:
                raise ValidationError('Esta matrícula já está em uso. Por favor, verifique.')

class FormatEmailReportForm(FlaskForm):
    raw_report = TextAreaField(
        'Relatório Bruto (Colar aqui o texto gerado pela IA)',
        validators=[DataRequired(message="Por favor, cole o relatório bruto.")],
        render_kw={"rows": 15, "class": "form-control", "placeholder": "Cole o relatório bruto da IA aqui..."}
    )
    include_greeting = BooleanField('Incluir Saudação Formal (Ex: "Prezados(as),")', default=True)
    custom_greeting = TextAreaField('Saudação Personalizada (Opcional)', render_kw={"rows": 2})
    include_closing = BooleanField('Incluir Despedida Padrão (Ex: "Atenciosamente, ...")', default=True)
    custom_closing = TextAreaField('Despedida Personalizada (Opcional)', render_kw={"rows": 2})
    submit = SubmitField('Formatar Relatório para E-mail', render_kw={"class": "btn btn-primary btn-lg"})