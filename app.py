from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Configuração do banco de dados
DATABASE = 'fin_assist.db'

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = dict_factory
    return db

def init_db():
    if not os.path.exists(DATABASE):
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# Rotas principais
@app.route('/')
def dashboard():
    db = get_db()
    now = datetime.now()
    mes_atual = now.month
    ano_atual = now.year

    # Obter resumo financeiro
    resumo = {
        'receitas': 0,
        'despesas': 0,
        'saldo': 0,
        'despesas_por_categoria': []
    }

    # Calcular receitas e despesas
    cursor = db.execute('''
        SELECT tipo, SUM(valor) as total
        FROM transacoes 
        WHERE strftime('%m', data) = ? AND strftime('%Y', data) = ?
        GROUP BY tipo
    ''', (f'{mes_atual:02d}', str(ano_atual)))
    
    for row in cursor:
        if row['tipo'] == 'Receita':
            resumo['receitas'] = row['total'] or 0
        else:
            resumo['despesas'] = row['total'] or 0
    
    resumo['saldo'] = resumo['receitas'] - resumo['despesas']

    # Calcular despesas por categoria
    cursor = db.execute('''
        SELECT categoria, SUM(valor) as total
        FROM transacoes 
        WHERE tipo = 'Despesa' AND strftime('%m', data) = ? AND strftime('%Y', data) = ?
        GROUP BY categoria
    ''', (f'{mes_atual:02d}', str(ano_atual)))
    
    resumo['despesas_por_categoria'] = cursor.fetchall()

    # Obter orçamentos
    orcamentos = db.execute('''
        SELECT id, categoria, valor_limite, 
               COALESCE((SELECT SUM(valor) 
                        FROM transacoes 
                        WHERE categoria = o.categoria 
                        AND tipo = 'Despesa'
                        AND strftime('%m', data) = ? 
                        AND strftime('%Y', data) = ?), 0) as valor_atual
        FROM orcamentos o
        WHERE mes = ? AND ano = ?
    ''', (f'{mes_atual:02d}', str(ano_atual), mes_atual, ano_atual)).fetchall()

    # Obter metas
    metas = db.execute('''
        SELECT id, descricao, valor_alvo, valor_atual, data_inicio, data_fim,
               CASE 
                   WHEN valor_atual >= valor_alvo THEN 'Concluída'
                   ELSE 'Em Andamento'
               END as status
        FROM metas
        ORDER BY data_fim ASC
    ''').fetchall()

    # Obter últimas transações
    transacoes = db.execute('''
        SELECT id, 
               strftime('%d/%m/%Y', data) as data_formatada,
               tipo, descricao, categoria, valor
        FROM transacoes
        ORDER BY data DESC, id DESC
        LIMIT 5
    ''').fetchall()

    return render_template('dashboard.html',
                         now=now,
                         resumo=resumo,
                         orcamentos=orcamentos,
                         metas=metas,
                         transacoes=transacoes)

@app.route('/transactions')
def transactions():
    db = get_db()
    tipo = request.args.get('tipo')
    categoria = request.args.get('categoria')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')

    query = '''
        SELECT id, 
               strftime('%d/%m/%Y', data) as data_formatada,
               tipo, descricao, categoria, valor 
        FROM transacoes 
        WHERE 1=1
    '''
    params = []

    if tipo:
        query += ' AND tipo = ?'
        params.append(tipo)
    if categoria:
        query += ' AND categoria = ?'
        params.append(categoria)
    if data_inicio:
        query += ' AND data >= ?'
        params.append(data_inicio)
    if data_fim:
        query += ' AND data <= ?'
        params.append(data_fim)

    query += ' ORDER BY data DESC, id DESC'
    
    transacoes = db.execute(query, params).fetchall()
    categorias = db.execute('SELECT DISTINCT nome FROM categorias ORDER BY nome').fetchall()

    return render_template('transactions.html',
                         transacoes=transacoes,
                         categorias=[cat['nome'] for cat in categorias])

@app.route('/budgets')
def budgets():
    db = get_db()
    now = datetime.now()
    mes_atual = now.month
    ano_atual = now.year

    orcamentos = db.execute('''
        SELECT id, categoria, valor_limite, 
               COALESCE((SELECT SUM(valor) 
                        FROM transacoes 
                        WHERE categoria = o.categoria 
                        AND tipo = 'Despesa'
                        AND strftime('%m', data) = ? 
                        AND strftime('%Y', data) = ?), 0) as valor_atual
        FROM orcamentos o
        WHERE mes = ? AND ano = ?
    ''', (f'{mes_atual:02d}', str(ano_atual), mes_atual, ano_atual)).fetchall()

    categorias = db.execute('SELECT DISTINCT nome FROM categorias ORDER BY nome').fetchall()

    return render_template('budgets.html',
                         orcamentos=orcamentos,
                         categorias=[cat['nome'] for cat in categorias],
                         mes_atual=mes_atual,
                         ano_atual=ano_atual)

@app.route('/goals')
def goals():
    db = get_db()
    metas = db.execute('''
        SELECT id, descricao, valor_alvo, valor_atual, data_inicio, data_fim,
               CASE 
                   WHEN valor_atual >= valor_alvo THEN 'Concluída'
                   ELSE 'Em Andamento'
               END as status
        FROM metas
        ORDER BY data_fim ASC
    ''').fetchall()

    return render_template('goals.html', metas=metas)

@app.route('/categories')
def categories():
    db = get_db()
    categorias = db.execute('SELECT nome FROM categorias ORDER BY nome').fetchall()
    
    # Calcular estatísticas para cada categoria
    estatisticas = {}
    for cat in categorias:
        nome = cat['nome']
        stats = db.execute('''
            SELECT COUNT(*) as total, SUM(valor) as valor
            FROM transacoes
            WHERE categoria = ?
        ''', (nome,)).fetchone()
        
        estatisticas[nome] = {
            'total': stats['total'],
            'valor': stats['valor'] or 0
        }

    return render_template('categories.html',
                         categorias=[cat['nome'] for cat in categorias],
                         estatisticas=estatisticas)

# Rotas para adicionar dados
@app.route('/adicionar_transacao', methods=['POST'])
def adicionar_transacao():
    db = get_db()
    try:
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        valor = float(request.form['valor'].replace('.', '').replace(',', '.'))
        data = request.form['data']

        db.execute('''
            INSERT INTO transacoes (data, tipo, descricao, categoria, valor)
            VALUES (?, ?, ?, ?, ?)
        ''', (data, tipo, descricao, categoria, valor))
        db.commit()
        flash('Transação adicionada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar transação: {str(e)}', 'error')
    
    return redirect(url_for('transactions'))

@app.route('/adicionar_orcamento', methods=['POST'])
def adicionar_orcamento():
    db = get_db()
    try:
        categoria = request.form['categoria']
        valor_limite = float(request.form['valor_limite'].replace('.', '').replace(',', '.'))
        mes = int(request.form['mes'])
        ano = int(request.form['ano'])

        db.execute('''
            INSERT INTO orcamentos (categoria, valor_limite, mes, ano)
            VALUES (?, ?, ?, ?)
        ''', (categoria, valor_limite, mes, ano))
        db.commit()
        flash('Orçamento adicionado com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar orçamento: {str(e)}', 'error')
    
    return redirect(url_for('budgets'))

@app.route('/adicionar_meta', methods=['POST'])
def adicionar_meta():
    db = get_db()
    try:
        descricao = request.form['descricao']
        valor_alvo = float(request.form['valor_alvo'].replace('.', '').replace(',', '.'))
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']

        db.execute('''
            INSERT INTO metas (descricao, valor_alvo, valor_atual, data_inicio, data_fim)
            VALUES (?, ?, 0, ?, ?)
        ''', (descricao, valor_alvo, data_inicio, data_fim))
        db.commit()
        flash('Meta adicionada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar meta: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

@app.route('/adicionar_categoria', methods=['POST'])
def adicionar_categoria():
    db = get_db()
    try:
        nome = request.form['nome']
        db.execute('INSERT INTO categorias (nome) VALUES (?)', (nome,))
        db.commit()
        flash('Categoria adicionada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao adicionar categoria: {str(e)}', 'error')
    
    return redirect(url_for('categories'))

# Rotas para atualizar dados
@app.route('/atualizar_meta/<int:id>', methods=['POST'])
def atualizar_meta(id):
    db = get_db()
    try:
        descricao = request.form['descricao']
        valor_alvo = float(request.form['valor_alvo'].replace('.', '').replace(',', '.'))
        valor_atual = float(request.form['valor_atual'].replace('.', '').replace(',', '.'))
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']
        status = request.form['status']

        db.execute('''
            UPDATE metas 
            SET descricao = ?, valor_alvo = ?, valor_atual = ?, 
                data_inicio = ?, data_fim = ?
            WHERE id = ?
        ''', (descricao, valor_alvo, valor_atual, data_inicio, data_fim, id))
        db.commit()
        flash('Meta atualizada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar meta: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

@app.route('/atualizar_categoria/<nome>', methods=['POST'])
def atualizar_categoria(nome):
    db = get_db()
    try:
        novo_nome = request.form['novo_nome']
        db.execute('UPDATE categorias SET nome = ? WHERE nome = ?', (novo_nome, nome))
        db.execute('UPDATE transacoes SET categoria = ? WHERE categoria = ?', (novo_nome, nome))
        db.execute('UPDATE orcamentos SET categoria = ? WHERE categoria = ?', (novo_nome, nome))
        db.commit()
        flash('Categoria atualizada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar categoria: {str(e)}', 'error')
    
    return redirect(url_for('categories'))

# Rotas para excluir dados
@app.route('/excluir_transacao/<int:id>', methods=['POST'])
def excluir_transacao(id):
    db = get_db()
    try:
        db.execute('DELETE FROM transacoes WHERE id = ?', (id,))
        db.commit()
        flash('Transação excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir transação: {str(e)}', 'error')
    
    return redirect(url_for('transactions'))

@app.route('/excluir_orcamento/<int:id>', methods=['POST'])
def excluir_orcamento(id):
    db = get_db()
    try:
        db.execute('DELETE FROM orcamentos WHERE id = ?', (id,))
        db.commit()
        flash('Orçamento excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir orçamento: {str(e)}', 'error')
    
    return redirect(url_for('budgets'))

@app.route('/excluir_meta/<int:id>', methods=['POST'])
def excluir_meta(id):
    db = get_db()
    try:
        db.execute('DELETE FROM metas WHERE id = ?', (id,))
        db.commit()
        flash('Meta excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir meta: {str(e)}', 'error')
    
    return redirect(url_for('goals'))

@app.route('/excluir_categoria/<nome>', methods=['POST'])
def excluir_categoria(nome):
    db = get_db()
    try:
        db.execute('DELETE FROM categorias WHERE nome = ?', (nome,))
        db.commit()
        flash('Categoria excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir categoria: {str(e)}', 'error')
    
    return redirect(url_for('categories'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=8000)
