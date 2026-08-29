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

from wtforms import DateField, SelectField

class GeradorRelatorioPlantaoForm(FlaskForm):
    data_plantao = DateField("Data do Plantão", validators=[DataRequired()])
    turno = SelectField("Turno", choices=[("Noturno", "Noturno"), ("Diurno", "Diurno")])
    supervisor = SelectField("Supervisor", choices=[("Luis Royo", "Luis Royo"), ("Eduardo", "Eduardo")]) # Pode ser preenchido dinamicamente na rota

    # OPERAÇÃO INTERNA – MASTER / RESIDENCIAIS
    distribuicao_master = TextAreaField("Agentes de Monitoramento (Um por linha)", render_kw={"rows": 4})
    
    ausencias_master = TextAreaField("Ausências Master (Um por linha)", render_kw={"rows": 2})
    ausencias_residenciais = TextAreaField("Ausências Residenciais (Um por linha)", render_kw={"rows": 2})
    
    ferias_residenciais = TextAreaField("Férias (Um por linha)", render_kw={"rows": 3})
    
    info_senha = TextAreaField("Senha do dia", render_kw={"rows": 1})
    info_abastecimentos = TextAreaField("Abastecimentos", render_kw={"rows": 2})
    info_folgas = TextAreaField("Folgas Trabalhadas (Um por linha)", render_kw={"rows": 3})

    # OPERAÇÃO UNISETER
    uniseter_inspetor = TextAreaField("Inspetor (Um por linha)", render_kw={"rows": 1})
    uniseter_lider = TextAreaField("Líder (Um por linha)", render_kw={"rows": 1})
    uniseter_vigilantes = TextAreaField("Vigilantes (Um por linha)", render_kw={"rows": 2})
    uniseter_apoio = TextAreaField("Apoio Alpha 01/Atendente de Sinistro (Um por linha)", render_kw={"rows": 4})
    
    info_movimentacao = TextAreaField("Informações e Movimentação de Pessoal (Um por linha)", render_kw={"rows": 3})

    submit = SubmitField("Gerar Relatório", render_kw={"class": "btn btn-primary"}) 