-- Tabela de Categorias
CREATE TABLE IF NOT EXISTS categorias (
    nome TEXT PRIMARY KEY
);

-- Tabela de Transações
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data DATE NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('Receita', 'Despesa')),
    descricao TEXT NOT NULL,
    categoria TEXT NOT NULL,
    valor REAL NOT NULL,
    FOREIGN KEY (categoria) REFERENCES categorias(nome)
);

-- Tabela de Orçamentos
CREATE TABLE IF NOT EXISTS orcamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    valor_limite REAL NOT NULL,
    mes INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    ano INTEGER NOT NULL,
    FOREIGN KEY (categoria) REFERENCES categorias(nome),
    UNIQUE(categoria, mes, ano)
);

-- Tabela de Metas Financeiras
CREATE TABLE IF NOT EXISTS metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descricao TEXT NOT NULL,
    valor_alvo REAL NOT NULL,
    valor_atual REAL NOT NULL DEFAULT 0,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    CHECK (data_fim >= data_inicio),
    CHECK (valor_alvo > 0),
    CHECK (valor_atual >= 0)
);

-- Inserir algumas categorias padrão
INSERT OR IGNORE INTO categorias (nome) VALUES
    ('Alimentação'),
    ('Moradia'),
    ('Transporte'),
    ('Saúde'),
    ('Educação'),
    ('Lazer'),
    ('Vestuário'),
    ('Outros');
