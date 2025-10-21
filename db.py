"""
Módulo de gerenciamento de conexão com o banco de dados PostgreSQL
Suporta conexões duais: local e Railway (para redundância)
Inclui suporte para auditoria automática via triggers
"""

from flask import g, session
import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG, DB_CONFIG_LOCAL, DB_CONFIG_RAILWAY


def get_db_local():
    """
    Obtém a conexão com o banco de dados LOCAL.
    Cria uma nova conexão se não existir uma no contexto da aplicação.
    """
    if "db_local" not in g:
        try:
            g.db_local = psycopg2.connect(**DB_CONFIG_LOCAL)
            g.db_local.autocommit = False  # Para controlar transações manualmente
        except Exception as e:
            print(f"[AVISO] Falha ao conectar no banco LOCAL: {e}")
            g.db_local = None
    return g.db_local


def get_db_railway():
    """
    Obtém a conexão com o banco de dados RAILWAY.
    Cria uma nova conexão se não existir uma no contexto da aplicação.
    """
    if "db_railway" not in g:
        try:
            print(f"[DEBUG] Tentando conectar ao banco RAILWAY...")
            g.db_railway = psycopg2.connect(**DB_CONFIG_RAILWAY)
            g.db_railway.autocommit = False  # Para controlar transações manualmente
            print(f"[DEBUG] Conexão RAILWAY estabelecida com sucesso")
        except Exception as e:
            print(f"[AVISO] Falha ao conectar no banco RAILWAY: {e}")
            import traceback
            traceback.print_exc()
            g.db_railway = None
    return g.db_railway


def get_db():
    """
    Obtém a conexão com o banco de dados padrão (Railway para compatibilidade).
    Mantida para retrocompatibilidade com código existente.
    """
    if "db" not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
        g.db.autocommit = False
    return g.db


def get_cursor_local():
    """
    Retorna um cursor do banco LOCAL que funciona como dictionary.
    Facilita o acesso aos dados por nome de coluna.
    """
    db = get_db_local()
    if db is None:
        return None
    return db.cursor(cursor_factory=RealDictCursor)


def get_cursor_railway():
    """
    Retorna um cursor do banco RAILWAY que funciona como dictionary.
    Facilita o acesso aos dados por nome de coluna.
    """
    db = get_db_railway()
    if db is None:
        return None
    return db.cursor(cursor_factory=RealDictCursor)


def get_cursor():
    """
    Retorna um cursor do banco padrão (Railway).
    Mantida para retrocompatibilidade com código existente.
    """
    db = get_db()
    return db.cursor(cursor_factory=RealDictCursor)


def execute_dual(query, params=None):
    """
    Executa uma operação de escrita (INSERT/UPDATE/DELETE) nos dois bancos de dados.
    Retorna um dicionário com status de cada banco.
    
    Args:
        query: String SQL a ser executada
        params: Parâmetros para a query (tuple ou dict)
    
    Returns:
        dict: {'success': bool, 'local': bool, 'railway': bool, 'errors': dict}
    """
    success_local = False
    success_railway = False
    errors = {}
    
    # Executar no banco LOCAL
    try:
        cur_local = get_cursor_local()
        if cur_local:
            cur_local.execute(query, params)
            get_db_local().commit()
            success_local = True
            print(f"[DEBUG] Query executada com sucesso no banco LOCAL")
        else:
            errors['local'] = "Cursor LOCAL não disponível"
    except Exception as e:
        error_msg = str(e)
        print(f"[ERRO] Falha ao executar no banco LOCAL: {error_msg}")
        errors['local'] = error_msg
        try:
            db_local = get_db_local()
            if db_local:
                db_local.rollback()
        except:
            pass
    
    # Executar no banco RAILWAY
    try:
        cur_railway = get_cursor_railway()
        if cur_railway:
            cur_railway.execute(query, params)
            get_db_railway().commit()
            success_railway = True
            print(f"[DEBUG] Query executada com sucesso no banco RAILWAY")
        else:
            errors['railway'] = "Cursor RAILWAY não disponível"
    except Exception as e:
        error_msg = str(e)
        print(f"[ERRO] Falha ao executar no banco RAILWAY: {error_msg}")
        errors['railway'] = error_msg
        try:
            db_railway = get_db_railway()
            if db_railway:
                db_railway.rollback()
        except:
            pass
    
    # Retornar resultado detalhado
    result = {
        'success': success_local or success_railway,
        'local': success_local,
        'railway': success_railway,
        'errors': errors
    }
    
    return result


def execute_dual_with_audit(query, params=None, usuario_id=None):
    """
    Executa operação com auditoria usando SET LOCAL em transação.
    
    Args:
        query: String SQL a ser executada
        params: Parâmetros para a query
        usuario_id: ID do usuário para auditoria (obrigatório)
    
    Returns:
        dict: {'success': bool, 'local': bool, 'railway': bool, 'errors': dict}
    """
    if usuario_id is None:
        usuario_id = session.get('usuario_id', 1)  # Default: 1 (sistema)
    
    success_local = False
    success_railway = False
    errors = {}
    
    # Executar no banco LOCAL com transação
    try:
        db_local = get_db_local()
        if db_local:
            cur_local = db_local.cursor()
            
            # Iniciar transação e definir usuário
            cur_local.execute("BEGIN")
            cur_local.execute(f"SET LOCAL app.current_user_id = '{usuario_id}'")
            
            # Executar a query
            cur_local.execute(query, params)
            
            # Commit
            db_local.commit()
            success_local = True
            print(f"[DEBUG] Query com auditoria executada no LOCAL (user_id={usuario_id})")
        else:
            errors['local'] = "Conexão LOCAL não disponível"
    except Exception as e:
        error_msg = str(e)
        print(f"[ERRO] Falha no LOCAL: {error_msg}")
        errors['local'] = error_msg
        try:
            db_local = get_db_local()
            if db_local:
                db_local.rollback()
        except:
            pass
    
    # Executar no banco RAILWAY com transação
    try:
        db_railway = get_db_railway()
        if db_railway:
            cur_railway = db_railway.cursor()
            
            # Iniciar transação e definir usuário
            cur_railway.execute("BEGIN")
            cur_railway.execute(f"SET LOCAL app.current_user_id = '{usuario_id}'")
            
            # Executar a query
            cur_railway.execute(query, params)
            
            # Commit
            db_railway.commit()
            success_railway = True
            print(f"[DEBUG] Query com auditoria executada no RAILWAY (user_id={usuario_id})")
        else:
            errors['railway'] = "Conexão RAILWAY não disponível"
    except Exception as e:
        error_msg = str(e)
        print(f"[ERRO] Falha no RAILWAY: {error_msg}")
        errors['railway'] = error_msg
        try:
            db_railway = get_db_railway()
            if db_railway:
                db_railway.rollback()
        except:
            pass
    
    return {
        'success': success_local or success_railway,
        'local': success_local,
        'railway': success_railway,
        'errors': errors
    }


def close_db(e=None):
    """
    Fecha as conexões com os bancos de dados ao final do contexto da aplicação.
    """
    # Fechar conexão local
    db_local = g.pop("db_local", None)
    if db_local is not None:
        db_local.close()
    
    # Fechar conexão railway
    db_railway = g.pop("db_railway", None)
    if db_railway is not None:
        db_railway.close()
    
    # Fechar conexão padrão (retrocompatibilidade)
    db = g.pop("db", None)
    if db is not None:
        db.close()
