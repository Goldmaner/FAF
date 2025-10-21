"""
Script para configurar triggers de auditoria na tabela parcerias_despesas
Executa uma única vez para criar as funções e triggers no PostgreSQL
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from config import DB_CONFIG_LOCAL, DB_CONFIG_RAILWAY

def get_connection_local():
    """Obtém conexão direta com o banco LOCAL"""
    try:
        return psycopg2.connect(**DB_CONFIG_LOCAL)
    except Exception as e:
        print(f"Erro ao conectar no banco LOCAL: {e}")
        return None

def get_connection_railway():
    """Obtém conexão direta com o banco RAILWAY"""
    try:
        return psycopg2.connect(**DB_CONFIG_RAILWAY)
    except Exception as e:
        print(f"Erro ao conectar no banco RAILWAY: {e}")
        return None

def setup_audit_triggers():
    """Cria função e triggers para auditoria automática de parcerias_despesas"""
    
    # SQL para criar a função de auditoria
    create_function_sql = """
    CREATE OR REPLACE FUNCTION parcerias_despesas_audit_trigger()
    RETURNS TRIGGER AS $$
    DECLARE
        v_usuario_id INTEGER;
    BEGIN
        -- Tentar obter usuario_id da sessão (configurado pela aplicação)
        -- Se não existir, usar um valor padrão (1 = sistema)
        BEGIN
            v_usuario_id := current_setting('app.current_user_id')::INTEGER;
        EXCEPTION
            WHEN OTHERS THEN
                v_usuario_id := 1; -- ID padrão do sistema
        END;

        IF (TG_OP = 'DELETE') THEN
            INSERT INTO parcerias_despesas_auditoria (
                parcerias_despesas_id,
                usuario_id,
                acao,
                dados_anteriores,
                dados_novos,
                data_modificacao
            ) VALUES (
                OLD.id,
                v_usuario_id,
                'DELETE',
                row_to_json(OLD)::JSONB,
                NULL,
                now()
            );
            RETURN OLD;
        ELSIF (TG_OP = 'UPDATE') THEN
            INSERT INTO parcerias_despesas_auditoria (
                parcerias_despesas_id,
                usuario_id,
                acao,
                dados_anteriores,
                dados_novos,
                data_modificacao
            ) VALUES (
                NEW.id,
                v_usuario_id,
                'UPDATE',
                row_to_json(OLD)::JSONB,
                row_to_json(NEW)::JSONB,
                now()
            );
            RETURN NEW;
        ELSIF (TG_OP = 'INSERT') THEN
            INSERT INTO parcerias_despesas_auditoria (
                parcerias_despesas_id,
                usuario_id,
                acao,
                dados_anteriores,
                dados_novos,
                data_modificacao
            ) VALUES (
                NEW.id,
                v_usuario_id,
                'INSERT',
                NULL,
                row_to_json(NEW)::JSONB,
                now()
            );
            RETURN NEW;
        END IF;
        RETURN NULL;
    END;
    $$ LANGUAGE plpgsql;
    """
    
    # SQL para criar o trigger
    create_trigger_sql = """
    DROP TRIGGER IF EXISTS parcerias_despesas_audit_trigger ON parcerias_despesas;
    
    CREATE TRIGGER parcerias_despesas_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON parcerias_despesas
    FOR EACH ROW EXECUTE FUNCTION parcerias_despesas_audit_trigger();
    """
    
    print("🔧 Configurando sistema de auditoria...")
    
    # Executar no banco LOCAL
    try:
        print("\n📍 Banco LOCAL:")
        conn = get_connection_local()
        if conn:
            cur = conn.cursor()
            print("  ✓ Criando função de auditoria...")
            cur.execute(create_function_sql)
            print("  ✓ Criando trigger...")
            cur.execute(create_trigger_sql)
            conn.commit()
            cur.close()
            conn.close()
            print("  ✅ Auditoria configurada no banco LOCAL")
        else:
            print("  ❌ Não foi possível conectar ao banco LOCAL")
    except Exception as e:
        print(f"  ❌ Erro no banco LOCAL: {e}")
    
    # Executar no banco RAILWAY
    try:
        print("\n📍 Banco RAILWAY:")
        conn = get_connection_railway()
        if conn:
            cur = conn.cursor()
            print("  ✓ Criando função de auditoria...")
            cur.execute(create_function_sql)
            print("  ✓ Criando trigger...")
            cur.execute(create_trigger_sql)
            conn.commit()
            cur.close()
            conn.close()
            print("  ✅ Auditoria configurada no banco RAILWAY")
        else:
            print("  ❌ Não foi possível conectar ao banco RAILWAY")
    except Exception as e:
        print(f"  ❌ Erro no banco RAILWAY: {e}")
    
    print("\n✅ Setup de auditoria concluído!")
    print("\n📝 Como funciona:")
    print("  • Toda INSERT/UPDATE/DELETE em parcerias_despesas será registrada")
    print("  • O trigger captura automaticamente o usuario_id da sessão")
    print("  • Dados anteriores e novos são armazenados em formato JSONB")
    print("  • Use o script 'visualizar_auditoria.py' para consultar os logs")

if __name__ == '__main__':
    setup_audit_triggers()
