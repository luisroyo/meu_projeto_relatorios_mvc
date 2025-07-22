from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, DateTimeLocalField, TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Length

def optional_int_coerce(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

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
        validators=[DataRequired(message="Selecione um tipo de ocorrência.")],
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
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False
        return True 