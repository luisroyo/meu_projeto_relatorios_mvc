from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, DateField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, ValidationError

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
        if self.nome_condominio.data == 'Outro' and not field.data.strip():
            raise ValidationError('Por favor, especifique o nome do condomínio se "Outro" foi selecionado.') 