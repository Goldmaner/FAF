"""
Remove COMPLETAMENTE toda a infraestrutura de auditoria dos bancos
Execute: python remove_all_audit.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def limpar_banco(nome, host, database, user, password, port):
    """Remove tudo relacionado a auditoria de um banco"""
    print(f"\n{'='*80}")
    print(f"🧹 LIMPANDO BANCO: {nome}")
    print(f"{'='*80}\n")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # 1. Remover trigger
        print("1️⃣  Removendo triggers...")
        cur.execute("DROP TRIGGER IF EXISTS parcerias_despesas_audit ON Parcerias_Despesas CASCADE")
        print("   ✓ Trigger removido")
        
        # 2. Remover função
        print("2️⃣  Removendo função de trigger...")
        cur.execute("DROP FUNCTION IF EXISTS parcerias_despesas_audit_trigger() CASCADE")
        print("   ✓ Função removida")
        
        # 3. Remover foreign keys da tabela de auditoria (se existir)
        print("3️⃣  Removendo foreign keys...")
        try:
            cur.execute("""
                ALTER TABLE IF EXISTS parcerias_despesas_auditoria 
                DROP CONSTRAINT IF EXISTS parcerias_despesas_auditoria_parcerias_despesas_id_fkey CASCADE
            """)
            print("   ✓ FK parcerias_despesas_id removida")
        except Exception as e:
            print(f"   ⚠️  FK já estava removida ou tabela não existe")
        
        try:
            cur.execute("""
                ALTER TABLE IF EXISTS parcerias_despesas_auditoria 
                DROP CONSTRAINT IF EXISTS parcerias_despesas_auditoria_usuario_id_fkey CASCADE
            """)
            print("   ✓ FK usuario_id removida")
        except Exception as e:
            print(f"   ⚠️  FK usuário já estava removida")
        
        # 4. OPCIONALMENTE: Apagar a tabela de auditoria (descomente se quiser)
        print("4️⃣  Mantendo tabela de auditoria (os dados históricos ficam preservados)")
        # Descomente a linha abaixo se quiser APAGAR a tabela também:
        # cur.execute("DROP TABLE IF EXISTS parcerias_despesas_auditoria CASCADE")
        # print("   ✓ Tabela de auditoria removida")
        
        conn.close()
        print(f"\n✅ {nome} limpo com sucesso!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao limpar {nome}: {e}\n")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🗑️  REMOÇÃO COMPLETA DO SISTEMA DE AUDITORIA")
    print("="*80)
    
    # Limpar LOCAL
    limpar_banco(
        "LOCAL",
        os.getenv('DB_LOCAL_HOST'),
        os.getenv('DB_LOCAL_NAME'),
        os.getenv('DB_LOCAL_USER'),
        os.getenv('DB_LOCAL_PASSWORD'),
        os.getenv('DB_LOCAL_PORT', 5432)
    )
    
    # Limpar RAILWAY
    limpar_banco(
        "RAILWAY",
        os.getenv('DB_RAILWAY_HOST'),
        os.getenv('DB_RAILWAY_NAME'),
        os.getenv('DB_RAILWAY_USER'),
        os.getenv('DB_RAILWAY_PASSWORD'),
        os.getenv('DB_RAILWAY_PORT', 5432)
    )
    
    print("="*80)
    print("✅ LIMPEZA CONCLUÍDA!")
    print("="*80)
    print("\nAgora você pode testar o salvamento novamente.")
    print("Os dados históricos da auditoria foram preservados.\n")
