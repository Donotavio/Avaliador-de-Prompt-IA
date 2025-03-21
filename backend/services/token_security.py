"""
Módulo para gerenciar segurança de tokens JWT.
Implementa geração segura de chaves, rotação de chaves e validação adequada.
"""

import os
import secrets
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Tuple
from jose import jwt, JWTError
from fastapi import HTTPException, status
import functools

logger = logging.getLogger(__name__)

# Constantes de configuração
JWT_ALGORITHM = "HS256"  # Algoritmo usado para assinatura de tokens
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora (mais seguro que 7 dias)
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 dias para token de refresh
JWT_KEY_ROTATION_DAYS = 30            # Rotação de chaves a cada 30 dias
KEY_LENGTH_BYTES = 32                 # 256 bits

# Arquivo para armazenar histórico de chaves (para validação de tokens antigos)
KEY_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "jwt_keys.json")

# Estrutura para armazenar chaves em memória
jwt_keys = {
    "current_key": "",
    "current_key_id": "",
    "current_key_created": 0,
    "previous_keys": []  # Lista de tuplas (key_id, key, created_timestamp)
}

def ensure_data_dir():
    """Garante que o diretório para armazenar as chaves existe"""
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)

def generate_secret_key() -> str:
    """Gera uma chave secreta forte usando secrets"""
    return secrets.token_urlsafe(KEY_LENGTH_BYTES)

def generate_key_id() -> str:
    """Gera um ID único para a chave"""
    return secrets.token_hex(8)

def load_keys() -> bool:
    """
    Carrega chaves de JWT do arquivo ou gera novas se necessário.
    Implementa rotação automática de chaves.
    
    Returns:
        bool: True se as chaves foram carregadas com sucesso
    """
    global jwt_keys
    ensure_data_dir()
    
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(KEY_HISTORY_FILE):
            # Gerar chave inicial
            return rotate_keys()
        
        # Carrega dados do arquivo
        with open(KEY_HISTORY_FILE, "r") as f:
            stored_keys = json.load(f)
        
        # Atualiza as chaves em memória
        jwt_keys = stored_keys
        
        # Verifica se é necessário rotacionar a chave
        current_time = time.time()
        key_age_days = (current_time - jwt_keys["current_key_created"]) / (24 * 60 * 60)
        
        if key_age_days >= JWT_KEY_ROTATION_DAYS:
            logger.info(f"Chave JWT atual tem {key_age_days:.1f} dias. Iniciando rotação.")
            return rotate_keys()
        
        return True
    
    except Exception as e:
        logger.error(f"Erro ao carregar chaves JWT: {str(e)}")
        # Em caso de erro, rotaciona as chaves
        return rotate_keys()

def rotate_keys() -> bool:
    """
    Implementa rotação de chaves JWT.
    Gera uma nova chave e armazena a anterior no histórico.
    
    Returns:
        bool: True se a rotação foi concluída com sucesso
    """
    global jwt_keys
    ensure_data_dir()
    
    try:
        # Salva chave atual (se existir) no histórico
        if jwt_keys["current_key"]:
            # Limita a quantidade de chaves anteriores para evitar crescimento infinito
            max_previous_keys = 3  # Mantém apenas as 3 últimas chaves
            
            jwt_keys["previous_keys"].append({
                "key_id": jwt_keys["current_key_id"],
                "key": jwt_keys["current_key"],
                "created": jwt_keys["current_key_created"]
            })
            
            # Trunca a lista se necessário
            if len(jwt_keys["previous_keys"]) > max_previous_keys:
                jwt_keys["previous_keys"] = jwt_keys["previous_keys"][-max_previous_keys:]
        
        # Gera nova chave
        jwt_keys["current_key"] = generate_secret_key()
        jwt_keys["current_key_id"] = generate_key_id()
        jwt_keys["current_key_created"] = time.time()
        
        # Salva no arquivo
        with open(KEY_HISTORY_FILE, "w") as f:
            json.dump(jwt_keys, f)
        
        logger.info(f"Rotação de chave JWT concluída. Nova chave ID: {jwt_keys['current_key_id']}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao rotacionar chaves JWT: {str(e)}")
        # Em caso de erro, tenta pelo menos garantir que haja uma chave disponível
        if not jwt_keys["current_key"]:
            jwt_keys["current_key"] = generate_secret_key()
            jwt_keys["current_key_id"] = generate_key_id()
            jwt_keys["current_key_created"] = time.time()
        return False

def get_current_key() -> Tuple[str, str]:
    """
    Obtém a chave atual e seu ID.
    Carrega as chaves se necessário.
    
    Returns:
        Tuple[str, str]: (key_id, key)
    """
    # Carrega as chaves se não estiverem carregadas
    if not jwt_keys["current_key"]:
        load_keys()
    
    return jwt_keys["current_key_id"], jwt_keys["current_key"]

def find_key_by_id(key_id: str) -> Optional[str]:
    """
    Encontra uma chave pelo seu ID.
    Verifica a chave atual e o histórico.
    
    Args:
        key_id: ID da chave a ser encontrada
        
    Returns:
        Optional[str]: A chave encontrada ou None
    """
    # Verifica se é a chave atual
    if jwt_keys["current_key_id"] == key_id:
        return jwt_keys["current_key"]
    
    # Procura no histórico
    for prev_key in jwt_keys["previous_keys"]:
        if prev_key["key_id"] == key_id:
            return prev_key["key"]
    
    return None

def handle_security_exception(func):
    """
    Decorador para lidar com exceções de segurança de maneira padronizada
    com registro de log detalhado e sem comprometer a segurança.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JWTError as e:
            logger.error(f"Erro JWT: {e}")
            # Não revela detalhes específicos do erro na mensagem de exceção
            raise JWTError("Erro de autenticação")
        except RuntimeError as e:
            # Captura erros específicos de segurança de nossa implementação
            logger.error(f"Erro crítico de segurança: {e}")
            raise JWTError("Erro crítico no sistema de segurança")
        except Exception as e:
            logger.error(f"Erro inesperado em operação de segurança: {e}")
            raise JWTError("Erro interno no sistema de segurança")
    return wrapper

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um token de acesso JWT.
    
    Args:
        data: Dados a serem codificados no token
        expires_delta: Tempo opcional de expiração
        
    Returns:
        str: Token JWT assinado
    """
    to_encode = data.copy()
    
    # Define expiração
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Adiciona claims padrão
    key_id, key = get_current_key()
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "kid": key_id,
        "type": "access"
    })
    
    # Codifica o token
    encoded_jwt = jwt.encode(to_encode, key, algorithm=JWT_ALGORITHM, headers={"kid": key_id})
    
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any]
) -> str:
    """
    Cria um token de refresh JWT com expiração mais longa.
    
    Args:
        data: Dados a serem codificados no token
        
    Returns:
        str: Token JWT de refresh assinado
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Adiciona claims padrão
    key_id, key = get_current_key()
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "kid": key_id,
        "type": "refresh"
    })
    
    # Codifica o token
    encoded_jwt = jwt.encode(to_encode, key, algorithm=JWT_ALGORITHM, headers={"kid": key_id})
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica e valida um token JWT.
    
    Args:
        token: Token JWT a ser decodificado
        
    Returns:
        Dict[str, Any]: Payload do token
        
    Raises:
        HTTPException: Se o token for inválido
    """
    try:
        # Decodifica o cabeçalho para obter o key_id
        header = jwt.get_unverified_header(token)
        key_id = header.get("kid")
        
        if not key_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token JWT sem identificador de chave",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Encontra a chave correspondente
        key = find_key_by_id(key_id)
        if not key:
            logger.warning(f"Tentativa de uso de token com key_id inválido: {key_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token JWT inválido (chave não encontrada)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Decodifica o token
        payload = jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
        
        return payload
    
    except JWTError as e:
        logger.warning(f"Erro ao decodificar token JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Função para inicializar as chaves JWT no arranque da aplicação
def initialize_jwt_keys():
    """
    Inicializa as chaves JWT no arranque da aplicação.
    Esta função deve ser chamada uma única vez no início do servidor.
    """
    logger.info("Inicializando chaves JWT...")
    try:
        # Garante que diretório de dados existe
        ensure_data_dir()
        
        # Carrega chaves existentes ou cria novas
        loaded = load_keys()
        
        if loaded:
            logger.info(f"Chaves JWT carregadas com sucesso. Utilizando chave com ID: {jwt_keys['current_key_id']}")
        else:
            logger.warning("Falha ao carregar as chaves JWT. Usando chaves padrão.")
    except Exception as e:
        logger.error(f"Erro ao inicializar chaves JWT: {str(e)}")
        # Fallback para chave padrão em caso de erro
        if not jwt_keys["current_key"]:
            jwt_keys["current_key"] = generate_secret_key()
            jwt_keys["current_key_id"] = generate_key_id()
            jwt_keys["current_key_created"] = time.time()
            # Tenta salvar as chaves
            try:
                with open(KEY_HISTORY_FILE, "w") as f:
                    json.dump(jwt_keys, f)
                logger.warning("Criada chave JWT de emergência devido a erro na inicialização")
            except Exception as e2:
                logger.error(f"Erro ao salvar chave de emergência: {str(e2)}")

# Inicializa carregando as chaves quando o módulo é importado
load_keys()

# A função initialize_jwt_keys será chamada no início do servidor
# para garantir que as chaves estejam prontas para uso 

# Aplica o decorador às funções críticas de segurança
create_access_token = handle_security_exception(create_access_token)
create_refresh_token = handle_security_exception(create_refresh_token)
decode_token = handle_security_exception(decode_token) 