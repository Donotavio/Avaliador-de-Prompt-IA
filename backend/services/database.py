from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from sqlalchemy import text
import sys
import logging

# Adiciona o diretório pai ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sql_security import safe_execute

# Carrega variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")
USER_DATABASE = os.getenv("USER_DATABASE")
DATABASE = os.getenv("DATABASE")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")

# Cria string de conexão MySQL
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{USER_DATABASE}:{DATABASE_PASSWORD}@{DATABASE_URL}/{DATABASE}"

# Parâmetros de conexão para MySQL remoto
connect_args = {
    "connect_timeout": 30,  # 30 segundos de timeout para conexão
    "read_timeout": 30,     # 30 segundos de timeout para leitura
    "write_timeout": 30,    # 30 segundos de timeout para escrita
}

# Cria engine do SQLAlchemy com configurações robustas para conexão remota
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    pool_size=10,              # Tamanho máximo do pool de conexões
    max_overflow=20,           # Conexões adicionais permitidas além do pool_size
    pool_timeout=30,           # Timeout em segundos para obter uma conexão do pool
    pool_recycle=1800,         # Recicla conexões após 30 minutos (evita o erro "MySQL server has gone away")
    pool_pre_ping=True         # Verifica se a conexão ainda está ativa antes de usar
)

# Cria sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos declarativos
Base = declarative_base()

# Dependency para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Função para testar a conexão com o banco de dados
def test_db_connection():
    try:
        # Cria uma conexão de teste
        connection = engine.connect()
        
        # Executa uma consulta simples usando a função segura
        safe_execute(connection, "SELECT 1")
        
        connection.close()
        print("Conexão com o banco de dados estabelecida com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {str(e)}")
        return False
        
# Teste de conexão quando este arquivo é executado diretamente
if __name__ == "__main__":
    test_db_connection() 