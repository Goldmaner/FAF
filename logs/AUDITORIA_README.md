# Sistema de Auditoria - Parcerias_Despesas

## 📋 Visão Geral

Sistema completo de auditoria automática para rastreamento de todas as modificações (INSERT, UPDATE, DELETE) na tabela `parcerias_despesas`. Utiliza triggers PostgreSQL para captura automática de dados e vinculação com usuários logados.

## 🗃️ Estrutura do Banco de Dados

### Tabela de Auditoria

```sql
CREATE TABLE parcerias_despesas_auditoria (
    id SERIAL PRIMARY KEY,
    parcerias_despesas_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    acao VARCHAR(20) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE'
    dados_anteriores JSONB,    -- os dados antigos, se houver
    dados_novos JSONB,         -- os dados novos, se houver
    data_modificacao TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    FOREIGN KEY (parcerias_despesas_id) REFERENCES parcerias_despesas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
```

### Campos Importantes

- **parcerias_despesas_id**: ID do registro modificado
- **usuario_id**: ID do usuário que fez a modificação (FK para tabela `usuarios`)
- **acao**: Tipo de operação (`INSERT`, `UPDATE`, `DELETE`)
- **dados_anteriores**: Snapshot completo do registro ANTES da modificação (JSON)
- **dados_novos**: Snapshot completo do registro DEPOIS da modificação (JSON)
- **data_modificacao**: Timestamp da modificação

## 🚀 Instalação e Configuração

### 1. Executar Setup de Triggers

Execute o script para criar as funções e triggers no PostgreSQL:

```bash
cd "c:\Users\d843702\OneDrive - rede.sp\Área de Trabalho\FAF\FAF"
python logs/setup_auditoria.py
```

Este script:
- ✅ Cria a função `parcerias_despesas_audit_trigger()` no PostgreSQL
- ✅ Cria o trigger que executa AFTER INSERT/UPDATE/DELETE
- ✅ Configura em ambos os bancos (LOCAL e RAILWAY)

### 2. Verificar Integração

O sistema já está integrado nas seguintes rotas:

**routes/despesas.py:**
- `criar_despesa()` - Captura INSERT/DELETE ao salvar orçamento
- `confirmar_despesa()` - Captura INSERT/DELETE ao confirmar orçamento

**routes/orcamento.py:**
- `atualizar_categoria()` - Captura UPDATE ao modificar categorias em massa

## 📊 Como Usar

### Modo Interativo (Menu)

```bash
python logs/visualizar_auditoria.py
```

Menu com opções:
1. Ver estatísticas gerais
2. Ver últimas modificações (50)
3. Filtrar por usuário
4. Filtrar por data
5. Filtrar por ação (INSERT/UPDATE/DELETE)
6. Filtrar por número do termo
7. Consulta personalizada

### Modo Linha de Comando

```bash
# Ver estatísticas
python logs/visualizar_auditoria.py --stats

# Ver ajuda
python logs/visualizar_auditoria.py --help
```

### Uso Programático (Python)

```python
from logs.visualizar_auditoria import visualizar_auditoria, estatisticas_auditoria

# Ver últimas 100 modificações
visualizar_auditoria(limite=100)

# Filtrar por usuário
visualizar_auditoria(usuario_email='joao@prefeitura.sp.gov.br')

# Filtrar por data (últimos 7 dias)
from datetime import datetime, timedelta
visualizar_auditoria(data_inicio=datetime.now() - timedelta(days=7))

# Filtrar por tipo de ação
visualizar_auditoria(acao='UPDATE')

# Filtrar por termo
visualizar_auditoria(numero_termo='TFM/190/2024')

# Consulta combinada
visualizar_auditoria(
    usuario_email='maria',
    data_inicio=datetime.now() - timedelta(days=30),
    acao='DELETE',
    limite=20
)

# Ver estatísticas
estatisticas_auditoria()
```

## 🔍 Exemplos de Saída

### Visualização de Modificações

```
================================================================================
📊 AUDITORIA DE PARCERIAS_DESPESAS
================================================================================
👤 Usuário: jeffersonluiz@prefeitura.sp.gov.br
📋 Limite: 50 registros
================================================================================

✅ 3 registro(s) encontrado(s):

1. ✏️ UPDATE - ID Auditoria: 42
   📄 Termo: TFM/190/2024/SMDHC/FUMCAD
   🆔 Despesa ID: 23
   👤 Usuário: jeffersonluiz@prefeitura.sp.gov.br (Agente Público)
   🕐 Data: 14/10/2025 12:35:11
      ✏️  MUDANÇAS:
         • valor:
             DE: 2117.52
             PARA: 2217.52
         • mes:
             DE: 1
             PARA: 2

2. ➕ INSERT - ID Auditoria: 23
   📄 Termo: TFM/190/2024/SMDHC/FUMCAD
   🆔 Despesa ID: 22
   👤 Usuário: jeffersonluiz@prefeitura.sp.gov.br (Agente Público)
   🕐 Data: 14/10/2025 12:35:11
      📝 NOVO REGISTRO:
         • numero_termo: TFM/190/2024/SMDHC/FUMCAD
         • rubrica: Pessoal
         • quantidade: 1
         • categoria_despesa: Assistente de Comunicação
         • valor: 2217.52
         • mes: 1
         • aditivo: 0
```

### Estatísticas

```
================================================================================
📊 ESTATÍSTICAS DE AUDITORIA
================================================================================

📈 RESUMO GERAL:
   • Total de ações registradas: 156
   • Usuários únicos: 2
   • Despesas modificadas: 45
   • Inserções: 122
   • Atualizações: 12
   • Exclusões: 22
   • Primeira modificação: 24/09/2025 15:13:58
   • Última modificação: 20/10/2025 17:39:44

👥 TOP 5 USUÁRIOS MAIS ATIVOS:
   1. jeffersonluiz@prefeitura.sp.gov.br (Agente Público) - 145 ações
   2. mmteixeira@prefeitura.sp.gov.br (OSC) - 11 ações
```

## 🔧 Como Funciona

### 1. Trigger Automático

Quando qualquer operação é executada em `parcerias_despesas`:

```sql
-- INSERT: Captura os dados novos
-- UPDATE: Captura dados anteriores E novos (para comparação)
-- DELETE: Captura os dados anteriores
```

### 2. Vinculação com Usuário

O sistema usa uma variável de sessão PostgreSQL:

```python
# No código Python (antes de modificar dados)
set_audit_user(usuario_id)  # Configura o usuário na sessão

# No trigger PostgreSQL
v_usuario_id := current_setting('app.current_user_id')::INTEGER;
```

### 3. Armazenamento JSONB

Todos os dados são armazenados em formato JSON:

```json
{
  "id": 23,
  "numero_termo": "TFM/190/2024/SMDHC/FUMCAD",
  "rubrica": "Pessoal",
  "quantidade": 1,
  "categoria_despesa": "Assistente de Comunicação",
  "valor": 2217.52,
  "mes": 1,
  "aditivo": 0
}
```

## 📝 Casos de Uso

### 1. Rastrear Quem Modificou um Valor

```python
visualizar_auditoria(
    numero_termo='TFM/190/2024',
    acao='UPDATE'
)
```

### 2. Ver Todas as Ações de um Usuário

```python
visualizar_auditoria(
    usuario_email='maria@prefeitura.sp.gov.br'
)
```

### 3. Auditoria de Período

```python
from datetime import datetime, timedelta

# Últimos 30 dias
visualizar_auditoria(
    data_inicio=datetime.now() - timedelta(days=30)
)
```

### 4. Investigar Exclusões

```python
# Ver todos os DELETEs
visualizar_auditoria(acao='DELETE', limite=100)
```

### 5. Relatório de Atividades

```python
# Estatísticas gerais
estatisticas_auditoria()

# Atividades de hoje
visualizar_auditoria(
    data_inicio=datetime.now().replace(hour=0, minute=0, second=0)
)
```

## ⚠️ Considerações Importantes

### Performance

- ✅ Triggers são RÁPIDOS (executam em microsegundos)
- ✅ Dados JSONB são indexáveis e pesquisáveis
- ⚠️ Tabela de auditoria cresce indefinidamente (considere arquivamento periódico)

### Segurança

- ✅ Todos os logs são imutáveis (apenas INSERT)
- ✅ Vinculação obrigatória com usuário logado
- ✅ Timestamps automáticos
- ⚠️ Dados sensíveis são armazenados (considere criptografia se necessário)

### Manutenção

```sql
-- Limpar logs antigos (mais de 2 anos)
DELETE FROM parcerias_despesas_auditoria 
WHERE data_modificacao < NOW() - INTERVAL '2 years';

-- Arquivar logs antigos
INSERT INTO parcerias_despesas_auditoria_arquivo 
SELECT * FROM parcerias_despesas_auditoria 
WHERE data_modificacao < NOW() - INTERVAL '1 year';
```

## 🐛 Troubleshooting

### Problema: Auditoria não está capturando usuário

**Solução:** Verificar se `set_audit_user()` está sendo chamado antes das operações:

```python
# ❌ ERRADO
execute_dual(query, params)

# ✅ CORRETO
set_audit_user(get_current_user_id())
execute_dual(query, params)
```

### Problema: Trigger não está funcionando

**Solução:** Re-executar o setup:

```bash
python logs/setup_auditoria.py
```

### Problema: Erro "current_setting não existe"

**Solução:** O trigger tem fallback automático para `usuario_id = 1` (sistema)

## 📚 Arquivos do Sistema

```
logs/
├── setup_auditoria.py           # Script de instalação dos triggers
├── visualizar_auditoria.py      # Script de consulta e visualização
└── AUDITORIA_README.md          # Esta documentação
```

## 🎯 Próximos Passos

- [ ] Dashboard web para visualizar auditoria
- [ ] Exportação de relatórios em PDF/Excel
- [ ] Notificações automáticas para ações críticas
- [ ] Integração com sistema de alertas
- [ ] API REST para consulta de auditoria

---

**Desenvolvido em:** 20/10/2025  
**Versão:** 1.0.0
