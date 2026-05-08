# =============================================================================
# database/connection.py — Gerenciamento da conexão com o Firebird
# =============================================================================
# Este módulo é responsável por TODA a comunicação com o banco de dados.
# Outros módulos nunca importam o firebird-driver diretamente — só usam
# as funções daqui. Isso facilita trocar o banco no futuro se necessário.
# =============================================================================

import re
import pandas as pd
from firebird.driver import connect
from config import DB_CONFIG


def _get_connection():
    """
    Cria e retorna uma conexão com o banco Firebird via TCP/IP.

    A conexão é feita usando a string de conexão no formato:
        host/porta:caminho_do_banco

    Returns:
        firebird.driver.Connection: objeto de conexão ativo

    Raises:
        Exception: se o banco estiver inacessível, senha errada, etc.
    """
    # Monta a string de conexão TCP: "192.168.25.73/3050:D:\...\VISAWORK.FDB"
    dsn = f"{DB_CONFIG['host']}/{DB_CONFIG['port']}:{DB_CONFIG['database']}"

    conexao = connect(
        dsn,
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        charset=DB_CONFIG["charset"],
    )
    return conexao


def _converter_para_posicional(sql: str, parametros: dict):
    """
    Converte parâmetros nomeados (:nome) para posicionais (?).

    O firebird-driver NÃO aceita dicionários com :nome diretamente.
    Ele exige parâmetros posicionais usando '?' na SQL e uma tupla de valores.

    Exemplo:
        SQL entrada : "WHERE cod = :pcodemp AND dat BETWEEN :pdatai AND :pdataf"
        SQL saída   : "WHERE cod = ?         AND dat BETWEEN ?       AND ?"
        Tupla saída : (1, '2024-01-01', '2024-12-31')

    A regex `:palavra` captura cada parâmetro nomeado na ordem em que aparece
    na SQL, garantindo que a tupla de valores siga a mesma ordem.
    """
    # Encontra todos os :nome_param na ordem em que aparecem na SQL
    nomes_ordenados = re.findall(r':([a-zA-Z_][a-zA-Z0-9_]*)', sql)

    # Substitui cada :nome por ? (marcador posicional do Firebird)
    sql_posicional = re.sub(r':[a-zA-Z_][a-zA-Z0-9_]*', '?', sql)

    # Monta a tupla de valores na mesma ordem dos marcadores ?
    try:
        valores = tuple(parametros[nome] for nome in nomes_ordenados)
    except KeyError as e:
        raise ValueError(
            f"Parâmetro {e} encontrado na SQL mas não fornecido no dicionário.\n"
            f"  Parâmetros na SQL : {nomes_ordenados}\n"
            f"  Parâmetros recebidos: {list(parametros.keys())}"
        )

    return sql_posicional, valores


def executar_query(sql: str, parametros: dict = None) -> pd.DataFrame:
    """
    Executa uma query SQL e retorna os resultados como DataFrame do pandas.

    O uso de DataFrame facilita MUITO a manipulação dos dados antes de
    passar para os gráficos Plotly.

    Args:
        sql (str): A query SQL. Use :nome_param para parâmetros nomeados.
                   Internamente, eles serão convertidos para ? (posicional).
        parametros (dict): Dicionário com os valores dos parâmetros.
                           Ex: {"pcodemp": 1, "pdatai": "2024-01-01", "pdataf": "2024-12-31"}

    Returns:
        pd.DataFrame: Tabela com os resultados. Vazia se não houver dados.

    Example:
        df = executar_query(
            "SELECT * FROM CLIENTE WHERE COD_EMP = :emp",
            {"emp": 1}
        )

    Notas importantes sobre o firebird-driver:
        - NÃO aceita dict com :nome diretamente (ao contrário de SQLAlchemy/psycopg2)
        - Usa marcadores POSICIONAIS: cursor.execute(sql, (val1, val2, ...))
        - Esta função faz a conversão automática para você
    """
    conexao = None
    try:
        conexao = _get_connection()
        cursor = conexao.cursor()

        if parametros:
            # Converte :nome → ? e dict → tupla ordenada
            sql_exec, valores = _converter_para_posicional(sql, parametros)
            cursor.execute(sql_exec, valores)
        else:
            cursor.execute(sql)

        # Pega os nomes das colunas direto do cursor (não precisa hardcodar)
        colunas = [desc[0] for desc in cursor.description]

        # Busca todas as linhas de uma vez
        linhas = cursor.fetchall()

        # Monta o DataFrame com colunas nomeadas
        df = pd.DataFrame(linhas, columns=colunas)

        return df

    except Exception as erro:
        # Log do erro para diagnóstico. Em produção, use logging ao invés de print.
        print(f"[ERRO] Falha na consulta ao banco de dados:")
        print(f"       {type(erro).__name__}: {erro}")
        # Retorna DataFrame vazio para não quebrar a interface
        return pd.DataFrame()

    finally:
        # SEMPRE fecha a conexão, mesmo se der erro
        # O bloco finally garante isso independente do que acontecer
        if conexao:
            conexao.close()


def testar_conexao() -> bool:
    """
    Testa se o banco está acessível. Útil para validar as configurações.

    Returns:
        bool: True se conectou com sucesso, False caso contrário.

    Usage:
        Chame esta função antes de rodar a aplicação:
        $ python -c "from database.connection import testar_conexao; testar_conexao()"
    """
    try:
        conn = _get_connection()
        conn.close()
        print("✅ Conexão com o banco de dados estabelecida com sucesso!")
        print(f"   Host    : {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"   Banco   : {DB_CONFIG['database']}")
        print(f"   Usuário : {DB_CONFIG['user']}")
        return True
    except Exception as erro:
        print("❌ Falha ao conectar com o banco de dados!")
        print(f"   Erro: {erro}")
        print("\nVerifique:")
        print("  1. O servidor Firebird está rodando?")
        print("  2. O IP e porta estão corretos no config.py?")
        print("  3. O caminho do .FDB está correto?")
        print("  4. Usuário e senha estão corretos?")
        print("  5. A porta 3050 está liberada no firewall?")
        return False