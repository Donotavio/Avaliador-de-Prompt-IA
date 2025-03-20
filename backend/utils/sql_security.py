"""
Utilitários para garantir consultas SQL seguras e prevenir injeção SQL.
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from sqlalchemy.engine import Connection
from sqlalchemy import text

logger = logging.getLogger(__name__)

def validate_table_name(table_name: str) -> bool:
    """
    Valida o nome de uma tabela para garantir que contém apenas caracteres permitidos.
    
    Args:
        table_name: Nome da tabela a ser validado
        
    Returns:
        bool: True se o nome for válido, False caso contrário
    """
    # Regex para validar nomes de tabelas permitidos (letras, números e underscore)
    valid_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
    return bool(valid_pattern.match(table_name))

def validate_column_name(column_name: str) -> bool:
    """
    Valida o nome de uma coluna para garantir que contém apenas caracteres permitidos.
    
    Args:
        column_name: Nome da coluna a ser validado
        
    Returns:
        bool: True se o nome for válido, False caso contrário
    """
    # Mesmo padrão para colunas
    valid_pattern = re.compile(r'^[a-zA-Z0-9_]+$')
    return bool(valid_pattern.match(column_name))

def safe_execute(
    connection: Connection, 
    sql_query: str, 
    params: Optional[Dict[str, Any]] = None
) -> Any:
    """
    Executa consultas SQL de forma segura usando parâmetros nomeados.
    
    Args:
        connection: Conexão SQLAlchemy
        sql_query: Query SQL com marcadores nomeados (:param)
        params: Dicionário com os valores dos parâmetros
        
    Returns:
        Resultado da execução da query
        
    Raises:
        ValueError: Se a query contiver sintaxe suspeita
    """
    # Verifica sintaxe básica para padrões suspeitos
    suspicious_patterns = [
        r';.*--',      # Tentativa de injeção com comentário
        r';\s*DROP',   # Tentativa de DROP
        r';\s*DELETE', # Tentativa de DELETE
        r';\s*INSERT', # Tentativa de INSERT
        r';\s*UPDATE', # Tentativa de UPDATE
        r';\s*ALTER',  # Tentativa de ALTER
        r'UNION\s+SELECT', # Tentativa de UNION
        r'--',         # Comentário SQL
        r'/\*'         # Comentário multilinhas
    ]
    
    # Verifica a query contra padrões suspeitos
    for pattern in suspicious_patterns:
        if re.search(pattern, sql_query, re.IGNORECASE):
            logger.error(f"Consulta SQL suspeita detectada: {sql_query}")
            raise ValueError("Consulta SQL potencialmente perigosa detectada")
    
    # Usa text() do SQLAlchemy para preparar a consulta
    statement = text(sql_query)
    
    # Executa com parâmetros (ou sem eles se não fornecidos)
    if params:
        return connection.execute(statement, params)
    else:
        return connection.execute(statement)

def safe_select_where_equals(
    connection: Connection,
    table_name: str,
    columns: List[str],
    where_column: str,
    where_value: Any
) -> Any:
    """
    Executa uma consulta SELECT segura com uma condição WHERE simples.
    
    Args:
        connection: Conexão SQLAlchemy
        table_name: Nome da tabela
        columns: Lista de colunas a serem selecionadas
        where_column: Coluna para a condição WHERE
        where_value: Valor para a condição WHERE
        
    Returns:
        Resultado da consulta
        
    Raises:
        ValueError: Se os nomes de tabela ou coluna não forem válidos
    """
    # Valida nomes de tabelas e colunas
    if not validate_table_name(table_name):
        raise ValueError(f"Nome de tabela inválido: {table_name}")
    
    if not validate_column_name(where_column):
        raise ValueError(f"Nome de coluna inválido: {where_column}")
    
    for col in columns:
        if not validate_column_name(col):
            raise ValueError(f"Nome de coluna inválido: {col}")
    
    # Constrói a consulta de forma segura
    columns_str = ", ".join(columns)
    query = f"SELECT {columns_str} FROM {table_name} WHERE {where_column} = :value"
    
    # Executa a consulta com parâmetros
    return safe_execute(connection, query, {"value": where_value})

def log_sql_warning(query: str, params: Optional[Dict[str, Any]] = None) -> None:
    """
    Registra um aviso sobre uma consulta SQL potencialmente insegura.
    
    Args:
        query: A consulta SQL
        params: Parâmetros da consulta (opcional)
    """
    if params:
        logger.warning(f"Consulta SQL potencialmente insegura: {query} com parâmetros {params}")
    else:
        logger.warning(f"Consulta SQL potencialmente insegura: {query}") 