"""
Script de teste simples para verificar conexões e salvamento nos bancos.
Execute: python test_save_simple.py
"""

import os
from db import get_db_local, get_db_railway, execute_dual

def test_connections():
    """Testa conexões com ambos os bancos"""
    print("\n" + "="*80)
    print("🔍 TESTANDO CONEXÕES")
    print("="*80)
    
    # Testar LOCAL
    try:
        db_local = get_db_local()
        if db_local:
            cur = db_local.cursor()
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            print("✅ LOCAL: Conectado com sucesso")
        else:
            print("❌ LOCAL: Falha ao conectar (None)")
    except Exception as e:
        print(f"❌ LOCAL: Erro - {e}")
    
    # Testar RAILWAY
    try:
        db_railway = get_db_railway()
        if db_railway:
            cur = db_railway.cursor()
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            print("✅ RAILWAY: Conectado com sucesso")
        else:
            print("❌ RAILWAY: Falha ao conectar (None)")
    except Exception as e:
        print(f"❌ RAILWAY: Erro - {e}")


def test_simple_insert():
    """Testa um INSERT simples usando execute_dual()"""
    print("\n" + "="*80)
    print("🔍 TESTANDO INSERT SIMPLES")
    print("="*80)
    
    # Criar tabela de teste se não existir
    try:
        # LOCAL
        db_local = get_db_local()
        if db_local:
            cur = db_local.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_save (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            db_local.commit()
            print("✅ Tabela test_save criada/verificada no LOCAL")
    except Exception as e:
        print(f"❌ Erro ao criar tabela no LOCAL: {e}")
    
    try:
        # RAILWAY
        db_railway = get_db_railway()
        if db_railway:
            cur = db_railway.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_save (
                    id SERIAL PRIMARY KEY,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
            db_railway.commit()
            print("✅ Tabela test_save criada/verificada no RAILWAY")
    except Exception as e:
        print(f"❌ Erro ao criar tabela no RAILWAY: {e}")
    
    # Tentar inserir um registro
    print("\n📝 Inserindo registro de teste...")
    try:
        result = execute_dual(
            "INSERT INTO test_save (data) VALUES (%s)",
            ("Teste de salvamento - " + str(os.getpid()),)
        )
        
        print(f"\n📊 Resultado do execute_dual:")
        print(f"   - success: {result['success']}")
        print(f"   - local: {result['local']}")
        print(f"   - railway: {result['railway']}")
        print(f"   - errors: {result['errors']}")
        
        if result['success']:
            bancos = []
            if result['local']: bancos.append("LOCAL")
            if result['railway']: bancos.append("RAILWAY")
            print(f"\n✅ INSERT bem-sucedido em: {', '.join(bancos)}")
        else:
            print(f"\n❌ INSERT falhou em ambos os bancos")
            
    except Exception as e:
        print(f"\n❌ Exceção durante INSERT: {e}")
        import traceback
        traceback.print_exc()


def test_parcerias_despesas():
    """Testa INSERT direto na tabela Parcerias_Despesas"""
    print("\n" + "="*80)
    print("🔍 TESTANDO INSERT EM Parcerias_Despesas")
    print("="*80)
    
    # Buscar um termo existente
    try:
        db = get_db_railway()
        cur = db.cursor()
        cur.execute("SELECT numero_termo FROM Parcerias LIMIT 1")
        termo = cur.fetchone()
        
        if not termo:
            print("❌ Nenhum termo encontrado na tabela Parcerias")
            return
        
        numero_termo = termo[0]
        print(f"📋 Usando termo: {numero_termo}")
        
        # Tentar inserir uma despesa de teste
        print("\n📝 Inserindo despesa de teste...")
        result = execute_dual(
            """INSERT INTO Parcerias_Despesas 
               (numero_termo, rubrica, quantidade, categoria_despesa, valor, mes, aditivo)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (numero_termo, "TESTE_RUBRICA", 1, "TESTE_CATEGORIA", 100.00, 1, 999)
        )
        
        print(f"\n📊 Resultado:")
        print(f"   - success: {result['success']}")
        print(f"   - local: {result['local']}")
        print(f"   - railway: {result['railway']}")
        print(f"   - errors: {result.get('errors', {})}")
        
        if result['success']:
            print("\n✅ INSERT em Parcerias_Despesas funcionou!")
            
            # Limpar o teste
            print("\n🧹 Limpando registro de teste...")
            execute_dual(
                "DELETE FROM Parcerias_Despesas WHERE aditivo = 999 AND rubrica = 'TESTE_RUBRICA'",
                None
            )
            print("✅ Teste limpo")
        else:
            print("\n❌ INSERT em Parcerias_Despesas falhou")
            
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🧪 INICIANDO TESTES DE SALVAMENTO\n")
    
    test_connections()
    test_simple_insert()
    test_parcerias_despesas()
    
    print("\n" + "="*80)
    print("✅ TESTES CONCLUÍDOS")
    print("="*80)
