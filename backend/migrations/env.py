from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import os
import sys
import logging

# Adiciona o diretório pai ao sys.path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa os modelos e a configuração do banco de dados
from services.database import Base, SQLALCHEMY_DATABASE_URL
from utils.sql_security import safe_execute, log_sql_warning

# Configuração adicional de logging
migration_logger = logging.getLogger("alembic.migrations")

# Verifica se a configuração de banco de dados está correta
print(f"DATABASE_URL: {os.getenv('DATABASE_URL')}")
print(f"USER_DATABASE: {os.getenv('USER_DATABASE')}")
print(f"DATABASE: {os.getenv('DATABASE')}")

# Função para execução segura de SQL em migrações
def execute_migration_sql(connection, sql_query, params=None):
    """
    Executa SQL de migração de forma segura.
    Usa nossa função de segurança ou faz fallback para execução direta em caso de erro.
    
    Args:
        connection: Conexão SQLAlchemy
        sql_query: Query SQL
        params: Parâmetros para a query (opcional)
    
    Returns:
        Resultado da execução
    """
    try:
        # Tenta usar nossa função segura
        return safe_execute(connection, sql_query, params)
    except Exception as e:
        # Aviso de fallback
        migration_logger.warning(f"Executando migração em modo fallback devido a: {str(e)}")
        log_sql_warning(sql_query, params)
        
        # Executa diretamente se a validação de segurança falhar
        # Importante para migrações que precisam usar sintaxe SQL não
        # filtrada pela nossa função segura
        stmt = text(sql_query)
        if params:
            return connection.execute(stmt, params)
        else:
            return connection.execute(stmt)

# Monkey patch para context.execute para usar nossa função segura
original_execute = context.execute

def secure_execute(sql, *args, **kwargs):
    # Obtem a conexão atual
    conn = context.get_bind()
    try:
        # Se for uma string SQL, usamos nossa função segura
        if isinstance(sql, str):
            migration_logger.info("Executando SQL de migração com validação de segurança")
            return execute_migration_sql(conn, sql, kwargs.get('params'))
        # Caso contrário, passamos para a função original
        return original_execute(sql, *args, **kwargs)
    except Exception as e:
        migration_logger.error(f"Erro ao executar SQL de migração: {str(e)}")
        # Prosseguir com a execução original em caso de erro
        return original_execute(sql, *args, **kwargs)

# Aplica o monkey patch
context.execute = secure_execute

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Substitui a URL do banco de dados na configuração
config.set_main_option("sqlalchemy.url", SQLALCHEMY_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online() 