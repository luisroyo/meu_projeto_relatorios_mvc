from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

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
        pass 