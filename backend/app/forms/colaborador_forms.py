from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

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
        if matricula_field.data:
            pass 