import re
import logging
from datetime import datetime
from app import db
from app.models import OcorrenciaTipo, Colaborador, Condominio, OrgaoPublico

logger = logging.getLogger(__name__)

class OcorrenciaParser:
    @staticmethod
    def processar_e_corrigir_texto(texto):
        """Processa e corrige o texto do relatório"""
        # Correções básicas
        correcoes = {
            "hoirario": "horário",
            "conatto": "contato",
            "marador": "morador",
            "fernado": "Fernando",
            "ocorrencia": "ocorrência",
            "marad": "morador"
        }
        
        texto_corrigido = texto
        for erro, correcao in correcoes.items():
            texto_corrigido = texto_corrigido.replace(erro, correcao)
        
        # Melhorias de formatação
        texto_corrigido = texto_corrigido.strip()
        texto_corrigido = re.sub(r'\s+', ' ', texto_corrigido)  # Remove espaços extras
        texto_corrigido = re.sub(r'([.!?])\s*([A-Za-z])', r'\1 \2', texto_corrigido)  # Espaços após pontuação
        
        # Capitalização de início de frases
        linhas = texto_corrigido.split('\n')
        linhas_corrigidas = []
        for linha in linhas:
            if linha.strip():
                linha = linha.strip()
                if linha and not linha[0].isupper():
                    linha = linha[0].upper() + linha[1:]
                linhas_corrigidas.append(linha)
            else:
                linhas_corrigidas.append('')
        
        return '\n'.join(linhas_corrigidas)

    @staticmethod
    def formatar_para_email_profissional(texto):
        """Formata o texto para envio profissional por email"""
        # Adiciona cabeçalho profissional
        cabecalho = "RELATÓRIO DE OCORRÊNCIA\n"
        cabecalho += "=" * 30 + "\n\n"
        
        # Formata o corpo
        corpo = texto.replace('\n', '\n    ')
        
        # Adiciona rodapé
        rodape = "\n\n" + "=" * 30 + "\n"
        rodape += "Este relatório foi gerado automaticamente pelo sistema de gestão de segurança.\n"
        rodape += "Data de geração: " + datetime.now().strftime("%d/%m/%Y %H:%M")
        
        return cabecalho + corpo + rodape

    @staticmethod
    def extrair_dados_relatorio(texto):
        """Extrai dados estruturados do relatório de ocorrência"""
        dados = {}
        
        try:
            logger.info(f"Iniciando extração de dados do texto: {texto[:200]}...")
            
            # Extrair data
            data_match = re.search(r'Data:\s*(\d{2}/\d{2}/\d{4})', texto)
            if data_match:
                data_str = data_match.group(1)
                # Converter formato DD/MM/YYYY para YYYY-MM-DD
                try:
                    dia, mes, ano = data_str.split('/')
                    dados['data_hora_ocorrencia'] = f"{ano}-{mes}-{dia}"
                    logger.info(f"Data extraída: {data_str} -> {dados['data_hora_ocorrencia']}")
                except ValueError:
                    logger.warning(f"Erro ao analisar data: {data_str}")
            
            # Extrair hora
            hora_match = re.search(r'Hora:\s*(\d{2}:\d{2})', texto)
            if hora_match:
                dados['hora_ocorrencia'] = hora_match.group(1)
                logger.info(f"Hora extraída: {dados['hora_ocorrencia']}")
            
            # ============================================================================
            # EXTRAÇÃO DE ENDEREÇO - ABORDAGEM SIMPLIFICADA
            # ============================================================================
            logger.info("Iniciando busca por endereço...")
            
            # Buscar por "Local:" e extrair até a próxima linha ou palavra-chave
            local_match = re.search(r'Local:\s*([^\n\r]+)', texto, re.IGNORECASE)
            if local_match:
                endereco = local_match.group(1).strip()
                logger.info(f"Endereço bruto encontrado: '{endereco}'")
                
                # Limpar o endereço - parar na primeira palavra-chave
                palavras_fim = ['ocorrência', 'ocorrencia', 'relato', 'ações', 'acionamentos']
                for palavra in palavras_fim:
                    if palavra in endereco.lower():
                        pos = endereco.lower().find(palavra)
                        if pos > 0:
                            endereco = endereco[:pos].strip()
                            break
                
                # Se ainda estiver muito longo, parar na primeira vírgula ou hífen
                if len(endereco) > 50:
                    for separador in [',', '-', ';']:
                        if separador in endereco:
                            pos = endereco.find(separador)
                            endereco = endereco[:pos].strip()
                            break
                
                dados['endereco_especifico'] = endereco
                logger.info(f"Endereço limpo extraído: {endereco}")
            
            # ============================================================================
            # EXTRAÇÃO DE TIPO DE OCORRÊNCIA - LÓGICA INTELIGENTE
            # ============================================================================
            logger.info("Iniciando busca por tipo de ocorrência...")
            
            tipos_ocorrencia = OcorrenciaTipo.query.all()
            tipo_encontrado = False
            
            # Palavras-chave para cada tipo de ocorrência
            palavras_chave_tipos = {
                'Auxílio ao Residencial': ['porta', 'residência', 'residencial', 'morador', 'auxílio', 'ajuda'],
                'Verificação': ['verificação', 'verificar', 'checagem', 'inspeção', 'observação'],
                'Perturbação de sossego': ['barulho', 'som', 'música', 'festa', 'perturbação', 'sossego'],
                'Tentativa de furto': ['tentativa', 'furto', 'roubo', 'invasão', 'suspeito'],
                'Furtos': ['furto', 'roubo', 'furtado', 'desapareceu'],
                'Vandalismo': ['vandalismo', 'destruição', 'danificado', 'quebrado', 'pichação']
            }
            
            # Primeiro: tentar encontrar por nome exato
            for tipo in tipos_ocorrencia:
                if tipo.nome.lower() in texto.lower():
                    dados['ocorrencia_tipo_id'] = tipo.id
                    logger.info(f"Tipo de ocorrência identificado (nome exato): {tipo.nome} (ID: {tipo.id})")
                    tipo_encontrado = True
                    break
            
            # Segundo: se não encontrou, usar palavras-chave
            if not tipo_encontrado:
                logger.info("Buscando por palavras-chave...")
                melhor_match = None
                melhor_score = 0
                
                for tipo in tipos_ocorrencia:
                    if tipo.nome in palavras_chave_tipos:
                        palavras_chave = palavras_chave_tipos[tipo.nome]
                        score = 0
                        
                        for palavra in palavras_chave:
                            if palavra.lower() in texto.lower():
                                score += 1
                        
                        if score > melhor_score:
                            melhor_score = score
                            melhor_match = tipo
                
                if melhor_match and melhor_score > 0:
                    dados['ocorrencia_tipo_id'] = melhor_match.id
                    logger.info(f"Tipo identificado por palavras-chave: {melhor_match.nome} (ID: {melhor_match.id}, score: {melhor_score})")
                    tipo_encontrado = True
            
            # Terceiro: se ainda não encontrou, usar tipo padrão inteligente
            if not tipo_encontrado:
                logger.info("Usando tipo padrão inteligente...")
                
                # Verificar se é algo relacionado a residencial/morador
                if any(palavra in texto.lower() for palavra in ['residencial', 'morador', 'porta', 'residência']):
                    tipo_padrao = OcorrenciaTipo.query.filter_by(nome="Auxílio ao Residencial").first()
                    if tipo_padrao:
                        dados['ocorrencia_tipo_id'] = tipo_padrao.id
                        logger.info(f"Tipo padrão inteligente (residencial): {tipo_padrao.nome} (ID: {tipo_padrao.id})")
                    else:
                        # Fallback para o primeiro tipo disponível
                        primeiro_tipo = OcorrenciaTipo.query.first()
                        if primeiro_tipo:
                            dados['ocorrencia_tipo_id'] = primeiro_tipo.id
                            logger.info(f"Fallback para primeiro tipo: {primeiro_tipo.nome} (ID: {primeiro_tipo.id})")
                else:
                    # Fallback para "Verificação" se existir
                    tipo_verificacao = OcorrenciaTipo.query.filter_by(nome="Verificação").first()
                    if tipo_verificacao:
                        dados['ocorrencia_tipo_id'] = tipo_verificacao.id
                        logger.info(f"Tipo padrão (verificação): {tipo_verificacao.nome} (ID: {tipo_verificacao.id})")
                    else:
                        # Último fallback
                        primeiro_tipo = OcorrenciaTipo.query.first()
                        if primeiro_tipo:
                            dados['ocorrencia_tipo_id'] = primeiro_tipo.id
                            logger.info(f"Fallback final: {primeiro_tipo.nome} (ID: {primeiro_tipo.id})")
            
            # ============================================================================
            # EXTRAÇÃO DE COLABORADORES - LÓGICA CORRIGIDA E MELHORADA
            # ============================================================================
            logger.info("Iniciando busca por colaboradores...")
            
            colaboradores_envolvidos = []
            colaboradores = Colaborador.query.all()
            
            # Palavras-chave que indicam que a pessoa é um colaborador do sistema
            indicadores_colaborador = [
                'águia', 'agente', 'segurança', 'vigilante', 'ronda', 'patrulha',
                'supervisor', 'coordenador', 'responsável pelo registro'
            ]
            
            # Palavras-chave que indicam que a pessoa NÃO é um colaborador
            indicadores_nao_colaborador = [
                'morador', 'residente', 'sócio', 'responsável pela mudança', 'testemunha',
                'envolvido', 'cpf', 'endereço', 'escritório', 'estabelecimento'
            ]
            
            for colaborador in colaboradores:
                nome_completo = colaborador.nome_completo.lower()
                primeiro_nome = colaborador.nome_completo.split()[0].lower()
                
                # Verificar se o nome aparece no texto
                if nome_completo in texto.lower() or primeiro_nome in texto.lower():
                    # Buscar o contexto onde o nome aparece
                    nome_para_buscar = nome_completo if len(nome_completo) > 3 else primeiro_nome
                    pos_inicio = texto.lower().find(nome_para_buscar)
                    
                    if pos_inicio != -1:
                        # Pegar contexto antes e depois do nome (100 caracteres para mais contexto)
                        contexto_inicio = max(0, pos_inicio - 100)
                        contexto_fim = min(len(texto), pos_inicio + len(nome_para_buscar) + 100)
                        contexto = texto[contexto_inicio:contexto_fim]
                        
                        # Verificar se é realmente um colaborador
                        is_colaborador = False
                        
                        # Se contém indicadores de colaborador, é válido
                        for indicador in indicadores_colaborador:
                            if indicador in contexto.lower():
                                is_colaborador = True
                                break
                        
                        # Se contém indicadores de NÃO colaborador, verificar se não é um falso positivo
                        for indicador in indicadores_nao_colaborador:
                            if indicador in contexto.lower():
                                # Verificar se é um falso positivo (ex: "responsável pelo registro" vs "responsável pela mudança")
                                if indicador == 'responsável pelo registro':
                                    continue
                                elif indicador == 'envolvido' and 'envolvido na ocorrência' in contexto.lower():
                                    continue
                                else:
                                    is_colaborador = False
                                    break
                        
                        # Lógica adicional: se o nome aparece próximo a "responsável pelo registro", é colaborador
                        if 'responsável pelo registro' in contexto.lower() and nome_para_buscar in contexto.lower():
                            is_colaborador = True
                        
                        if is_colaborador:
                            colaboradores_envolvidos.append(colaborador.id)
            
            if colaboradores_envolvidos:
                dados['colaboradores_envolvidos'] = list(set(colaboradores_envolvidos)) # Remove duplicatas
                logger.info(f"Total de colaboradores identificados: {len(dados['colaboradores_envolvidos'])}")
            
            # ============================================================================
            # EXTRAÇÃO DE TURNO
            # ============================================================================
            if 'hora_ocorrencia' in dados:
                hora = int(dados['hora_ocorrencia'].split(':')[0])
                if 6 <= hora < 18:
                    dados['turno'] = 'Diurno'
                else:
                    dados['turno'] = 'Noturno'
                logger.info(f"Turno determinado: {dados['turno']} (hora: {hora})")
            
            # ============================================================================
            # IDENTIFICAÇÃO DE CONDOMÍNIO
            # ============================================================================
            condominios = Condominio.query.all()
            for condominio in condominios:
                if condominio.nome.lower() in texto.lower():
                    dados['condominio_id'] = condominio.id
                    logger.info(f"Condomínio identificado: {condominio.nome} (ID: {condominio.id})")
                    break
            
            logger.info(f"Dados extraídos finais: {dados}")
                
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            dados = {}
        
        return dados
