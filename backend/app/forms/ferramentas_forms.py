from flask_wtf import FlaskForm
from wtforms import TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length

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