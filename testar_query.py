# =============================================================================
# testar_query.py — Script de diagnóstico da conexão e da query
# =============================================================================
# Execute com:  python testar_query.py
# Roda fora do Dash, mostra erros reais sem filtros da interface.
# =============================================================================

import sys
import re

# Tenta importar o driver
try:
    from firebird.driver import connect
    print("✅ firebird-driver importado com sucesso")
except ImportError as e:
    print(f"❌ Erro ao importar firebird-driver: {e}")
    sys.exit(1)

from config import DB_CONFIG

# -----------------------------------------------------------------------------
# 1. TESTE DE CONEXÃO
# -----------------------------------------------------------------------------
print("\n" + "="*60)
print("PASSO 1 — Testando conexão TCP com o Firebird")
print("="*60)

dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"
print(f"  DSN     : {dsn}")
print(f"  Usuário : {DB_CONFIG['user']}")
print(f"  Charset : {DB_CONFIG['charset']}")

try:
    con = connect(dsn, user=DB_CONFIG['user'],
                  password=DB_CONFIG['password'], charset=DB_CONFIG['charset'])
    print("✅ Conexão estabelecida!\n")
except Exception as e:
    print(f"❌ Falha na conexão: {e}")
    sys.exit(1)

# -----------------------------------------------------------------------------
# 2. TESTE COM QUERY SIMPLES — sem parâmetros, só conta registros
# -----------------------------------------------------------------------------
print("="*60)
print("PASSO 2 — Contando registros na tabela sainota")
print("="*60)

try:
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM sainota")
    total = cur.fetchone()[0]
    print(f"✅ Total de registros em sainota: {total}")
except Exception as e:
    print(f"❌ Erro ao acessar sainota: {e}")
    con.close()
    sys.exit(1)

# -----------------------------------------------------------------------------
# 3. VER QUAIS EMPRESAS E DATAS EXISTEM NO BANCO
# -----------------------------------------------------------------------------
print("\n" + "="*60)
print("PASSO 3 — Empresas e período de datas disponíveis")
print("="*60)

try:
    cur.execute("""
        SELECT cod_emp, COUNT(*) as qtd,
               MIN(dat_emi) as primeira, MAX(dat_emi) as ultima
        FROM sainota
        GROUP BY cod_emp
        ORDER BY cod_emp
    """)
    rows = cur.fetchall()
    if rows:
        print(f"  {'Coligada':<10} {'Qtd Notas':<12} {'Primeira Data':<16} {'Última Data'}")
        print(f"  {'-'*8:<10} {'-'*9:<12} {'-'*13:<16} {'-'*11}")
        for r in rows:
            print(f"  {str(r[0]):<10} {str(r[1]):<12} {str(r[2]):<16} {str(r[3])}")
    else:
        print("  ⚠️  Nenhum registro encontrado na tabela!")
except Exception as e:
    print(f"❌ Erro: {e}")

# -----------------------------------------------------------------------------
# 4. TESTE DA QUERY COMPLETA COM PARÂMETROS POSICIONAIS
# -----------------------------------------------------------------------------
print("\n" + "="*60)
print("PASSO 4 — Testando a query completa com parâmetros")
print("="*60)

# ⚠️  AJUSTE ESTES VALORES conforme o que você viu no PASSO 3
# ⚠️  cod_emp é string com zeros à esquerda no banco (ex: '001', não 1)
COLIGADA = "001"        # <— troque pelo cod_emp exato que apareceu no PASSO 3
DATA_INI = "2026-01-01"
DATA_FIM = "2026-05-08"

print(f"  Coligada : {COLIGADA}")
print(f"  De       : {DATA_INI}")
print(f"  Até      : {DATA_FIM}")

SQL = """
    SELECT
        s.cod_emp, s.codcli, s.noment, s.numped, s.nota,
        s.dat_emi, s.valor, s.codfun,
        funcionario.nomfun,
        s.cidendent,
        tipvenda.descricao,
        formapag.despag,
        tipoconta.destip,
        s.notcan
    FROM sainota s
    INNER JOIN tipvenda    ON tipvenda.codigo    = s.tipvenda
    INNER JOIN funcionario ON funcionario.codfun = s.codfun
    INNER JOIN formapag    ON formapag.codpag    = s.codpag
    INNER JOIN tipoconta   ON tipoconta.codtip   = s.codtip
    WHERE s.cod_emp = ?
      AND s.dat_emi BETWEEN ? AND ?
"""

try:
    cur.execute(SQL, (COLIGADA, DATA_INI, DATA_FIM))  # COLIGADA é string '001'
    rows = cur.fetchmany(5)  # Pega só as 5 primeiras para não poluir o terminal

    if rows:
        print(f"\n✅ Query retornou dados! Primeiras linhas:")
        colunas = [desc[0] for desc in cur.description]
        print("  " + " | ".join(colunas))
        print("  " + "-" * 80)
        for r in rows:
            print("  " + " | ".join(str(v) for v in r))
    else:
        print("\n⚠️  Query executou mas não retornou linhas.")
        print("    Verifique se a coligada e o período estão corretos (veja PASSO 3).")

except Exception as e:
    print(f"\n❌ Erro na query completa: {e}")
    print("\n--- Tentando query SEM os JOINs para isolar o problema ---")
    try:
        cur.execute(
            "SELECT COUNT(*) FROM sainota WHERE cod_emp = ? AND dat_emi BETWEEN ? AND ?",
            (COLIGADA, DATA_INI, DATA_FIM)
        )
        qtd = cur.fetchone()[0]
        print(f"  sainota isolada retornou: {qtd} registros")
        print("  → O problema está em um dos JOINs (tipvenda, funcionario, formapag ou tipoconta)")
        print("    Verifique se há registros sem par nas tabelas relacionadas.")
    except Exception as e2:
        print(f"  ❌ Erro mesmo sem JOINs: {e2}")

# -----------------------------------------------------------------------------
# 5. TESTE DO FORMATO DE DATA — o Firebird pode ser sensível ao formato
# -----------------------------------------------------------------------------
print("\n" + "="*60)
print("PASSO 5 — Verificando formato de data aceito pelo banco")
print("="*60)

formatos = [
    ("2026-01-01",              "string ISO (YYYY-MM-DD)"),
    ("01/01/2026",              "string BR (DD/MM/YYYY)"),
    ("01-JAN-2026",             "string Firebird clássico"),
]

from datetime import date as dt_date
formatos_python = [
    (dt_date(2026, 1, 1),  "objeto Python date"),
]

for val, descricao in formatos:
    try:
        cur.execute(
            "SELECT COUNT(*) FROM sainota WHERE cod_emp = ? AND dat_emi >= ?",
            (COLIGADA, val)
        )
        qtd = cur.fetchone()[0]
        print(f"  ✅ '{descricao}' aceito → {qtd} registros encontrados")
    except Exception as e:
        print(f"  ❌ '{descricao}' rejeitado: {e}")

for val, descricao in formatos_python:
    try:
        cur.execute(
            "SELECT COUNT(*) FROM sainota WHERE cod_emp = ? AND dat_emi >= ?",
            (COLIGADA, val)
        )
        qtd = cur.fetchone()[0]
        print(f"  ✅ '{descricao}' aceito → {qtd} registros encontrados")
    except Exception as e:
        print(f"  ❌ '{descricao}' rejeitado: {e}")

con.close()
print("\n" + "="*60)
print("Diagnóstico concluído. Compartilhe o resultado acima.")
print("="*60)
# teste extra
