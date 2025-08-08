from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField(
        "Nome de Usuário",
        validators=[
            DataRequired(message="Este campo é obrigatório."),
            Length(
                min=4,
                max=25,
                message="Nome de usuário deve ter entre 4 e 25 caracteres.",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Este campo é obrigatório."),
            Email(message="Endereço de e-mail inválido."),
        ],
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Este campo é obrigatório."),
            Length(min=6, message="Senha deve ter pelo menos 6 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar Senha",
        validators=[
            DataRequired(message="Este campo é obrigatório."),
            EqualTo("password", message="As senhas devem ser iguais."),
        ],
    )
    submit = SubmitField("Registrar", render_kw={"class": "btn btn-primary w-100"})

    def validate_username(self, username) -> None:
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email) -> None:
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este e-mail já está registrado. Por favor, escolha outro ou faça login.')

class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Este campo é obrigatório."),
            Email(message="Endereço de e-mail inválido."),
        ],
    )
    password = PasswordField(
        "Senha", validators=[DataRequired(message="Este campo é obrigatório.")]
    )
    remember = BooleanField("Lembrar-me")
    submit = SubmitField("Login", render_kw={"class": "btn btn-primary w-100"}) 