import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from sqlalchemy import text
import sys
import logging

# Adiciona o diretório pai ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.sql_security import safe_execute

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Obter a URL da base de dados - verificando se é uma URL completa ou se precisamos construí-la
raw_database_url = os.getenv("DATABASE_URL")
database_user = os.getenv("USER_DATABASE")
database_password = os.getenv("DATABASE_PASSWORD")
database_name = os.getenv("DATABASE")

# Construir URL completa para o MySQL
if raw_database_url and ("mysql://" in raw_database_url or "mysql+pymysql://" in raw_database_url):
    # Já é uma URL completa
    database_url = raw_database_url
else:
    # Construir a partir dos componentes
    host = "srv1783.hstgr.io" if not raw_database_url else raw_database_url
    database_url = f"mysql+pymysql://{database_user}:{database_password}@{host}:3306/{database_name}"

# Log para debug
print(f"DATABASE_URL final: {database_url}")

# Para compatibilidade com código existente
SQLALCHEMY_DATABASE_URL = database_url

# Criar engine
engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"charset": "utf8mb4"}
)

# Criar sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Função para obter uma sessão do banco de dados
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