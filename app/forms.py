from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField # Adicionado TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User # Para verificar se usuário/email já existem
import logging
from datetime import datetime, timezone # <<< LINHA ADICIONADA

logger = logging.getLogger(__name__)

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', 
                           validators=[DataRequired(message="Este campo é obrigatório."), 
                                       Length(min=4, max=25, message="Deve ter entre 4 e 25 caracteres.")])
    email = StringField('Email',
                        validators=[DataRequired(message="Este campo é obrigatório."), 
                                    Email(message="Endereço de email inválido.")])
    password = PasswordField('Senha', 
                             validators=[DataRequired(message="Este campo é obrigatório."), 
                                         Length(min=6, message="A senha deve ter pelo menos 6 caracteres.")])
    confirm_password = PasswordField('Confirmar Senha',
                                     validators=[DataRequired(message="Este campo é obrigatório."), 
                                                 EqualTo('password', message="As senhas não coincidem.")])
    submit = SubmitField('Registrar')

    # Validador customizado para verificar se o nome de usuário já existe
    def validate_username(self, username_field): # O argumento é o campo em si
        user = User.query.filter_by(username=username_field.data).first()
        if user:
            logger.warning(f"Tentativa de registro com nome de usuário já existente: {username_field.data}")
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    # Validador customizado para verificar se o email já existe
    def validate_email(self, email_field): # O argumento é o campo em si
        user = User.query.filter_by(email=email_field.data).first()
        if user:
            logger.warning(f"Tentativa de registro com email já existente: {email_field.data}")
            raise ValidationError('Este email já está registrado. Por favor, escolha outro.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(message="Este campo é obrigatório."), 
                                    Email(message="Endereço de email inválido.")])
    password = PasswordField('Senha', 
                             validators=[DataRequired(message="Este campo é obrigatório.")])
    remember = BooleanField('Lembrar-me') 
    submit = SubmitField('Login')

class TestarRondasForm(FlaskForm):
    log_bruto_rondas = TextAreaField('Log Bruto das Rondas', 
                                     validators=[DataRequired(message="O log de rondas é obrigatório.")],
                                     render_kw={"rows": 10, "cols": 70})
    nome_condominio = StringField('Nome do Condomínio', 
                                  validators=[DataRequired(message="Este campo é obrigatório.")],
                                  default='Condomínio Exemplo') # Valor padrão
    data_plantao = StringField('Data do Plantão (dd/mm/aaaa)', 
                               validators=[DataRequired(message="Este campo é obrigatório.")],
                               default=datetime.now(timezone.utc).strftime('%d/%m/%Y')) # Usa datetime importado
    escala_plantao = StringField('Escala do Plantão (Ex: 18-06)', 
                                 validators=[DataRequired(message="Este campo é obrigatório.")],
                                 default='18-06') # Valor padrão
    submit = SubmitField('Processar Log de Rondas')