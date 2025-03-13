from flask import Flask, request, redirect, url_for, render_template_string
from src.database import DatabaseManager
from src.models import Transacao, ResumoFinanceiro
from src.utils import validar_valor, validar_data, formatar_valor_monetario
from datetime import datetime
import logging

app = Flask(__name__)
db = DatabaseManager()

# Template HTML inline
TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fin Assist - Assistente Financeiro</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.5;
            background: #f5f5f5;
            color: #333;
        }
        .header {
            background: #4F46E5;
            color: white;
            padding: 1rem;
            margin-bottom: 2rem;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        .receita { color: #22c55e; }
        .despesa { color: #ef4444; }
        .form-section {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }
        .form-control {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        .btn {
            background: #4F46E5;
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1rem;
        }
        .btn:hover {
            background: #4338CA;
        }
        .table-container {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f8fafc;
            font-weight: 600;
        }
        .badge {
            padding: 0.25rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.875rem;
        }
        .badge-receita {
            background: #dcfce7;
            color: #166534;
        }
        .badge-despesa {
            background: #fee2e2;
            color: #991b1b;
        }
        .text-right {
            text-align: right;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <h1>Fin Assist</h1>
        </div>
    </header>

    <main class="container">
        <div class="dashboard">
            <div class="card">
                <div class="card-title">Receitas</div>
                <div class="receita">R$ {{ "%.2f"|format(resumo.receitas) }}</div>
            </div>
            <div class="card">
                <div class="card-title">Despesas</div>
                <div class="despesa">R$ {{ "%.2f"|format(resumo.despesas) }}</div>
            </div>
            <div class="card">
                <div class="card-title">Saldo</div>
                <div class="{{ 'receita' if resumo.saldo >= 0 else 'despesa' }}">
                    R$ {{ "%.2f"|format(resumo.saldo) }}
                </div>
            </div>
        </div>

        <div class="form-section">
            <h2 style="margin-bottom: 1.5rem;">Nova Transação</h2>
            <form action="{{ url_for('adicionar_transacao') }}" method="POST">
                <div class="form-grid">
                    <div class="form-group">
                        <label class="form-label">Tipo</label>
                        <select name="tipo" class="form-control" required>
                            <option value="Receita">Receita</option>
                            <option value="Despesa">Despesa</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Valor (R$)</label>
                        <input type="text" name="valor" class="form-control" required placeholder="0,00">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Data</label>
                        <input type="date" name="data" class="form-control" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Categoria</label>
                        <select name="categoria" class="form-control" required>
                            {% for categoria in categorias %}
                            <option value="{{ categoria }}">{{ categoria }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Descrição</label>
                    <input type="text" name="descricao" class="form-control" placeholder="Descrição da transação">
                </div>
                <div class="text-right">
                    <button type="submit" class="btn">Salvar Transação</button>
                </div>
            </form>
        </div>

        <div class="table-container">
            <h2 style="margin-bottom: 1.5rem;">Histórico de Transações</h2>
            <table>
                <thead>
                    <tr>
                        <th>Data</th>
                        <th>Tipo</th>
                        <th>Valor</th>
                        <th>Categoria</th>
                        <th>Descrição</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
                    {% for transacao in transacoes %}
                    <tr>
                        <td>{{ transacao[3] }}</td>
                        <td>
                            <span class="badge {{ 'badge-receita' if transacao[1] == 'Receita' else 'badge-despesa' }}">
                                {{ transacao[1] }}
                            </span>
                        </td>
                        <td class="{{ 'receita' if transacao[1] == 'Receita' else 'despesa' }}">
                            R$ {{ "%.2f"|format(transacao[2]) }}
                        </td>
                        <td>{{ transacao[5] }}</td>
                        <td>{{ transacao[4] }}</td>
                        <td>
                            <form action="{{ url_for('excluir_transacao', id=transacao[0]) }}" method="POST" style="display: inline;">
                                <button type="submit" class="btn" style="background: #ef4444; font-size: 0.875rem; padding: 0.5rem;">
                                    Excluir
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </main>

    <script>
        // Formatar input de valor para moeda brasileira
        document.querySelector('input[name="valor"]').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = (value/100).toFixed(2);
            value = value.replace('.', ',');
            value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
            e.target.value = value;
        });

        // Definir data atual como padrão
        document.querySelector('input[name="data"]').valueAsDate = new Date();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Página principal."""
    resumo = db.get_resumo_financeiro()
    transacoes = db.get_transacoes()
    categorias = [cat[0] for cat in db.get_categorias()]
    
    return render_template_string(
        TEMPLATE,
        resumo=ResumoFinanceiro.from_dict(resumo),
        transacoes=transacoes,
        categorias=categorias
    )

@app.route('/adicionar_transacao', methods=['POST'])
def adicionar_transacao():
    """Adiciona uma nova transação."""
    try:
        tipo = request.form['tipo']
        valor = request.form['valor']
        data = request.form['data']
        categoria = request.form['categoria']
        descricao = request.form['descricao']

        # Validações
        valido, valor_float, erro = validar_valor(valor)
        if not valido:
            return f"Erro: {erro}", 400

        valido, _, erro = validar_data(data)
        if not valido:
            return f"Erro: {erro}", 400

        # Salva no banco de dados
        db.add_transacao(tipo, valor_float, data, descricao, categoria)
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logging.error(f"Erro ao adicionar transação: {e}")
        return "Erro ao salvar a transação", 500

@app.route('/excluir_transacao/<int:id>', methods=['POST'])
def excluir_transacao(id):
    """Exclui uma transação."""
    try:
        db.delete_transacao(id)
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Erro ao excluir transação: {e}")
        return "Erro ao excluir a transação", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
