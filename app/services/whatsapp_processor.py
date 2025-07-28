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
    """Processador principal para arquivos do WhatsApp."""
    
    def __init__(self):
        # Regex para capturar mensagens do WhatsApp (formato padrão)
        self.pattern = re.compile(
            r'\[(\d{2}/\d{2}/\d{4}),\s*(\d{2}:\d{2})\]\s*([^:]+):\s*(.+)'
        )
        
        # Regex para capturar mensagens do WhatsApp (formato alternativo)
        self.pattern_alt = re.compile(
            r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s+-\s+([^:]+):\s*(.+)'
        )
        
        # Regex para identificar mensagens do sistema
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
    
    def is_system_message(self, conteudo: str) -> bool:
        """Verifica se a mensagem é do sistema."""
        return any(pattern.search(conteudo) for pattern in self.system_patterns)
    
    def parse_datetime(self, data_str: str, hora_str: str) -> datetime:
        """Converte string de data e hora para datetime."""
        return datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M")
    
    def parse_date(self, data_str: str) -> datetime:
        """Converte string de data para datetime."""
        return datetime.strptime(data_str, "%d/%m/%Y")
    
    def get_plantao_info(self, dt: datetime) -> Tuple[datetime, str, datetime, datetime]:
        """
        Determina informações do plantão baseado na data/hora.
        
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
    
    def parse_messages(self, content: str, data_inicio: Optional[datetime] = None, 
                      data_fim: Optional[datetime] = None, autor_filtro: Optional[str] = None) -> List[Mensagem]:
        """Extrai mensagens do conteúdo do arquivo com filtros opcionais."""
        mensagens = []
        linhas = content.split('\n')
        i = 0
        
        while i < len(linhas):
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
            
            # Pula mensagens do sistema
            if self.is_system_message(conteudo):
                i += 1
                continue
            
            # Coleta linhas adicionais da mensagem
            conteudo_completo = [conteudo]
            j = i + 1
            while j < len(linhas):
                proxima_linha = linhas[j].strip()
                if not proxima_linha:
                    break
                # Se a próxima linha não é uma nova mensagem (não tem data/hora), adiciona ao conteúdo
                if not self.pattern.match(proxima_linha) and not self.pattern_alt.match(proxima_linha):
                    conteudo_completo.append(proxima_linha)
                    j += 1
                else:
                    break
            
            try:
                data_hora = self.parse_datetime(data_str, hora_str)
                
                # Aplica filtros por data/hora completa
                if data_inicio and data_hora < data_inicio:
                    i = j
                    continue
                if data_fim and data_hora > data_fim:
                    i = j
                    continue
                if autor_filtro and autor_filtro.lower() not in autor.lower():
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
        """Agrupa mensagens por plantão."""
        if not mensagens:
            return []
        
        # Ordena mensagens por data/hora
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
        """Processa um arquivo .txt do WhatsApp e retorna plantões."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Tenta com encoding diferente
            with open(filepath, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Processa mensagens com filtros
        mensagens = self.parse_messages(content, data_inicio, data_fim, autor_filtro)
        plantoes = self.group_by_plantao(mensagens)
        
        return plantoes
    
    def format_for_ronda_log(self, plantao: Plantao) -> str:
        """Formata as mensagens do plantão para o formato de log de ronda."""
        if not plantao.mensagens:
            return ""
        
        # Ordena mensagens por horário
        plantao.mensagens.sort(key=lambda m: m.data_hora)
        
        log_lines = []
        for msg in plantao.mensagens:
            hora_str = msg.data_hora.strftime("%H:%M")
            data_str = msg.data_hora.strftime("%d/%m/%Y")
            log_lines.append(f"[{hora_str}, {data_str}] {msg.autor}: {msg.conteudo}")
        
        return "\n".join(log_lines)
    
    def get_available_plantoes(self, filepath: str) -> List[Dict]:
        """Retorna lista de plantões disponíveis no arquivo."""
        plantoes = self.process_file(filepath)
        
        available = []
        for plantao in plantoes:
            data_str = plantao.data.strftime("%d/%m/%Y")
            if plantao.tipo == "diurno":
                horario_str = "06h às 18h"
                escala = "06h às 18h"
            else:
                horario_str = "18h às 06h"
                escala = "18h às 06h"
            
            available.append({
                'data': plantao.data.date(),
                'data_str': data_str,
                'tipo': plantao.tipo,
                'horario': horario_str,
                'escala': escala,
                'total_mensagens': len(plantao.mensagens),
                'inicio': plantao.inicio,
                'fim': plantao.fim
            })
        
        return available 