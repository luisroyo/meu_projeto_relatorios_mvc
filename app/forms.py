from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField # BooleanField não estamos usando ainda, mas é comum
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User # Para verificar se usuário/email já existem
import logging

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
    remember = BooleanField('Lembrar-me') # Para funcionalidade "lembrar-me"
    submit = SubmitField('Login')