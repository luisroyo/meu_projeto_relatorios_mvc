# locale_config.py - Configuração de localização para o sistema
# Padroniza todos os textos para português brasileiro

import locale
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LocaleConfig:
    """Configuração de localização para o sistema."""
    
    # Configuração padrão
    DEFAULT_LOCALE = 'pt_BR'
    DEFAULT_ENCODING = 'UTF-8'
    
    # Locales suportados
    SUPPORTED_LOCALES = ['pt_BR', 'pt_BR.UTF-8', 'pt_BR.ISO8859-1']
    
    # Nomes dos meses em português
    MONTH_NAMES = {
        'pt_BR': [
            'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
    }
    
    # Nomes dos meses abreviados em português
    MONTH_NAMES_SHORT = {
        'pt_BR': [
            'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
            'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
        ]
    }
    
    # Nomes dos dias da semana em português
    DAY_NAMES = {
        'pt_BR': [
            'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
            'Quinta-feira', 'Sexta-feira', 'Sábado'
        ]
    }
    
    # Nomes dos dias abreviados em português
    DAY_NAMES_SHORT = {
        'pt_BR': [
            'Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'
        ]
    }
    
    # Traduções de textos comuns
    TRANSLATIONS = {
        'pt_BR': {
            # Status e mensagens
            'active': 'Ativo',
            'inactive': 'Inativo',
            'pending': 'Pendente',
            'approved': 'Aprovado',
            'rejected': 'Rejeitado',
            'completed': 'Concluído',
            'cancelled': 'Cancelado',
            'processing': 'Processando',
            'error': 'Erro',
            'success': 'Sucesso',
            'warning': 'Aviso',
            'info': 'Informação',
            
            # Turnos
            'morning': 'Diurno',
            'night': 'Noturno',
            'day': 'Diurno',
            'evening': 'Vespertino',
            
            # Tipos de ocorrência
            'theft': 'Roubo',
            'vandalism': 'Vandalismo',
            'suspicious_activity': 'Atividade Suspeita',
            'maintenance': 'Manutenção',
            'security_incident': 'Incidente de Segurança',
            'other': 'Outro',
            
            # Mensagens de sistema
            'loading': 'Carregando...',
            'processing': 'Processando...',
            'saving': 'Salvando...',
            'deleting': 'Excluindo...',
            'updating': 'Atualizando...',
            'creating': 'Criando...',
            'searching': 'Buscando...',
            'filtering': 'Filtrando...',
            
            # Botões
            'save': 'Salvar',
            'cancel': 'Cancelar',
            'delete': 'Excluir',
            'edit': 'Editar',
            'create': 'Criar',
            'update': 'Atualizar',
            'search': 'Buscar',
            'filter': 'Filtrar',
            'clear': 'Limpar',
            'close': 'Fechar',
            'confirm': 'Confirmar',
            'back': 'Voltar',
            'next': 'Próximo',
            'previous': 'Anterior',
            
            # Campos de formulário
            'name': 'Nome',
            'email': 'E-mail',
            'password': 'Senha',
            'confirm_password': 'Confirmar Senha',
            'username': 'Nome de Usuário',
            'full_name': 'Nome Completo',
            'phone': 'Telefone',
            'address': 'Endereço',
            'city': 'Cidade',
            'state': 'Estado',
            'country': 'País',
            'zip_code': 'CEP',
            'date': 'Data',
            'time': 'Hora',
            'datetime': 'Data e Hora',
            'description': 'Descrição',
            'notes': 'Observações',
            'status': 'Status',
            'type': 'Tipo',
            'category': 'Categoria',
            'priority': 'Prioridade',
            'assigned_to': 'Atribuído a',
            'created_by': 'Criado por',
            'created_at': 'Criado em',
            'updated_at': 'Atualizado em',
            'deleted_at': 'Excluído em',
            
            # Validações
            'required_field': 'Campo obrigatório',
            'invalid_format': 'Formato inválido',
            'min_length': 'Tamanho mínimo não atingido',
            'max_length': 'Tamanho máximo excedido',
            'invalid_email': 'E-mail inválido',
            'passwords_not_match': 'Senhas não coincidem',
            'invalid_date': 'Data inválida',
            'invalid_time': 'Hora inválida',
            'future_date_not_allowed': 'Data futura não permitida',
            'past_date_not_allowed': 'Data passada não permitida',
            
            # Mensagens de erro
            'error_occurred': 'Ocorreu um erro',
            'try_again': 'Tente novamente',
            'contact_support': 'Entre em contato com o suporte',
            'page_not_found': 'Página não encontrada',
            'access_denied': 'Acesso negado',
            'session_expired': 'Sessão expirada',
            'invalid_credentials': 'Credenciais inválidas',
            'account_locked': 'Conta bloqueada',
            'too_many_attempts': 'Muitas tentativas',
            
            # Mensagens de sucesso
            'saved_successfully': 'Salvo com sucesso',
            'updated_successfully': 'Atualizado com sucesso',
            'deleted_successfully': 'Excluído com sucesso',
            'created_successfully': 'Criado com sucesso',
            'operation_completed': 'Operação concluída',
            'changes_saved': 'Alterações salvas',
            'login_successful': 'Login realizado com sucesso',
            'logout_successful': 'Logout realizado com sucesso',
            'password_changed': 'Senha alterada com sucesso',
            
            # Dashboards e relatórios
            'dashboard': 'Dashboard',
            'reports': 'Relatórios',
            'analytics': 'Análises',
            'metrics': 'Métricas',
            'statistics': 'Estatísticas',
            'charts': 'Gráficos',
            'filters': 'Filtros',
            'export': 'Exportar',
            'print': 'Imprimir',
            'download': 'Download',
            'upload': 'Upload',
            'refresh': 'Atualizar',
            'auto_refresh': 'Atualização Automática',
            
            # Navegação
            'home': 'Início',
            'menu': 'Menu',
            'settings': 'Configurações',
            'profile': 'Perfil',
            'account': 'Conta',
            'preferences': 'Preferências',
            'help': 'Ajuda',
            'support': 'Suporte',
            'about': 'Sobre',
            'contact': 'Contato',
            'logout': 'Sair',
            'login': 'Entrar',
            'register': 'Cadastrar',
            
            # Tabelas e listas
            'no_data': 'Nenhum dado encontrado',
            'no_results': 'Nenhum resultado encontrado',
            'loading_data': 'Carregando dados...',
            'showing_results': 'Mostrando resultados',
            'of': 'de',
            'total': 'Total',
            'page': 'Página',
            'rows_per_page': 'Linhas por página',
            'first': 'Primeiro',
            'last': 'Último',
            'previous_page': 'Página anterior',
            'next_page': 'Próxima página',
            
            # Filtros e busca
            'search_placeholder': 'Digite para buscar...',
            'filter_by': 'Filtrar por',
            'clear_filters': 'Limpar filtros',
            'apply_filters': 'Aplicar filtros',
            'select_all': 'Selecionar todos',
            'deselect_all': 'Desselecionar todos',
            'select_none': 'Nenhuma seleção',
            'custom_range': 'Intervalo personalizado',
            'today': 'Hoje',
            'yesterday': 'Ontem',
            'this_week': 'Esta semana',
            'last_week': 'Semana passada',
            'this_month': 'Este mês',
            'last_month': 'Mês passado',
            'this_year': 'Este ano',
            'last_year': 'Ano passado',
        }
    }
    
    @classmethod
    def setup_locale(cls, locale_name: str = None) -> bool:
        """
        Configura o locale do sistema.
        
        Args:
            locale_name: Nome do locale a ser configurado
            
        Returns:
            bool: True se configurado com sucesso, False caso contrário
        """
        if not locale_name:
            locale_name = cls.DEFAULT_LOCALE
            
        for loc in cls.SUPPORTED_LOCALES:
            try:
                locale.setlocale(locale.LC_TIME, loc)
                logger.info(f"Locale configurado com sucesso: {loc}")
                return True
            except locale.Error:
                continue
        
        logger.warning(f"Locale '{locale_name}' não encontrado. Nomes de meses podem aparecer em inglês.")
        return False
    
    @classmethod
    def get_month_name(cls, month: int, locale_name: str = 'pt_BR', short: bool = False) -> str:
        """
        Obtém o nome do mês no idioma especificado.
        
        Args:
            month: Número do mês (1-12)
            locale_name: Nome do locale
            short: Se deve retornar nome abreviado
            
        Returns:
            str: Nome do mês
        """
        if month < 1 or month > 12:
            return ''
            
        if short:
            month_names = cls.MONTH_NAMES_SHORT.get(locale_name, cls.MONTH_NAMES_SHORT['pt_BR'])
        else:
            month_names = cls.MONTH_NAMES.get(locale_name, cls.MONTH_NAMES['pt_BR'])
            
        return month_names[month - 1]
    
    @classmethod
    def get_day_name(cls, day: int, locale_name: str = 'pt_BR', short: bool = False) -> str:
        """
        Obtém o nome do dia da semana no idioma especificado.
        
        Args:
            day: Número do dia (0-6, onde 0 = Domingo)
            locale_name: Nome do locale
            short: Se deve retornar nome abreviado
            
        Returns:
            str: Nome do dia
        """
        if day < 0 or day > 6:
            return ''
            
        if short:
            day_names = cls.DAY_NAMES_SHORT.get(locale_name, cls.DAY_NAMES_SHORT['pt_BR'])
        else:
            day_names = cls.DAY_NAMES.get(locale_name, cls.DAY_NAMES['pt_BR'])
            
        return day_names[day]
    
    @classmethod
    def translate(cls, key: str, locale_name: str = 'pt_BR') -> str:
        """
        Traduz uma chave para o idioma especificado.
        
        Args:
            key: Chave de tradução
            locale_name: Nome do locale
            
        Returns:
            str: Texto traduzido ou a chave original se não encontrada
        """
        translations = cls.TRANSLATIONS.get(locale_name, cls.TRANSLATIONS['pt_BR'])
        return translations.get(key, key)
    
    @classmethod
    def get_all_month_names(cls, locale_name: str = 'pt_BR', short: bool = False) -> List[str]:
        """
        Obtém todos os nomes dos meses no idioma especificado.
        
        Args:
            locale_name: Nome do locale
            short: Se deve retornar nomes abreviados
            
        Returns:
            List[str]: Lista com todos os nomes dos meses
        """
        if short:
            return cls.MONTH_NAMES_SHORT.get(locale_name, cls.MONTH_NAMES_SHORT['pt_BR'])
        else:
            return cls.MONTH_NAMES.get(locale_name, cls.MONTH_NAMES['pt_BR'])
    
    @classmethod
    def get_all_day_names(cls, locale_name: str = 'pt_BR', short: bool = False) -> List[str]:
        """
        Obtém todos os nomes dos dias da semana no idioma especificado.
        
        Args:
            locale_name: Nome do locale
            short: Se deve retornar nomes abreviados
            
        Returns:
            List[str]: Lista com todos os nomes dos dias
        """
        if short:
            return cls.DAY_NAMES_SHORT.get(locale_name, cls.DAY_NAMES_SHORT['pt_BR'])
        else:
            return cls.DAY_NAMES.get(locale_name, cls.DAY_NAMES['pt_BR'])


# Configuração automática ao importar o módulo
LocaleConfig.setup_locale()
