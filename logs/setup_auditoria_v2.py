"""
Script para configurar sistema de auditoria com SET LOCAL
Execute: python logs/setup_auditoria_v2.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# SQL do trigger correto
TRIGGER_SQL = """
-- 1. Remover trigger e função antigos, se existirem
DROP TRIGGER IF EXISTS parcerias_despesas_audit_trigger ON "Parcerias_Despesas";
DROP FUNCTION IF EXISTS parcerias_despesas_audit_trigger();

-- 2. Criar a função de auditoria usando variável de sessão para o usuário
CREATE OR REPLACE FUNCTION parcerias_despesas_audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_usuario_id INTEGER;
BEGIN
    BEGIN
        v_usuario_id := current_setting('app.current_user_id')::integer;
    EXCEPTION WHEN others THEN
        RAISE EXCEPTION 'Variável de sessão app.current_user_id não está definida. Use SET LOCAL app.current_user_id = ... antes do comando DML.';
    END;

    IF TG_OP = 'DELETE' THEN
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
    ELSIF TG_OP = 'INSERT' THEN
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
    ELSIF TG_OP = 'UPDATE' THEN
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
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 3. Criar o trigger
CREATE TRIGGER parcerias_despesas_audit_trigger
    BEFORE INSERT OR UPDATE OR DELETE
    ON "Parcerias_Despesas"
    FOR EACH ROW
    EXECUTE FUNCTION parcerias_despesas_audit_trigger();
"""

def setup_trigger(nome, host, database, user, password, port):
    """Instala o trigger de auditoria em um banco"""
    print(f"\n{'='*80}")
    print(f"📍 Configurando auditoria no banco: {nome}")
    print(f"{'='*80}\n")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        conn.autocommit = False
        cur = conn.cursor()
        
        print("1️⃣  Executando SQL do trigger...")
        cur.execute(TRIGGER_SQL)
        conn.commit()
        print("   ✓ Trigger criado com sucesso")
        
        # Verificar se funcionou
        cur.execute("""
            SELECT tgname 
            FROM pg_trigger 
            WHERE tgname = 'parcerias_despesas_audit_trigger'
        """)
        result = cur.fetchone()
        
        if result:
            print(f"   ✓ Trigger verificado: {result[0]}")
        else:
            print("   ⚠️  Trigger não encontrado após criação")
        
        conn.close()
        print(f"\n✅ {nome} configurado com sucesso!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao configurar {nome}: {e}\n")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔧 INSTALAÇÃO DO SISTEMA DE AUDITORIA V2")
    print("="*80)
    print("\n⚠️  IMPORTANTE: Este trigger requer SET LOCAL antes de qualquer DML!")
    print("   Exemplo: BEGIN; SET LOCAL app.current_user_id = '123'; INSERT...; COMMIT;\n")
    
    # Setup LOCAL
    setup_trigger(
        "LOCAL",
        os.getenv('DB_LOCAL_HOST'),
        os.getenv('DB_LOCAL_NAME'),
        os.getenv('DB_LOCAL_USER'),
        os.getenv('DB_LOCAL_PASSWORD'),
        os.getenv('DB_LOCAL_PORT', 5432)
    )
    
    # Setup RAILWAY
    setup_trigger(
        "RAILWAY",
        os.getenv('DB_RAILWAY_HOST'),
        os.getenv('DB_RAILWAY_NAME'),
        os.getenv('DB_RAILWAY_USER'),
        os.getenv('DB_RAILWAY_PASSWORD'),
        os.getenv('DB_RAILWAY_PORT', 5432)
    )
    
    print("="*80)
    print("✅ INSTALAÇÃO CONCLUÍDA!")
    print("="*80)
    print("\n📝 Próximo passo: Modificar o código Python para usar transações com SET LOCAL\n")
