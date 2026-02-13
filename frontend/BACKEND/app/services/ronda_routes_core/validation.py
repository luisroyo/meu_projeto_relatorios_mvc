def validar_campos_essenciais(log_bruto, condominio_obj, data_plantao_str, escala_plantao):
    if not all([log_bruto, condominio_obj, data_plantao_str, escala_plantao]):
        return False, "Dados essenciais ausentes."
    return True, ""

def validar_condominio_existe(condominio_obj):
    if not condominio_obj or not hasattr(condominio_obj, 'id'):
        return False, "Condomínio inválido."
    return True, "" 