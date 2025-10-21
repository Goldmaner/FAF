"""
Remove os triggers de auditoria dos bancos LOCAL e RAILWAY
Execute: python logs/remove_audit_triggers.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def remove_triggers():
    """Remove triggers e função de auditoria"""
    
    # Conectar ao banco LOCAL
    print("\n📍 Removendo triggers do banco LOCAL...")
    try:
        conn_local = psycopg2.connect(
            host=os.getenv('DB_LOCAL_HOST'),
            database=os.getenv('DB_LOCAL_NAME'),
            user=os.getenv('DB_LOCAL_USER'),
            password=os.getenv('DB_LOCAL_PASSWORD'),
            port=os.getenv('DB_LOCAL_PORT', 5432)
        )
        cur_local = conn_local.cursor()
        
        # Remover trigger
        cur_local.execute("DROP TRIGGER IF EXISTS parcerias_despesas_audit ON Parcerias_Despesas CASCADE")
        print("  ✓ Trigger removido")
        
        # Remover função
        cur_local.execute("DROP FUNCTION IF EXISTS parcerias_despesas_audit_trigger() CASCADE")
        print("  ✓ Função removida")
        
        # Remover foreign key da tabela de auditoria
        cur_local.execute("""
            ALTER TABLE parcerias_despesas_auditoria 
            DROP CONSTRAINT IF EXISTS parcerias_despesas_auditoria_parcerias_despesas_id_fkey CASCADE
        """)
        print("  ✓ Foreign key removida")
        
        conn_local.commit()
        conn_local.close()
        print("✅ Auditoria removida do banco LOCAL\n")
        
    except Exception as e:
        print(f"❌ Erro ao remover do LOCAL: {e}\n")
    
    # Conectar ao banco RAILWAY
    print("📍 Removendo triggers do banco RAILWAY...")
    try:
        conn_railway = psycopg2.connect(
            host=os.getenv('DB_RAILWAY_HOST'),
            database=os.getenv('DB_RAILWAY_NAME'),
            user=os.getenv('DB_RAILWAY_USER'),
            password=os.getenv('DB_RAILWAY_PASSWORD'),
            port=os.getenv('DB_RAILWAY_PORT', 5432)
        )
        cur_railway = conn_railway.cursor()
        
        # Remover trigger
        cur_railway.execute("DROP TRIGGER IF EXISTS parcerias_despesas_audit ON Parcerias_Despesas CASCADE")
        print("  ✓ Trigger removido")
        
        # Remover função
        cur_railway.execute("DROP FUNCTION IF EXISTS parcerias_despesas_audit_trigger() CASCADE")
        print("  ✓ Função removida")
        
        conn_railway.commit()
        conn_railway.close()
        print("✅ Auditoria removida do banco RAILWAY\n")
        
    except Exception as e:
        print(f"❌ Erro ao remover do RAILWAY: {e}\n")

if __name__ == "__main__":
    print("\n🧹 REMOVENDO SISTEMA DE AUDITORIA\n")
    print("="*80)
    remove_triggers()
    print("="*80)
    print("\n✅ Processo concluído!")
    print("\nAgora o salvamento deve funcionar normalmente.\n")
