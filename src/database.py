import sqlite3
import logging
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_file="fin_assist.db"):
        """Inicializa o gerenciador de banco de dados."""
        self.db_file = db_file
        self._ensure_db_directory()
        self.init_database()

    def _ensure_db_directory(self):
        """Garante que o diretório do banco de dados existe."""
        db_dir = Path(self.db_file).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def init_database(self):
        """Inicializa o banco de dados e cria as tabelas necessárias."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Criar tabelas necessárias
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transacoes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tipo TEXT NOT NULL,
                        valor REAL NOT NULL,
                        data TEXT NOT NULL,
                        descricao TEXT,
                        categoria TEXT NOT NULL
                    )
                ''')
                
                # Criar tabela de orçamentos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orcamentos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        categoria TEXT NOT NULL,
                        valor_limite REAL NOT NULL,
                        mes INTEGER NOT NULL,
                        ano INTEGER NOT NULL,
                        UNIQUE(categoria, mes, ano)
                    )
                ''')
                
                # Criar tabela de metas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        descricao TEXT NOT NULL,
                        valor_alvo REAL NOT NULL,
                        valor_atual REAL DEFAULT 0,
                        data_inicio TEXT NOT NULL,
                        data_fim TEXT NOT NULL,
                        status TEXT DEFAULT 'Em Andamento'
                    )
                ''')
                
                # Criar tabela de categorias
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS categorias (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL UNIQUE
                    )
                ''')
                
                # Inserir categorias padrão se a tabela estiver vazia
                cursor.execute('SELECT COUNT(*) FROM categorias')
                if cursor.fetchone()[0] == 0:
                    categorias_padrao = [
                        ('Alimentação',),
                        ('Transporte',),
                        ('Moradia',),
                        ('Lazer',),
                        ('Saúde',),
                        ('Educação',),
                        ('Salário',),
                        ('Investimentos',),
                        ('Outros',)
                    ]
                    cursor.executemany('INSERT INTO categorias (nome) VALUES (?)', categorias_padrao)
                
                conn.commit()
                logging.info("Banco de dados inicializado com sucesso!")
                
        except sqlite3.Error as e:
            logging.error(f"Erro ao inicializar o banco de dados: {e}")
            raise

    def execute_query(self, query, parameters=None):
        """Executa uma query SQL com parâmetros opcionais."""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            logging.error(f"Erro ao executar query: {e}")
            raise

    def fetch_all(self, query, parameters=None):
        """Executa uma query SELECT e retorna todos os resultados."""
        cursor = self.execute_query(query, parameters)
        return cursor.fetchall()

    def fetch_one(self, query, parameters=None):
        """Executa uma query SELECT e retorna um resultado."""
        cursor = self.execute_query(query, parameters)
        return cursor.fetchone()

    def insert(self, query, parameters=None):
        """Insere dados no banco e retorna o ID do último registro."""
        cursor = self.execute_query(query, parameters)
        return cursor.lastrowid

    def get_categorias(self):
        """Retorna todas as categorias cadastradas."""
        return self.fetch_all("SELECT nome FROM categorias ORDER BY nome")

    def add_transacao(self, tipo, valor, data, descricao, categoria):
        """Adiciona uma nova transação ao banco de dados."""
        query = '''
            INSERT INTO transacoes (tipo, valor, data, descricao, categoria)
            VALUES (?, ?, ?, ?, ?)
        '''
        return self.insert(query, (tipo, valor, data, descricao, categoria))

    def get_transacoes(self):
        """Retorna todas as transações ordenadas por data."""
        return self.fetch_all('''
            SELECT id, tipo, valor, data, descricao, categoria
            FROM transacoes
            ORDER BY data DESC
        ''')

    def update_transacao(self, id, tipo, valor, data, descricao, categoria):
        """Atualiza uma transação existente."""
        query = '''
            UPDATE transacoes
            SET tipo = ?, valor = ?, data = ?, descricao = ?, categoria = ?
            WHERE id = ?
        '''
        self.execute_query(query, (tipo, valor, data, descricao, categoria, id))

    def delete_transacao(self, id):
        """Remove uma transação do banco de dados."""
        self.execute_query("DELETE FROM transacoes WHERE id = ?", (id,))

    def get_resumo_financeiro(self):
        """Retorna o resumo financeiro (total de receitas e despesas)."""
        receitas = self.fetch_one('''
            SELECT COALESCE(SUM(valor), 0)
            FROM transacoes
            WHERE tipo = 'Receita'
        ''')[0]
        
        despesas = self.fetch_one('''
            SELECT COALESCE(SUM(valor), 0)
            FROM transacoes
            WHERE tipo = 'Despesa'
        ''')[0]
        
        # Buscar resumo por categoria do mês atual
        from datetime import datetime
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        despesas_por_categoria = self.fetch_all('''
            SELECT categoria, COALESCE(SUM(valor), 0) as total
            FROM transacoes
            WHERE tipo = 'Despesa'
            AND strftime('%m', data) = ?
            AND strftime('%Y', data) = ?
            GROUP BY categoria
        ''', (f"{mes_atual:02d}", str(ano_atual)))
        
        return {
            'receitas': receitas,
            'despesas': despesas,
            'saldo': receitas - despesas,
            'despesas_por_categoria': despesas_por_categoria
        }

    # Métodos para Orçamentos
    def add_orcamento(self, categoria, valor_limite, mes, ano):
        """Adiciona ou atualiza um orçamento."""
        try:
            self.execute_query('''
                INSERT INTO orcamentos (categoria, valor_limite, mes, ano)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(categoria, mes, ano)
                DO UPDATE SET valor_limite = ?
            ''', (categoria, valor_limite, mes, ano, valor_limite))
            return True
        except Exception as e:
            logging.error(f"Erro ao adicionar orçamento: {e}")
            return False

    def get_orcamentos(self, mes=None, ano=None):
        """Retorna os orçamentos para um mês/ano específico."""
        if mes is None:
            mes = datetime.now().month
        if ano is None:
            ano = datetime.now().year

        return self.fetch_all('''
            SELECT o.id, o.categoria, o.valor_limite,
                   COALESCE((
                       SELECT SUM(t.valor)
                       FROM transacoes t
                       WHERE t.categoria = o.categoria
                       AND strftime('%m', t.data) = ?
                       AND strftime('%Y', t.data) = ?
                       AND t.tipo = 'Despesa'
                   ), 0) as valor_atual
            FROM orcamentos o
            WHERE o.mes = ? AND o.ano = ?
        ''', (f"{mes:02d}", str(ano), mes, ano))

    def delete_orcamento(self, id):
        """Remove um orçamento."""
        self.execute_query("DELETE FROM orcamentos WHERE id = ?", (id,))

    # Métodos para Metas
    def add_meta(self, descricao, valor_alvo, data_inicio, data_fim):
        """Adiciona uma nova meta."""
        return self.insert('''
            INSERT INTO metas (descricao, valor_alvo, data_inicio, data_fim)
            VALUES (?, ?, ?, ?)
        ''', (descricao, valor_alvo, data_inicio, data_fim))

    def get_metas(self):
        """Retorna todas as metas."""
        return self.fetch_all('''
            SELECT id, descricao, valor_alvo, valor_atual, 
                   data_inicio, data_fim, status
            FROM metas
            ORDER BY data_fim
        ''')

    def update_meta(self, id, descricao, valor_alvo, valor_atual, data_inicio, data_fim, status):
        """Atualiza uma meta existente."""
        self.execute_query('''
            UPDATE metas
            SET descricao = ?, valor_alvo = ?, valor_atual = ?,
                data_inicio = ?, data_fim = ?, status = ?
            WHERE id = ?
        ''', (descricao, valor_alvo, valor_atual, data_inicio, data_fim, status, id))

    def delete_meta(self, id):
        """Remove uma meta."""
        self.execute_query("DELETE FROM metas WHERE id = ?", (id,))

    def atualizar_progresso_meta(self, id, valor_atual):
        """Atualiza o progresso de uma meta."""
        self.execute_query('''
            UPDATE metas
            SET valor_atual = ?,
                status = CASE 
                    WHEN ? >= valor_alvo THEN 'Concluída'
                    ELSE 'Em Andamento'
                END
            WHERE id = ?
        ''', (valor_atual, valor_atual, id))
