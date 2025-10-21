"""
Script para visualizar e consultar logs de auditoria da tabela parcerias_despesas
Permite filtrar por usuário, data, ação e visualizar mudanças
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG_LOCAL
import json

def get_connection():
    """Obtém conexão direta com o banco LOCAL"""
    return psycopg2.connect(**DB_CONFIG_LOCAL)

def formatar_valor(valor):
    """Formata valores para exibição legível"""
    if valor is None:
        return "[NULL]"
    if isinstance(valor, (int, float)):
        return str(valor)
    if isinstance(valor, str):
        return valor
    return str(valor)

def exibir_mudancas(dados_anteriores, dados_novos):
    """Compara e exibe as mudanças entre dois registros"""
    if not dados_anteriores and dados_novos:
        print("      📝 NOVO REGISTRO:")
        for chave, valor in dados_novos.items():
            if chave not in ['id', 'criado_em']:  # Ignorar campos técnicos
                print(f"         • {chave}: {formatar_valor(valor)}")
        return
    
    if dados_anteriores and not dados_novos:
        print("      🗑️  REGISTRO EXCLUÍDO:")
        for chave, valor in dados_anteriores.items():
            if chave not in ['id', 'criado_em']:
                print(f"         • {chave}: {formatar_valor(valor)}")
        return
    
    if dados_anteriores and dados_novos:
        print("      ✏️  MUDANÇAS:")
        mudancas = []
        
        # Comparar todos os campos
        todas_chaves = set(dados_anteriores.keys()) | set(dados_novos.keys())
        for chave in todas_chaves:
            if chave in ['id', 'criado_em']:  # Ignorar campos técnicos
                continue
            
            valor_antigo = dados_anteriores.get(chave)
            valor_novo = dados_novos.get(chave)
            
            if valor_antigo != valor_novo:
                mudancas.append({
                    'campo': chave,
                    'antigo': valor_antigo,
                    'novo': valor_novo
                })
        
        if not mudancas:
            print("         (Nenhuma mudança detectada nos dados)")
        else:
            for m in mudancas:
                print(f"         • {m['campo']}:")
                print(f"             DE: {formatar_valor(m['antigo'])}")
                print(f"             PARA: {formatar_valor(m['novo'])}")

def visualizar_auditoria(
    usuario_email=None,
    data_inicio=None,
    data_fim=None,
    acao=None,
    numero_termo=None,
    limite=50
):
    """
    Visualiza logs de auditoria com filtros opcionais
    
    Args:
        usuario_email: Email do usuário (opcional)
        data_inicio: Data inicial (datetime, opcional)
        data_fim: Data final (datetime, opcional)
        acao: Tipo de ação - 'INSERT', 'UPDATE', 'DELETE' (opcional)
        numero_termo: Número do termo para filtrar (opcional)
        limite: Número máximo de registros (padrão: 50)
    """
    
    query = """
        SELECT 
            a.id,
            a.parcerias_despesas_id,
            a.acao,
            a.dados_anteriores,
            a.dados_novos,
            a.data_modificacao,
            u.email as usuario_email,
            u.tipo_usuario,
            pd.numero_termo
        FROM parcerias_despesas_auditoria a
        INNER JOIN usuarios u ON a.usuario_id = u.id
        LEFT JOIN parcerias_despesas pd ON a.parcerias_despesas_id = pd.id
        WHERE 1=1
    """
    
    params = []
    param_count = 1
    
    if usuario_email:
        query += f" AND u.email ILIKE ${param_count}"
        params.append(f"%{usuario_email}%")
        param_count += 1
    
    if data_inicio:
        query += f" AND a.data_modificacao >= ${param_count}"
        params.append(data_inicio)
        param_count += 1
    
    if data_fim:
        query += f" AND a.data_modificacao <= ${param_count}"
        params.append(data_fim)
        param_count += 1
    
    if acao:
        query += f" AND a.acao = ${param_count}"
        params.append(acao.upper())
        param_count += 1
    
    if numero_termo:
        query += f" AND pd.numero_termo ILIKE ${param_count}"
        params.append(f"%{numero_termo}%")
        param_count += 1
    
    query += f" ORDER BY a.data_modificacao DESC LIMIT ${param_count}"
    params.append(limite)
    
    # Substituir placeholders PostgreSQL por %s para psycopg2
    for i in range(len(params), 0, -1):
        query = query.replace(f"${i}", "%s")
    
    print("\n" + "="*80)
    print("📊 AUDITORIA DE PARCERIAS_DESPESAS")
    print("="*80)
    
    if usuario_email:
        print(f"👤 Usuário: {usuario_email}")
    if data_inicio:
        print(f"📅 Data início: {data_inicio.strftime('%d/%m/%Y %H:%M')}")
    if data_fim:
        print(f"📅 Data fim: {data_fim.strftime('%d/%m/%Y %H:%M')}")
    if acao:
        print(f"🔧 Ação: {acao}")
    if numero_termo:
        print(f"📄 Termo: {numero_termo}")
    
    print(f"📋 Limite: {limite} registros")
    print("="*80 + "\n")
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute(query, params)
        registros = cur.fetchall()
        
        if not registros:
            print("❌ Nenhum registro de auditoria encontrado com os filtros especificados.\n")
            cur.close()
            conn.close()
            return
        
        print(f"✅ {len(registros)} registro(s) encontrado(s):\n")
        
        for idx, reg in enumerate(registros, 1):
            audit_id, despesa_id, acao_tipo, dados_ant, dados_nov, data_mod, email, tipo_usr, num_termo = reg
            
            # Ícone baseado na ação
            icone = "➕" if acao_tipo == "INSERT" else "✏️" if acao_tipo == "UPDATE" else "🗑️"
            
            print(f"{idx}. {icone} {acao_tipo} - ID Auditoria: {audit_id}")
            print(f"   📄 Termo: {num_termo or '[Registro deletado]'}")
            print(f"   🆔 Despesa ID: {despesa_id}")
            print(f"   👤 Usuário: {email} ({tipo_usr})")
            print(f"   🕐 Data: {data_mod.strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Exibir mudanças
            exibir_mudancas(dados_ant, dados_nov)
            
            print()
        
        print("="*80 + "\n")
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"\n❌ Erro ao consultar auditoria: {e}\n")
        import traceback
        traceback.print_exc()

def estatisticas_auditoria():
    """Exibe estatísticas gerais da auditoria"""
    
    query_stats = """
        SELECT 
            COUNT(*) as total_registros,
            COUNT(DISTINCT usuario_id) as total_usuarios,
            COUNT(DISTINCT parcerias_despesas_id) as total_despesas,
            COUNT(CASE WHEN acao = 'INSERT' THEN 1 END) as total_inserts,
            COUNT(CASE WHEN acao = 'UPDATE' THEN 1 END) as total_updates,
            COUNT(CASE WHEN acao = 'DELETE' THEN 1 END) as total_deletes,
            MIN(data_modificacao) as primeira_modificacao,
            MAX(data_modificacao) as ultima_modificacao
        FROM parcerias_despesas_auditoria
    """
    
    query_top_usuarios = """
        SELECT 
            u.email,
            u.tipo_usuario,
            COUNT(*) as total_acoes
        FROM parcerias_despesas_auditoria a
        INNER JOIN usuarios u ON a.usuario_id = u.id
        GROUP BY u.email, u.tipo_usuario
        ORDER BY total_acoes DESC
        LIMIT 5
    """
    
    print("\n" + "="*80)
    print("📊 ESTATÍSTICAS DE AUDITORIA")
    print("="*80 + "\n")
    
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Estatísticas gerais
        cur.execute(query_stats)
        stats = cur.fetchone()
        
        if stats and stats[0] > 0:
            total, usuarios, despesas, inserts, updates, deletes, primeira, ultima = stats
            
            print("📈 RESUMO GERAL:")
            print(f"   • Total de ações registradas: {total}")
            print(f"   • Usuários únicos: {usuarios}")
            print(f"   • Despesas modificadas: {despesas}")
            print(f"   • Inserções: {inserts}")
            print(f"   • Atualizações: {updates}")
            print(f"   • Exclusões: {deletes}")
            
            if primeira:
                print(f"   • Primeira modificação: {primeira.strftime('%d/%m/%Y %H:%M:%S')}")
            if ultima:
                print(f"   • Última modificação: {ultima.strftime('%d/%m/%Y %H:%M:%S')}")
            
            print("\n👥 TOP 5 USUÁRIOS MAIS ATIVOS:")
            cur.execute(query_top_usuarios)
            top_usuarios = cur.fetchall()
            
            for idx, (email, tipo, total_acoes) in enumerate(top_usuarios, 1):
                print(f"   {idx}. {email} ({tipo}) - {total_acoes} ações")
            
        else:
            print("❌ Nenhum registro de auditoria encontrado.\n")
        
        print("\n" + "="*80 + "\n")
        
        cur.close()
        conn.close()
    
    except Exception as e:
        print(f"\n❌ Erro ao consultar estatísticas: {e}\n")

# Menu interativo
def menu_principal():
    """Menu interativo para consultar auditoria"""
    
    while True:
        print("\n" + "="*80)
        print("🔍 SISTEMA DE AUDITORIA - PARCERIAS_DESPESAS")
        print("="*80)
        print("\nEscolha uma opção:")
        print("  1. Ver estatísticas gerais")
        print("  2. Ver últimas modificações (50)")
        print("  3. Filtrar por usuário")
        print("  4. Filtrar por data")
        print("  5. Filtrar por ação (INSERT/UPDATE/DELETE)")
        print("  6. Filtrar por número do termo")
        print("  7. Consulta personalizada")
        print("  0. Sair")
        print()
        
        opcao = input("Digite o número da opção: ").strip()
        
        if opcao == "0":
            print("\n👋 Até logo!\n")
            break
        
        elif opcao == "1":
            estatisticas_auditoria()
        
        elif opcao == "2":
            visualizar_auditoria(limite=50)
        
        elif opcao == "3":
            email = input("Digite o email do usuário (ou parte dele): ").strip()
            visualizar_auditoria(usuario_email=email)
        
        elif opcao == "4":
            try:
                dias_atras = int(input("Quantos dias atrás deseja consultar? (ex: 7): ").strip())
                data_inicio = datetime.now() - timedelta(days=dias_atras)
                visualizar_auditoria(data_inicio=data_inicio)
            except ValueError:
                print("❌ Valor inválido!")
        
        elif opcao == "5":
            print("\nTipos de ação:")
            print("  1. INSERT (novos registros)")
            print("  2. UPDATE (atualizações)")
            print("  3. DELETE (exclusões)")
            tipo = input("Digite o número: ").strip()
            
            acoes = {"1": "INSERT", "2": "UPDATE", "3": "DELETE"}
            if tipo in acoes:
                visualizar_auditoria(acao=acoes[tipo])
            else:
                print("❌ Opção inválida!")
        
        elif opcao == "6":
            termo = input("Digite o número do termo (ou parte dele): ").strip()
            visualizar_auditoria(numero_termo=termo)
        
        elif opcao == "7":
            print("\n🔍 CONSULTA PERSONALIZADA")
            
            email = input("Email do usuário (Enter para ignorar): ").strip() or None
            termo = input("Número do termo (Enter para ignorar): ").strip() or None
            
            print("\nAção (Enter para ignorar):")
            print("  1. INSERT  2. UPDATE  3. DELETE")
            tipo = input("Digite o número: ").strip()
            acoes = {"1": "INSERT", "2": "UPDATE", "3": "DELETE"}
            acao = acoes.get(tipo)
            
            try:
                dias = input("Dias atrás (Enter para ignorar): ").strip()
                data_inicio = datetime.now() - timedelta(days=int(dias)) if dias else None
            except ValueError:
                data_inicio = None
            
            try:
                limite = int(input("Limite de registros (padrão 50): ").strip() or "50")
            except ValueError:
                limite = 50
            
            visualizar_auditoria(
                usuario_email=email,
                data_inicio=data_inicio,
                acao=acao,
                numero_termo=termo,
                limite=limite
            )
        
        else:
            print("❌ Opção inválida!")
        
        input("\nPressione Enter para continuar...")

if __name__ == '__main__':
    import sys
    
    # Se passar argumentos, usar modo não-interativo
    if len(sys.argv) > 1:
        if sys.argv[1] == '--stats':
            estatisticas_auditoria()
        elif sys.argv[1] == '--help':
            print("""
Uso: python visualizar_auditoria.py [opção]

Opções:
  (sem argumentos)  - Menu interativo
  --stats           - Exibir estatísticas gerais
  --help            - Exibir esta ajuda

Exemplos de uso programático:
  from logs.visualizar_auditoria import visualizar_auditoria, estatisticas_auditoria
  
  # Ver últimas 100 modificações
  visualizar_auditoria(limite=100)
  
  # Filtrar por usuário
  visualizar_auditoria(usuario_email='joao@example.com')
  
  # Filtrar por data
  from datetime import datetime, timedelta
  visualizar_auditoria(data_inicio=datetime.now() - timedelta(days=7))
  
  # Ver estatísticas
  estatisticas_auditoria()
            """)
        else:
            print(f"❌ Opção desconhecida: {sys.argv[1]}")
            print("Use --help para ver as opções disponíveis")
    else:
        # Menu interativo
        menu_principal()
