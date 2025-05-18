from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.fields import DateField 
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User
import logging
from datetime import date, datetime, timezone # Adicionado datetime e timezone para compatibilidade, date para DateField

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

    def validate_username(self, username_field):
        user = User.query.filter_by(username=username_field.data).first()
        if user:
            logger.warning(f"Tentativa de registro com nome de usuário já existente: {username_field.data}")
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email_field):
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

class TestarRondasForm(FlaskForm): # Mantendo o nome da classe como TestarRondasForm por enquanto
    log_bruto_rondas = TextAreaField('Log Bruto das Rondas', 
                                     validators=[DataRequired(message="O log de rondas é obrigatório.")],
                                     render_kw={"rows": 10, "cols": 70})
    
    condominios_choices = [
        ('', '-- Selecione um Condomínio --'),
        ('VEVEY', 'VEVEY'), 
        ('AROSA', 'AROSA'), 
        ('ZERMATT', 'ZERMATT'), 
        ('DAVOS', 'DAVOS'),
        ('Outro', 'Outro (especificar abaixo)')
    ]
    nome_condominio = SelectField('Nome do Condomínio/Residencial', 
                                  choices=condominios_choices,
                                  validators=[DataRequired(message="Selecione um condomínio ou 'Outro'.")])
    
    nome_condominio_outro = StringField('Nome do Condomínio (se "Outro")',
                                        validators=[Optional()])

    data_plantao = DateField('Data do Plantão', 
                             format='%Y-%m-%d',
                             default=date.today,
                             validators=[DataRequired(message="Este campo é obrigatório.")])
    
    escala_choices = [
        ('', '-- Selecione a Escala --'),
        ('18:00 às 06:00', '18:00 às 06:00'),
        ('06:00 às 18:00', '06:00 às 18:00')
    ]
    escala_plantao = SelectField('Escala do Plantão', 
                                 choices=escala_choices,
                                 validators=[DataRequired(message="Selecione a escala do plantão.")])
    
    submit = SubmitField('Processar Relatório de Ronda')

    def validate_nome_condominio_outro(self, field):
        if self.nome_condominio.data == 'Outro' and not field.data:
            raise ValidationError('Por favor, especifique o nome do condomínio se "Outro" foi selecionado.')