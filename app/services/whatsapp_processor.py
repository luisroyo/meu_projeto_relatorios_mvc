#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de Mensagens do WhatsApp - Integração com Sistema de Ronda
======================================================================

Este módulo processa arquivos .txt exportados do WhatsApp e integra
com o sistema de ronda para preenchimento automático de logs.
"""

import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Mensagem:
    """Classe para representar uma mensagem do WhatsApp."""
    data_hora: datetime
    autor: str
    conteudo: str
    linha_original: str


@dataclass
class Plantao:
    """Classe para representar um plantão."""
    data: datetime
    tipo: str  # "diurno" ou "noturno"
    inicio: datetime
    fim: datetime
    mensagens: List[Mensagem]


class WhatsAppProcessor:
    """Processador principal para arquivos do WhatsApp - OTIMIZADO."""
    
    def __init__(self):
        # Regex compiladas para melhor performance
        self.pattern = re.compile(
            r'\[(\d{2}/\d{2}/\d{4}),\s*(\d{2}:\d{2})\]\s*([^:]+):\s*(.+)'
        )
        
        self.pattern_alt = re.compile(
            r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+-\s+([^:]+):\s*(.+)'
        )
        
        # Regex para mensagens do sistema (compiladas uma vez)
        self.system_patterns = [
            re.compile(r'mensagem apagada', re.IGNORECASE),
            re.compile(r'adicionou', re.IGNORECASE),
            re.compile(r'saiu', re.IGNORECASE),
            re.compile(r'removido', re.IGNORECASE),
            re.compile(r'alterou', re.IGNORECASE),
            re.compile(r'criou', re.IGNORECASE),
            re.compile(r'<mídia oculta>', re.IGNORECASE),
            re.compile(r'criptografia de ponta a ponta', re.IGNORECASE),
            re.compile(r'somente as pessoas que fazem parte', re.IGNORECASE),
        ]
        
        # Cache para melhor performance
        self.last_processed_date = None
        self.last_processed_plantao = None
        self._datetime_cache = {}  # Cache para parsing de datetime
    
    def is_system_message(self, conteudo: str) -> bool:
        """Verifica se a mensagem é do sistema - OTIMIZADO."""
        return any(pattern.search(conteudo) for pattern in self.system_patterns)
    
    def parse_datetime(self, data_str: str, hora_str: str) -> datetime:
        """Converte string de data e hora para datetime - COM CACHE."""
        cache_key = f"{data_str}_{hora_str}"
        if cache_key not in self._datetime_cache:
            self._datetime_cache[cache_key] = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
        return self._datetime_cache[cache_key]
    
    def parse_date(self, data_str: str) -> datetime:
        """Converte string de data para datetime."""
        return datetime.strptime(data_str, "%d/%m/%Y")
    
    def get_plantao_info(self, dt: datetime) -> Tuple[datetime, str, datetime, datetime]:
        """
        Determina informações do plantão baseado na data/hora - OTIMIZADO.
        
        Returns:
            (data_plantao, tipo, inicio, fim)
        """
        hora = dt.hour
        
        if 6 <= hora < 18:
            # Plantão diurno: 06h-18h (mesmo dia)
            data_plantao = dt.replace(hour=6, minute=0, second=0, microsecond=0)
            inicio = data_plantao
            fim = data_plantao.replace(hour=17, minute=59, second=59)
            tipo = "diurno"
        else:
            # Plantão noturno: 18h-06h (atravessa a meia-noite)
            if hora >= 18:
                # Início do plantão noturno (18h do dia atual)
                data_plantao = dt.replace(hour=18, minute=0, second=0, microsecond=0)
                inicio = data_plantao
                fim = (data_plantao + timedelta(days=1)).replace(hour=5, minute=59, second=59)
            else:
                # Continuação do plantão noturno (madrugada - 00h às 06h)
                # Pertence ao plantão que começou às 18h do dia anterior
                data_plantao = (dt - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
                inicio = data_plantao
                fim = dt.replace(hour=5, minute=59, second=59)
            tipo = "noturno"
        
        return data_plantao, tipo, inicio, fim
    
    def detect_plantao_change(self, dt: datetime) -> bool:
        """
        Detecta se houve mudança de data ou plantão - OTIMIZADO.
        """
        data_plantao, tipo, _, _ = self.get_plantao_info(dt)
        current_plantao = (data_plantao.date(), tipo)
        
        # Se é a primeira vez processando
        if self.last_processed_plantao is None:
            self.last_processed_plantao = current_plantao
            self.last_processed_date = data_plantao.date()
            return True
        
        # Verifica se houve mudança
        if current_plantao != self.last_processed_plantao:
            self.last_processed_plantao = current_plantao
            self.last_processed_date = data_plantao.date()
            return True
        
        return False
    
    def parse_messages(self, content: str, data_inicio: Optional[datetime] = None, 
                      data_fim: Optional[datetime] = None, autor_filtro: Optional[str] = None) -> List[Mensagem]:
        """Extrai mensagens do conteúdo do arquivo - OTIMIZADO."""
        mensagens = []
        linhas = content.split('\n')
        i = 0
        total_linhas = len(linhas)
        
        # Pré-compila filtros para melhor performance
        autor_filtro_lower = autor_filtro.lower() if autor_filtro else None
        
        while i < total_linhas:
            linha = linhas[i].strip()
            if not linha:
                i += 1
                continue
                
            # Tenta o formato padrão primeiro
            match = self.pattern.match(linha)
            if match:
                data_str, hora_str, autor, conteudo = match.groups()
            else:
                # Tenta o formato alternativo
                match = self.pattern_alt.match(linha)
                if match:
                    data_str, hora_str, autor, conteudo = match.groups()
                else:
                    i += 1
                    continue
            
            # Pula mensagens do sistema rapidamente
            if self.is_system_message(conteudo):
                i += 1
                continue
            
            # Coleta linhas adicionais da mensagem de forma otimizada
            conteudo_completo = [conteudo]
            j = i + 1
            while j < total_linhas:
                proxima_linha = linhas[j].strip()
                if not proxima_linha:
                    break
                # Se a próxima linha não é uma nova mensagem, adiciona ao conteúdo
                if not self.pattern.match(proxima_linha) and not self.pattern_alt.match(proxima_linha):
                    conteudo_completo.append(proxima_linha)
                    j += 1
                else:
                    break
            
            try:
                data_hora = self.parse_datetime(data_str, hora_str)
                
                # Aplica filtros de forma otimizada
                if data_inicio and data_hora < data_inicio:
                    i = j
                    continue
                if data_fim and data_hora > data_fim:
                    i = j
                    continue
                if autor_filtro_lower and autor_filtro_lower not in autor.lower():
                    i = j
                    continue
                
                mensagem = Mensagem(
                    data_hora=data_hora,
                    autor=autor.strip(),
                    conteudo="\n".join(conteudo_completo).strip(),
                    linha_original=linha
                )
                mensagens.append(mensagem)
                i = j
            except ValueError as e:
                print(f"Erro ao processar linha: {linha} - {e}")
                i += 1
        
        return mensagens
    
    def group_by_plantao(self, mensagens: List[Mensagem]) -> List[Plantao]:
        """Agrupa mensagens por plantão - OTIMIZADO."""
        if not mensagens:
            return []
        
        # Ordena mensagens por data/hora uma única vez
        mensagens.sort(key=lambda m: m.data_hora)
        
        plantoes = {}
        
        for msg in mensagens:
            data_plantao, tipo, inicio, fim = self.get_plantao_info(msg.data_hora)
            
            # Chave única para o plantão
            chave = (data_plantao.date(), tipo)
            
            if chave not in plantoes:
                plantao = Plantao(
                    data=data_plantao,
                    tipo=tipo,
                    inicio=inicio,
                    fim=fim,
                    mensagens=[]
                )
                plantoes[chave] = plantao
            
            plantoes[chave].mensagens.append(msg)
        
        # Ordena plantões por data
        return sorted(plantoes.values(), key=lambda p: p.data)
    
    def process_file(self, filepath: str, data_inicio: Optional[datetime] = None, 
                    data_fim: Optional[datetime] = None, autor_filtro: Optional[str] = None) -> List[Plantao]:
        """Processa um arquivo .txt do WhatsApp - OTIMIZADO."""
        try:
            # Tenta UTF-8 primeiro, depois latin-1
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(filepath, 'r', encoding='latin-1') as f:
                    content = f.read()
        
            # Processa mensagens com filtros
            mensagens = self.parse_messages(content, data_inicio, data_fim, autor_filtro)
            plantoes = self.group_by_plantao(mensagens)
            
            # Verifica mudança de plantão para o plantão atual
            if plantoes:
                plantao_atual = plantoes[-1]
                if self.detect_plantao_change(plantao_atual.data):
                    print(f"🚀 Novo plantão detectado: {plantao_atual.data.strftime('%d/%m/%Y')} - {plantao_atual.tipo}")
                    print(f"📊 Total de mensagens: {len(plantao_atual.mensagens)}")
            
            return plantoes
            
        except Exception as e:
            print(f"❌ Erro ao processar arquivo {filepath}: {e}")
            return []
    
    def format_for_ronda_log(self, plantao: Plantao) -> str:
        """Formata as mensagens do plantão para o formato de log de ronda - OTIMIZADO."""
        if not plantao.mensagens:
            return ""
        
        # Ordena mensagens por horário uma única vez
        plantao.mensagens.sort(key=lambda m: m.data_hora)
        
        # Usa list comprehension para melhor performance
        log_lines = [
            f"[{msg.data_hora.strftime('%H:%M')}, {msg.data_hora.strftime('%d/%m/%Y')}] {msg.autor}: {msg.conteudo}"
            for msg in plantao.mensagens
        ]
        
        return "\n".join(log_lines)
    
    def get_available_plantoes(self, filepath: str) -> List[Dict]:
        """Retorna lista de plantões disponíveis no arquivo - OTIMIZADO."""
        plantoes = self.process_file(filepath)
        
        # Usa list comprehension para melhor performance
        available = [
            {
                'data': plantao.data.date(),
                'data_str': plantao.data.strftime("%d/%m/%Y"),
                'tipo': plantao.tipo,
                'horario': "06h às 18h" if plantao.tipo == "diurno" else "18h às 06h",
                'escala': "06h às 18h" if plantao.tipo == "diurno" else "18h às 06h",
                'total_mensagens': len(plantao.mensagens),
                'inicio': plantao.inicio,
                'fim': plantao.fim
            }
            for plantao in plantoes
        ]
        
        return available 