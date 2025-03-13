from flask import Flask, render_template, request, jsonify, redirect, url_for
from src.database import DatabaseManager
from src.models import Transacao, ResumoFinanceiro
from src.utils import validar_valor, validar_data, formatar_valor_monetario
from datetime import datetime
import logging

app = Flask(__name__)
db = DatabaseManager()

@app.route('/')
def index():
    """Página principal."""
    resumo = db.get_resumo_financeiro()
    transacoes = db.get_transacoes()
    categorias = [cat[0] for cat in db.get_categorias()]
    
    return render_template(
        'index.html',
        resumo=resumo,
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
            return jsonify({'error': erro}), 400

        valido, _, erro = validar_data(data)
        if not valido:
            return jsonify({'error': erro}), 400

        # Salva no banco de dados
        db.add_transacao(tipo, valor_float, data, descricao, categoria)
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logging.error(f"Erro ao adicionar transação: {e}")
        return jsonify({'error': 'Erro ao salvar a transação'}), 500

@app.route('/excluir_transacao/<int:id>', methods=['POST'])
def excluir_transacao(id):
    """Exclui uma transação."""
    try:
        db.delete_transacao(id)
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Erro ao excluir transação: {e}")
        return jsonify({'error': 'Erro ao excluir a transação'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
