from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, DateTimeLocalField,
                     PasswordField, SelectField, SelectMultipleField,
                     StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Optional,
                                ValidationError)

from app.models import User


# Função helper para aceitar '' como None nos SelectField com coerce=int
def optional_int_coerce(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


# ====================================================================
# FORMULÁRIOS DE AUTENTICAÇÃO E USUÁRIO
# ====================================================================


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
        """Validate if the username is already taken."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

    def validate_email(self, email) -> None:
        """Validate if the email is already registered."""
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


# ====================================================================
# FORMULÁRIOS OPERACIONAIS (RONDAS, COLABORADORES, ETC.)
# ====================================================================


class TestarRondasForm(FlaskForm):
    """Formulário para testar e registrar rondas."""

    nome_condominio = SelectField(
        "Nome do Condomínio",
        choices=[],
        validators=[DataRequired(message="Selecione um condomínio.")],
    )
    nome_condominio_outro = StringField(
        'Se "Outro", qual o nome?', validators=[Optional(), Length(max=150)]
    )
    data_plantao = DateField(
        "Data do Plantão",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Insira a data do plantão.")],
    )
    escala_plantao = SelectField(
        "Escala do Plantão",
        choices=[
            ("06h às 18h", "06h às 18h (Diurno)"),
            ("18h às 06h", "18h às 06h (Noturno)")
        ],
        validators=[DataRequired(message="Selecione a escala.")],
    )
    supervisor_id = SelectField(
        "Supervisor da Ronda", coerce=int, validators=[Optional()]
    )
    log_bruto_rondas = TextAreaField(
        "Log Bruto das Rondas",
        validators=[DataRequired(message="Insira o log bruto das rondas.")],
        render_kw={"rows": 10, "class": "form-control"},
    )
    submit = SubmitField(
        "Processar Relatório de Ronda", render_kw={"class": "btn btn-primary"}
    )

    def validate_nome_condominio_outro(self, field) -> None:
        """Validate the alternative condominium name field."""
        if self.nome_condominio.data == 'Outro' and not field.data.strip():
            raise ValidationError('Por favor, especifique o nome do condomínio se "Outro" foi selecionado.')


class ColaboradorForm(FlaskForm):
    """Formulário para cadastro/edição de colaboradores."""

    nome_completo = StringField(
        "Nome Completo",
        validators=[
            DataRequired(message="Nome completo é obrigatório."),
            Length(min=3, max=150),
        ],
    )
    cargo = StringField(
        "Cargo",
        validators=[
            DataRequired(message="Cargo é obrigatório."),
            Length(min=2, max=100),
        ],
    )
    matricula = StringField("Matrícula", validators=[Optional(), Length(max=50)])
    data_admissao = DateField(
        "Data de Admissão", format="%Y-%m-%d", validators=[Optional()]
    )
    status = SelectField(
        "Status",
        choices=[('Ativo', 'Ativo'), ('Inativo', 'Inativo')],
        validators=[DataRequired(message="Status é obrigatório.")],
        default='Ativo',
    )
    submit = SubmitField("Salvar Colaborador", render_kw={"class": "btn btn-primary"})

    def validate_matricula(self, matricula_field) -> None:
        """Validate the collaborator's registration field."""
        if matricula_field.data:
            pass


class FormatEmailReportForm(FlaskForm):
    raw_report = TextAreaField(
        "Relatório Bruto (Colar aqui o texto gerado pela IA)",
        validators=[DataRequired(message="Por favor, cole o relatório bruto.")],
        render_kw={
            "rows": 15,
            "class": "form-control",
            "placeholder": "Cole o relatório bruto da IA aqui...",
        },
    )
    include_greeting = BooleanField("Incluir Saudação Formal", default=True)
    custom_greeting = TextAreaField(
        "Saudação Personalizada (Opcional)", render_kw={"rows": 2}
    )
    include_closing = BooleanField("Incluir Despedida Padrão", default=True)
    custom_closing = TextAreaField(
        "Despedida Personalizada (Opcional)", render_kw={"rows": 2}
    )
    submit = SubmitField(
        "Formatar Relatório para E-mail", render_kw={"class": "btn btn-primary btn-lg"}
    )


# ====================================================================
# FORMULÁRIOS DO SISTEMA DE OCORRÊNCIAS
# ====================================================================


class OcorrenciaForm(FlaskForm):
    """Formulário para cadastro/edição de ocorrências."""

    condominio_id = SelectField(
        "Condomínio", coerce=optional_int_coerce, validators=[Optional()], choices=[]
    )
    turno = SelectField(
        "Turno",
        choices=[('Diurno', 'Diurno'), ('Noturno', 'Noturno')],
        validators=[DataRequired(message="Selecione o turno.")],
    )
    supervisor_id = SelectField(
        "Supervisor", coerce=optional_int_coerce, validators=[Optional()], choices=[]
    )
    colaboradores_envolvidos = SelectMultipleField(
        "Colaboradores Envolvidos",
        coerce=optional_int_coerce,
        validators=[Optional()],
        choices=[],
        render_kw={"class": "form-select", "size": "5"},
    )
    data_hora_ocorrencia = DateTimeLocalField(
        "Data e Hora da Ocorrência",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired(message="Insira a data e hora da ocorrência.")],
        render_kw={"class": "form-control"},
    )
    endereco_especifico = StringField(
        "Endereço específico da Ocorrência (Opcional)",
        validators=[Optional(), Length(max=255)],
        render_kw={"class": "form-control"},
    )
    relatorio_final = TextAreaField(
        "Relatório Final da Ocorrência",
        validators=[DataRequired(message="O relatório não pode ficar em branco.")],
        render_kw={"rows": 15, "class": "form-control"},
    )
    ocorrencia_tipo_id = SelectField(
        "Tipo da Ocorrência (Selecione ou crie um novo abaixo)",
        coerce=optional_int_coerce,
        validators=[Optional()],
        choices=[],
    )
    novo_tipo_ocorrencia = StringField(
        "Novo Tipo de Ocorrência (se não encontrar na lista)",
        validators=[Optional(), Length(min=3, max=100)],
    )
    orgaos_acionados = SelectMultipleField(
        "Órgãos Públicos Acionados",
        coerce=optional_int_coerce,
        validators=[Optional()],
        choices=[],
        render_kw={"class": "form-select", "size": "5"},
    )
    status = SelectField(
        "Status",
        choices=[('Registrada', 'Registrada'), ('Em Andamento', 'Em Andamento'), ('Concluída', 'Concluída')],
        validators=[DataRequired(message="Selecione um status.")],
        default='Registrada',
    )
    submit = SubmitField("Salvar Ocorrência", render_kw={"class": "btn btn-primary"})

    def validate(self, extra_validators=None) -> bool:
        """Custom validation for the occurrence form."""
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False
        # Example: custom validation
        return True


class OrgaoPublicoForm(FlaskForm):
    nome = StringField(
        "Nome do Órgão Público (Ex: Polícia Militar, SAMU)",
        validators=[DataRequired(), Length(min=3, max=100)],
    )
    contato = StringField(
        "Contato (Telefone, etc.) (Opcional)", validators=[Optional(), Length(max=100)]
    )
    submit = SubmitField("Salvar", render_kw={"class": "btn btn-primary"})

    def validate_nome(self, nome) -> None:
        """Validate the public agency name field."""
        # Example of custom validation
        pass


# ====================================================================
# FORMULÁRIOS DE FERRAMENTAS (NOVA SEÇÃO)
# ====================================================================


class AnalisadorForm(FlaskForm):
    relatorio_bruto = TextAreaField(
        "Relatório Bruto",
        validators=[
            DataRequired(message="O campo do relatório não pode estar vazio."),
            Length(
                max=12000, message="O relatório excedeu o limite de 12000 caracteres."
            ),
        ],
        render_kw={
            "rows": "18",
            "class": "form-control",
            "placeholder": "Cole o relatório bruto aqui...",
        },
    )
    submit = SubmitField(
        "Analisar e Corrigir", render_kw={"class": "btn btn-primary btn-lg"}
    )
