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
                
                # Criar tabela de transações
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
        
        return {
            'receitas': receitas,
            'despesas': despesas,
            'saldo': receitas - despesas
        }
