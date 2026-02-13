# tests/test_ocorrencia_dashboard.py
import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock

from app.services.dashboard.ocorrencia_dashboard import get_ocorrencia_dashboard_data


class TestOcorrenciaDashboard:
    """Testes para o dashboard de ocorrências"""
    
    @pytest.fixture
    def mock_filters(self):
        """Filtros de teste padrão"""
        return {
            "data_inicio_str": "2024-01-01",
            "data_fim_str": "2024-01-31",
            "supervisor_id": None,
            "condominio_id": None,
            "turno": None,
            "status": None
        }
    
    @pytest.fixture
    def mock_filters_with_supervisor(self):
        """Filtros com supervisor específico"""
        return {
            "data_inicio_str": "2024-01-01",
            "data_fim_str": "2024-01-31",
            "supervisor_id": 1,
            "condominio_id": None,
            "turno": None,
            "status": None
        }
    
    @pytest.fixture
    def mock_vw_ocorrencias(self):
        """Mock da view VWOcorrenciasDetalhadas"""
        mock_ocorrencia = Mock()
        mock_ocorrencia.id = 1
        mock_ocorrencia.tipo = "Furto"
        mock_ocorrencia.condominio = "Residencial A"
        mock_ocorrencia.supervisor = "supervisor1"
        mock_ocorrencia.turno = "Diurno Par"
        mock_ocorrencia.status = "Registrada"
        mock_ocorrencia.data_hora_ocorrencia = datetime(2024, 1, 15, 10, 30)
        return mock_ocorrencia
    
    @patch('app.services.dashboard.ocorrencia_dashboard.db')
    @patch('app.services.dashboard.ocorrencia_dashboard.ocorrencia_service')
    @patch('app.services.dashboard.ocorrencia_dashboard.parse_date_range')
    def test_get_ocorrencia_dashboard_data_basic(self, mock_parse_date, mock_ocorrencia_service, mock_db, mock_filters):
        """Testa o dashboard básico sem filtros específicos"""
        # Mock das datas
        mock_parse_date.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock da query base
        mock_base_query = Mock()
        mock_base_query.count.return_value = 10
        mock_base_query.filter.return_value.count.return_value = 5
        
        # Mock do apply_ocorrencia_filters
        mock_ocorrencia_service.apply_ocorrencia_filters.return_value = mock_base_query
        
        # Mock das queries específicas
        mock_session = Mock()
        mock_db.session = mock_session
        
        # Mock para ocorrências por tipo
        mock_tipo_query = Mock()
        mock_tipo_query.group_by.return_value.order_by.return_value.all.return_value = [
            ("Furto", 5),
            ("Vandalismo", 3),
            ("Outros", 2)
        ]
        mock_session.query.return_value.filter.return_value = mock_tipo_query
        
        # Mock para ocorrências por condomínio
        mock_cond_query = Mock()
        mock_cond_query.group_by.return_value.order_by.return_value.all.return_value = [
            ("Residencial A", 6),
            ("Residencial B", 4)
        ]
        mock_session.query.return_value.filter.return_value = mock_cond_query
        
        # Mock para evolução diária
        mock_evolucao_query = Mock()
        mock_evolucao_query.group_by.return_value.order_by.return_value.all.return_value = [
            (date(2024, 1, 15), "Diurno Par", 3),
            (date(2024, 1, 16), "Noturno Impar", 2)
        ]
        mock_session.query.return_value.filter.return_value = mock_evolucao_query
        
        # Mock para últimas ocorrências
        mock_ultimas_query = Mock()
        mock_ultimas_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value = mock_ultimas_query
        
        # Mock para top colaboradores
        mock_colab_query = Mock()
        mock_colab_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.join.return_value.join.return_value.filter.return_value = mock_colab_query
        
        # Mock para User (supervisor)
        mock_user = Mock()
        mock_user.username = "supervisor1"
        mock_user.query.get.return_value = mock_user
        
        # Mock para kpis_helper
        with patch('app.services.dashboard.ocorrencia_dashboard.kpis_helper') as mock_kpis:
            mock_kpis.get_ocorrencia_period_info.return_value = {
                "dias_com_dados": 15,
                "periodo_solicitado_dias": 31,
                "cobertura_periodo": 48.4
            }
            mock_kpis.calculate_ocorrencia_period_comparison.return_value = {
                "total_atual": 10,
                "total_anterior": 8,
                "variacao_percentual": 25.0
            }
            mock_kpis.find_top_ocorrencia_supervisor.return_value = "supervisor1"
            
            # Executar a função
            result = get_ocorrencia_dashboard_data(mock_filters)
        
        # Verificações
        assert result["total_ocorrencias"] == 10
        assert result["ocorrencias_abertas"] == 5
        assert result["tipo_mais_comum"] == "Furto"
        assert result["kpi_supervisor_label"] == "Supervisor com Mais Ocorrências"
        assert result["kpi_supervisor_name"] == "supervisor1"
        
        # Verificar dados dos gráficos
        assert result["tipo_labels"] == ["Furto", "Vandalismo", "Outros"]
        assert result["ocorrencias_por_tipo_data"] == [5, 3, 2]
        assert result["condominio_labels"] == ["Residencial A", "Residencial B"]
        assert result["ocorrencias_por_condominio_data"] == [6, 4]
        
        # Verificar período info
        assert result["periodo_info"]["dias_com_dados"] == 15
        assert result["periodo_info"]["cobertura_periodo"] == 48.4
    
    @patch('app.services.dashboard.ocorrencia_dashboard.db')
    @patch('app.services.dashboard.ocorrencia_dashboard.ocorrencia_service')
    @patch('app.services.dashboard.ocorrencia_dashboard.parse_date_range')
    def test_get_ocorrencia_dashboard_data_with_supervisor(self, mock_parse_date, mock_ocorrencia_service, mock_db, mock_filters_with_supervisor):
        """Testa o dashboard com supervisor específico selecionado"""
        # Mock das datas
        mock_parse_date.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock da query base
        mock_base_query = Mock()
        mock_base_query.count.return_value = 6
        mock_base_query.filter.return_value.count.return_value = 3
        
        # Mock do apply_ocorrencia_filters
        mock_ocorrencia_service.apply_ocorrencia_filters.return_value = mock_base_query
        
        # Mock das queries específicas
        mock_session = Mock()
        mock_db.session = mock_session
        
        # Mock para ocorrências por tipo (filtradas por supervisor)
        mock_tipo_query = Mock()
        mock_tipo_query.group_by.return_value.order_by.return_value.all.return_value = [
            ("Furto", 3),
            ("Vandalismo", 2),
            ("Outros", 1)
        ]
        mock_session.query.return_value.filter.return_value = mock_tipo_query
        
        # Mock para ocorrências por condomínio (filtradas por supervisor)
        mock_cond_query = Mock()
        mock_cond_query.group_by.return_value.order_by.return_value.all.return_value = [
            ("Residencial A", 4),
            ("Residencial B", 2)
        ]
        mock_session.query.return_value.filter.return_value = mock_cond_query
        
        # Mock para evolução diária
        mock_evolucao_query = Mock()
        mock_evolucao_query.group_by.return_value.order_by.return_value.all.return_value = [
            (date(2024, 1, 15), "Diurno Par", 2),
            (date(2024, 1, 17), "Diurno Impar", 1)
        ]
        mock_session.query.return_value.filter.return_value = mock_evolucao_query
        
        # Mock para últimas ocorrências
        mock_ultimas_query = Mock()
        mock_ultimas_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value = mock_ultimas_query
        
        # Mock para top colaboradores
        mock_colab_query = Mock()
        mock_colab_query.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.join.return_value.join.return_value.filter.return_value = mock_colab_query
        
        # Mock para User (supervisor específico)
        mock_user = Mock()
        mock_user.username = "supervisor1"
        mock_user.id = 1
        mock_user.query.get.return_value = mock_user
        
        # Mock para kpis_helper
        with patch('app.services.dashboard.ocorrencia_dashboard.kpis_helper') as mock_kpis:
            mock_kpis.get_ocorrencia_period_info.return_value = {
                "dias_com_dados": 15,
                "periodo_solicitado_dias": 15,  # Ajustado para dias trabalhados
                "cobertura_periodo": 100.0  # 100% pois considera apenas dias trabalhados
            }
            mock_kpis.calculate_ocorrencia_period_comparison.return_value = {
                "total_atual": 6,
                "total_anterior": 4,
                "variacao_percentual": 50.0
            }
            
            # Executar a função
            result = get_ocorrencia_dashboard_data(mock_filters_with_supervisor)
        
        # Verificações específicas para supervisor
        assert result["total_ocorrencias"] == 6
        assert result["ocorrencias_abertas"] == 3
        assert result["kpi_supervisor_label"] == "Supervisor Selecionado"
        assert result["kpi_supervisor_name"] == "supervisor1"
        
        # Verificar que os gráficos mostram apenas dados do supervisor
        assert result["tipo_labels"] == ["Furto", "Vandalismo", "Outros"]
        assert result["ocorrencias_por_tipo_data"] == [3, 2, 1]  # Menos ocorrências
        assert result["condominio_labels"] == ["Residencial A", "Residencial B"]
        assert result["ocorrencias_por_condominio_data"] == [4, 2]  # Menos ocorrências
        
        # Verificar período info ajustado para supervisor
        assert result["periodo_info"]["dias_com_dados"] == 15
        assert result["periodo_info"]["periodo_solicitado_dias"] == 15
        assert result["periodo_info"]["cobertura_periodo"] == 100.0
    
    @patch('app.services.dashboard.ocorrencia_dashboard.db')
    @patch('app.services.dashboard.ocorrencia_dashboard.ocorrencia_service')
    @patch('app.services.dashboard.ocorrencia_dashboard.parse_date_range')
    def test_apply_ocorrencia_filters_called_correctly(self, mock_parse_date, mock_ocorrencia_service, mock_db, mock_filters):
        """Testa se apply_ocorrencia_filters é chamado corretamente para cada gráfico"""
        # Mock das datas
        mock_parse_date.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock da query base
        mock_base_query = Mock()
        mock_base_query.count.return_value = 5
        mock_base_query.filter.return_value.count.return_value = 2
        
        # Mock do apply_ocorrencia_filters
        mock_ocorrencia_service.apply_ocorrencia_filters.return_value = mock_base_query
        
        # Mock das queries específicas
        mock_session = Mock()
        mock_db.session = mock_session
        
        # Mock para todas as queries
        mock_query = Mock()
        mock_query.group_by.return_value.order_by.return_value.all.return_value = []
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value = mock_query
        
        # Mock para User
        mock_user = Mock()
        mock_user.username = "supervisor1"
        mock_user.query.get.return_value = mock_user
        
        # Mock para kpis_helper
        with patch('app.services.dashboard.ocorrencia_dashboard.kpis_helper') as mock_kpis:
            mock_kpis.get_ocorrencia_period_info.return_value = {
                "dias_com_dados": 10,
                "periodo_solicitado_dias": 31,
                "cobertura_periodo": 32.3
            }
            mock_kpis.calculate_ocorrencia_period_comparison.return_value = {
                "total_atual": 5,
                "total_anterior": 3,
                "variacao_percentual": 66.7
            }
            mock_kpis.find_top_ocorrencia_supervisor.return_value = "supervisor1"
            
            # Executar a função
            get_ocorrencia_dashboard_data(mock_filters)
        
        # Verificar que apply_ocorrencia_filters foi chamado para cada gráfico
        # Deve ser chamado 4 vezes: base_kpi_query, tipo, condomínio, evolução, últimas
        assert mock_ocorrencia_service.apply_ocorrencia_filters.call_count == 5
        
        # Verificar que foi chamado com os filtros corretos
        calls = mock_ocorrencia_service.apply_ocorrencia_filters.call_args_list
        for call in calls:
            args, kwargs = call
            assert args[1] == mock_filters  # Segundo argumento deve ser os filtros
    
    @patch('app.services.dashboard.ocorrencia_dashboard.db')
    @patch('app.services.dashboard.ocorrencia_dashboard.ocorrencia_service')
    @patch('app.services.dashboard.ocorrencia_dashboard.parse_date_range')
    def test_no_duplicate_date_filters(self, mock_parse_date, mock_ocorrencia_service, mock_db, mock_filters):
        """Testa que não há filtros de data duplicados"""
        # Mock das datas
        mock_parse_date.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        
        # Mock da query base
        mock_base_query = Mock()
        mock_base_query.count.return_value = 5
        mock_base_query.filter.return_value.count.return_value = 2
        
        # Mock do apply_ocorrencia_filters
        mock_ocorrencia_service.apply_ocorrencia_filters.return_value = mock_base_query
        
        # Mock das queries específicas
        mock_session = Mock()
        mock_db.session = mock_session
        
        # Mock para todas as queries
        mock_query = Mock()
        mock_query.group_by.return_value.order_by.return_value.all.return_value = []
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value = mock_query
        
        # Mock para User
        mock_user = Mock()
        mock_user.username = "supervisor1"
        mock_user.query.get.return_value = mock_user
        
        # Mock para kpis_helper
        with patch('app.services.dashboard.ocorrencia_dashboard.kpis_helper') as mock_kpis:
            mock_kpis.get_ocorrencia_period_info.return_value = {
                "dias_com_dados": 10,
                "periodo_solicitado_dias": 31,
                "cobertura_periodo": 32.3
            }
            mock_kpis.calculate_ocorrencia_period_comparison.return_value = {
                "total_atual": 5,
                "total_anterior": 3,
                "variacao_percentual": 66.7
            }
            mock_kpis.find_top_ocorrencia_supervisor.return_value = "supervisor1"
            
            # Executar a função
            result = get_ocorrencia_dashboard_data(mock_filters)
        
        # Verificar que o resultado contém os dados esperados
        assert "tipo_labels" in result
        assert "ocorrencias_por_tipo_data" in result
        assert "condominio_labels" in result
        assert "ocorrencias_por_condominio_data" in result
        assert "periodo_info" in result
        
        # Verificar que não há valores vazios ou incorretos
        assert len(result["tipo_labels"]) >= 0
        assert len(result["ocorrencias_por_tipo_data"]) >= 0
        assert len(result["condominio_labels"]) >= 0
        assert len(result["ocorrencias_por_condominio_data"]) >= 0
