from flask import jsonify, request
from flask_login import login_required

from app.blueprints.api import api_bp
from app.services.text_tools import clean_text, languagetool_check, ai_transform, parse_eml_to_text


@api_bp.route('/text/clean', methods=['POST'])
@login_required
def api_text_clean():
    data = request.get_json() or {}
    text = data.get('text', '')
    return jsonify({ 'cleaned': clean_text(text) })


@api_bp.route('/text/clean-eml', methods=['POST'])
@login_required
def api_text_clean_eml():
    """Aceita upload de .eml (raw ou base64/texto) e devolve texto limpo."""
    if request.content_type and 'multipart/form-data' in request.content_type:
        f = request.files.get('file')
        if not f:
            return jsonify({'error': 'Arquivo .eml não enviado.'}), 400
        raw = f.read()
    else:
        data = request.get_json() or {}
        raw = data.get('eml_raw') or ''
        raw = raw.encode('utf-8', errors='ignore')

    text = parse_eml_to_text(raw)
    return jsonify({ 'cleaned': text })


@api_bp.route('/text/analyze', methods=['POST'])
@login_required
def api_text_analyze():
    data = request.get_json() or {}
    text = data.get('text', '')
    if not text:
        return jsonify({ 'matches': [] })
    result = languagetool_check(text)
    return jsonify(result)


@api_bp.route('/text/transform', methods=['POST'])
@login_required
def api_text_transform():
    data = request.get_json() or {}
    text = data.get('text', '')
    mode = data.get('mode', 'formal')
    tone = data.get('tone')
    max_chars = data.get('max_chars')
    transformed = ai_transform(text, mode=mode, tone=tone, max_chars=max_chars)
    return jsonify({ 'transformed': transformed })


