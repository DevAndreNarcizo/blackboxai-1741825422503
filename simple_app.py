from flask import Flask, request, redirect, url_for, render_template_string, jsonify
from src.database import DatabaseManager
from src.models import Transacao, ResumoFinanceiro
from src.utils import validar_valor, validar_data, formatar_valor_monetario
from datetime import datetime, date
import logging

app = Flask(__name__)
db = DatabaseManager()

# Funções auxiliares
def get_mes_ano_atual():
    hoje = date.today()
    return hoje.month, hoje.year

def formatar_data_br(data_str):
    if not data_str:
        return ""
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d")
        return data.strftime("%d/%m/%Y")
    except:
        return data_str

def calcular_progresso(valor_atual, valor_alvo):
    if valor_alvo <= 0:
        return 0
    return min(100, (valor_atual / valor_alvo) * 100)

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
            min-height: 100vh;
        }

        /* Modal Styles */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            padding: 1rem;
        }

        .modal.active {
            display: flex;
        }

        .modal-content {
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            width: 100%;
            max-width: 500px;
            position: relative;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .modal-content {
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            width: 90%;
            max-width: 500px;
            position: relative;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateY(20px);
            opacity: 0;
            transition: all 0.3s ease;
        }

        .modal.show .modal-content {
            transform: translateY(0);
            opacity: 1;
        }

        .modal-close {
            position: absolute;
            top: 1.25rem;
            right: 1.25rem;
            background: none;
            border: none;
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            cursor: pointer;
            color: #666;
            transition: all 0.2s ease;
        }

        .modal-close:hover {
            background-color: #f3f4f6;
            color: #333;
        }

        .modal form {
            margin-top: 1.5rem;
        }

        .modal .form-control {
            transition: all 0.2s ease;
        }

        .modal .form-control:focus {
            border-color: #4F46E5;
            box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
        }

        .modal .btn-primary {
            background-color: #4F46E5;
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .modal .btn-primary:hover {
            background-color: #4338CA;
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
        <!-- Dashboard Principal -->
        <div class="dashboard">
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-arrow-up text-green-500 mr-2"></i>
                    Receitas
                </div>
                <div class="receita">R$ {{ "%.2f"|format(resumo.receitas) }}</div>
            </div>
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-arrow-down text-red-500 mr-2"></i>
                    Despesas
                </div>
                <div class="despesa">R$ {{ "%.2f"|format(resumo.despesas) }}</div>
            </div>
            <div class="card">
                <div class="card-title">
                    <i class="fas fa-balance-scale text-blue-500 mr-2"></i>
                    Saldo
                </div>
                <div class="{{ 'receita' if resumo.saldo >= 0 else 'despesa' }}">
                    R$ {{ "%.2f"|format(resumo.saldo) }}
                </div>
            </div>
        </div>

        <!-- Resumo por Categoria -->
        <div class="card mb-6">
            <h2 class="text-xl font-semibold mb-4">Despesas por Categoria (Mês Atual)</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {% for categoria, total in resumo.despesas_por_categoria %}
                <div class="p-4 border rounded-lg">
                    <div class="flex justify-between items-center">
                        <span class="font-medium">{{ categoria }}</span>
                        <span class="text-red-600">R$ {{ "%.2f"|format(total) }}</span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Orçamentos -->
        <div class="card mb-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Orçamentos ({{ mes_atual }}/{{ ano_atual }})</h2>
                <button onclick="document.getElementById('modal-orcamento').classList.add('show')" 
                        class="btn btn-primary">
                    <i class="fas fa-plus mr-2"></i>Novo Orçamento
                </button>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {% for orcamento in orcamentos %}
                <div class="p-4 border rounded-lg">
                    <div class="flex justify-between items-center mb-2">
                        <span class="font-medium">{{ orcamento[1] }}</span>
                        <form action="{{ url_for('excluir_orcamento', id=orcamento[0]) }}" 
                              method="POST" class="inline">
                            <button type="submit" class="text-red-600 hover:text-red-800">
                                <i class="fas fa-trash"></i>
                            </button>
                        </form>
                    </div>
                    <div class="mb-2">
                        <span class="text-gray-600">Limite: R$ {{ "%.2f"|format(orcamento[2]) }}</span>
                        <span class="mx-2">|</span>
                        <span class="text-gray-600">Atual: R$ {{ "%.2f"|format(orcamento[3]) }}</span>
                    </div>
                    {% set progresso = calcular_progresso(orcamento[3], orcamento[2]) %}
                    <div class="w-full bg-gray-200 rounded-full h-2.5">
                        <div class="bg-blue-600 h-2.5 rounded-full" 
                             style="width: {{ progresso }}%"></div>
                    </div>
                    <div class="text-right text-sm text-gray-600">
                        {{ "%.1f"|format(progresso) }}%
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Metas Financeiras -->
        <div class="card mb-6">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-xl font-semibold">Metas Financeiras</h2>
                <button onclick="document.getElementById('modal-meta').classList.add('show')" 
                        class="btn btn-primary">
                    <i class="fas fa-plus mr-2"></i>Nova Meta
                </button>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                {% for meta in metas %}
                <div class="p-4 border rounded-lg">
                    <div class="flex justify-between items-center mb-2">
                        <span class="font-medium">{{ meta[1] }}</span>
                        <div class="flex gap-2">
                            <button onclick="abrirEdicaoMeta({{ meta[0] }}, '{{ meta[1] }}', 
                                {{ meta[2] }}, {{ meta[3] }}, '{{ meta[4] }}', '{{ meta[5] }}', 
                                '{{ meta[6] }}')" 
                                    class="text-blue-600 hover:text-blue-800">
                                <i class="fas fa-edit"></i>
                            </button>
                            <form action="{{ url_for('excluir_meta', id=meta[0]) }}" 
                                  method="POST" class="inline">
                                <button type="submit" class="text-red-600 hover:text-red-800">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                    <div class="mb-2">
                        <span class="text-gray-600">Meta: R$ {{ "%.2f"|format(meta[2]) }}</span>
                        <span class="mx-2">|</span>
                        <span class="text-gray-600">Atual: R$ {{ "%.2f"|format(meta[3]) }}</span>
                    </div>
                    <div class="mb-2 text-sm text-gray-600">
                        {{ formatar_data(meta[4]) }} até {{ formatar_data(meta[5]) }}
                    </div>
                    {% set progresso = calcular_progresso(meta[3], meta[2]) %}
                    <div class="w-full bg-gray-200 rounded-full h-2.5 mb-2">
                        <div class="bg-green-600 h-2.5 rounded-full" 
                             style="width: {{ progresso }}%"></div>
                    </div>
                    <div class="flex justify-between items-center">
                        <span class="text-sm text-gray-600">{{ "%.1f"|format(progresso) }}%</span>
                        <span class="px-2 py-1 rounded-full text-xs 
                            {% if meta[6] == 'Concluída' %}
                                bg-green-100 text-green-800
                            {% else %}
                                bg-blue-100 text-blue-800
                            {% endif %}">
                            {{ meta[6] }}
                        </span>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Modal Novo Orçamento -->
        <div id="modal-orcamento" class="modal" role="dialog" aria-modal="true">
            <div class="modal-backdrop"></div>
            <div class="modal-content">
                <button class="modal-close" aria-label="Fechar">
                    <i class="fas fa-times"></i>
                </button>
                <h3 class="text-xl font-semibold mb-4">Novo Orçamento</h3>
                    <form action="{{ url_for('adicionar_orcamento') }}" method="POST">
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Categoria
                            </label>
                            <select name="categoria" required class="form-control">
                                {% for categoria in categorias %}
                                <option value="{{ categoria }}">{{ categoria }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Valor Limite (R$)
                            </label>
                            <input type="text" name="valor_limite" required 
                                   class="form-control" placeholder="0,00">
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">
                                    Mês
                                </label>
                                <select name="mes" required class="form-control">
                                    {% for i in range(1, 13) %}
                                    <option value="{{ i }}" 
                                            {{ 'selected' if i == mes_atual else '' }}>
                                        {{ i }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">
                                    Ano
                                </label>
                                <select name="ano" required class="form-control">
                                    {% for i in range(ano_atual - 1, ano_atual + 2) %}
                                    <option value="{{ i }}" 
                                            {{ 'selected' if i == ano_atual else '' }}>
                                        {{ i }}
                                    </option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="flex justify-end">
                            <button type="submit" class="btn btn-primary">
                                Salvar Orçamento
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Modal Nova Meta -->
        <div id="modal-meta" class="modal" role="dialog" aria-modal="true">
            <div class="modal-backdrop"></div>
            <div class="modal-content">
                <button class="modal-close" aria-label="Fechar">
                    <i class="fas fa-times"></i>
                </button>
                <h3 class="text-xl font-semibold mb-4">Nova Meta</h3>
                    <form action="{{ url_for('adicionar_meta') }}" method="POST">
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Descrição
                            </label>
                            <input type="text" name="descricao" required 
                                   class="form-control" placeholder="Descrição da meta">
                        </div>
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Valor Alvo (R$)
                            </label>
                            <input type="text" name="valor_alvo" required 
                                   class="form-control" placeholder="0,00">
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">
                                    Data Início
                                </label>
                                <input type="date" name="data_inicio" required 
                                       class="form-control">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">
                                    Data Fim
                                </label>
                                <input type="date" name="data_fim" required 
                                       class="form-control">
                            </div>
                        </div>
                        <div class="flex justify-end">
                            <button type="submit" class="btn btn-primary">
                                Salvar Meta
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Modal Editar Meta -->
        <div id="modal-editar-meta" class="modal" role="dialog" aria-modal="true">
            <div class="modal-backdrop"></div>
            <div class="modal-content">
                <button class="modal-close" aria-label="Fechar">
                    <i class="fas fa-times"></i>
                </button>
                <h3 class="text-xl font-semibold mb-4">Editar Meta</h3>
                    <form id="form-editar-meta" action="" method="POST">
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Descrição
                            </label>
                            <input type="text" name="descricao" required 
                                   class="form-control" id="edit-meta-descricao">
                        </div>
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Valor Alvo (R$)
                            </label>
                            <input type="text" name="valor_alvo" required 
                                   class="form-control" id="edit-meta-valor-alvo">
                        </div>
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Valor Atual (R$)
                            </label>
                            <input type="text" name="valor_atual" required 
                                   class="form-control" id="edit-meta-valor-atual">
                        </div>
                        <div class="grid grid-cols-2 gap-4 mb-4">
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">
                                    Data Início
                                </label>
                                <input type="date" name="data_inicio" required 
                                       class="form-control" id="edit-meta-data-inicio">
                            </div>
                            <div>
                                <label class="block text-gray-700 text-sm font-bold mb-2">
                                    Data Fim
                                </label>
                                <input type="date" name="data_fim" required 
                                       class="form-control" id="edit-meta-data-fim">
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="block text-gray-700 text-sm font-bold mb-2">
                                Status
                            </label>
                            <select name="status" required class="form-control" id="edit-meta-status">
                                <option value="Em Andamento">Em Andamento</option>
                                <option value="Concluída">Concluída</option>
                            </select>
                        </div>
                        <div class="flex justify-end">
                            <button type="submit" class="btn btn-primary">
                                Salvar Alterações
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>

        <!-- Nova Transação -->
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
        // Função para formatar valores monetários
        function formatarMoeda(input) {
            let value = input.value.replace(/\D/g, '');
            value = (value/100).toFixed(2);
            value = value.replace('.', ',');
            value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
            input.value = value;
        }

        // Adicionar formatação a todos os campos de valor
        document.querySelectorAll('input[name="valor"], input[name="valor_limite"], input[name="valor_alvo"], input[name="valor_atual"]')
            .forEach(input => {
                input.addEventListener('input', function(e) {
                    formatarMoeda(this);
                });
            });

        // Definir data atual como padrão
        document.querySelector('input[name="data"]').valueAsDate = new Date();
        
        // Funções para manipulação de modais
        function abrirModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.classList.add('show');
        }
        
        function fecharModal(modalId) {
            const modal = document.getElementById(modalId);
            modal.classList.remove('show');
        }
        
        // Função para abrir modal de edição de meta
        function abrirEdicaoMeta(id, descricao, valorAlvo, valorAtual, dataInicio, dataFim, status) {
            const modal = document.getElementById('modal-editar-meta');
            const form = document.getElementById('form-editar-meta');
            
            // Atualizar action do formulário
            form.action = `/atualizar_meta/${id}`;
            
            // Preencher campos
            document.getElementById('edit-meta-descricao').value = descricao;
            document.getElementById('edit-meta-valor-alvo').value = 
                (valorAlvo).toLocaleString('pt-BR', {minimumFractionDigits: 2});
            document.getElementById('edit-meta-valor-atual').value = 
                (valorAtual).toLocaleString('pt-BR', {minimumFractionDigits: 2});
            document.getElementById('edit-meta-data-inicio').value = dataInicio;
            document.getElementById('edit-meta-data-fim').value = dataFim;
            document.getElementById('edit-meta-status').value = status;
            
            // Exibir modal
            abrirModal('modal-editar-meta');
        }

        // Funções para manipulação de modais
        // Funções para manipulação de modais
        function toggleModal(modalId, show) {
            const modal = document.getElementById(modalId);
            if (modal) {
                if (show) {
                    modal.style.display = 'flex';
                    // Resetar formulário
                    const form = modal.querySelector('form');
                    if (form) form.reset();
                } else {
                    modal.style.display = 'none';
                }
            }
        }

        // Função para abrir modal
        function abrirModal(modalId) {
            toggleModal(modalId, true);
        }

        // Função para fechar modal
        function fecharModal(modalId) {
            toggleModal(modalId, false);
        }

        // Inicializar eventos quando o DOM estiver pronto
        document.addEventListener('DOMContentLoaded', function() {
            // Configurar botões de fechar modal
            document.querySelectorAll('.modal-close').forEach(button => {
                button.onclick = function(e) {
                    e.preventDefault();
                    const modal = this.closest('.modal');
                    if (modal) fecharModal(modal.id);
                };
            });

            // Fechar modal ao clicar fora
            document.querySelectorAll('.modal').forEach(modal => {
                modal.onclick = function(e) {
                    if (e.target === this) {
                        fecharModal(this.id);
                    }
                };
            });

            // Prevenir fechamento ao clicar no conteúdo do modal
            document.querySelectorAll('.modal-content').forEach(content => {
                content.onclick = function(e) {
                    e.stopPropagation();
                };
            });

            // Inicializar formatação de valores monetários
            document.querySelectorAll('input[name="valor"], input[name="valor_limite"], input[name="valor_alvo"], input[name="valor_atual"]')
                .forEach(input => {
                    input.addEventListener('input', function() {
                        formatarMoeda(this);
                    });
                });

            // Definir data atual como padrão para campos de data
            document.querySelectorAll('input[type="date"]').forEach(input => {
                if (!input.value) {
                    input.valueAsDate = new Date();
                }
            });
        });

        // Inicializar datas nos formulários
        document.querySelectorAll('input[type="date"]').forEach(input => {
            if (!input.value) {
                input.valueAsDate = new Date();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Página principal com dashboard."""
    mes_atual, ano_atual = get_mes_ano_atual()
    
    # Dados básicos
    resumo = db.get_resumo_financeiro()
    transacoes = db.get_transacoes()
    categorias = [cat[0] for cat in db.get_categorias()]
    
    # Orçamentos do mês atual
    orcamentos = db.get_orcamentos(mes_atual, ano_atual)
    
    # Metas ativas
    metas = db.get_metas()
    
    return render_template_string(
        TEMPLATE,
        resumo=ResumoFinanceiro.from_dict(resumo),
        transacoes=transacoes,
        categorias=categorias,
        orcamentos=orcamentos,
        metas=metas,
        mes_atual=mes_atual,
        ano_atual=ano_atual,
        formatar_data=formatar_data_br,
        calcular_progresso=calcular_progresso
    )

# Rotas para Transações
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

# Rotas para Orçamentos
@app.route('/adicionar_orcamento', methods=['POST'])
def adicionar_orcamento():
    """Adiciona um novo orçamento."""
    try:
        categoria = request.form['categoria']
        valor_limite = request.form['valor_limite']
        mes = int(request.form['mes'])
        ano = int(request.form['ano'])

        # Validação do valor
        valido, valor_float, erro = validar_valor(valor_limite)
        if not valido:
            return erro, 400

        if db.add_orcamento(categoria, valor_float, mes, ano):
            return redirect(url_for('index'))
        else:
            return "Erro ao salvar orçamento", 500
            
    except Exception as e:
        logging.error(f"Erro ao adicionar orçamento: {e}")
        return "Erro ao salvar orçamento", 500

@app.route('/excluir_orcamento/<int:id>', methods=['POST'])
def excluir_orcamento(id):
    """Exclui um orçamento."""
    try:
        db.delete_orcamento(id)
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Erro ao excluir orçamento: {e}")
        return "Erro ao excluir orçamento", 500

# Rotas para Metas
@app.route('/adicionar_meta', methods=['POST'])
def adicionar_meta():
    """Adiciona uma nova meta."""
    try:
        descricao = request.form['descricao']
        valor_alvo = request.form['valor_alvo']
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']

        # Validações
        valido, valor_float, erro = validar_valor(valor_alvo)
        if not valido:
            return erro, 400

        valido, _, erro = validar_data(data_inicio)
        if not valido:
            return erro, 400

        valido, _, erro = validar_data(data_fim)
        if not valido:
            return erro, 400

        db.add_meta(descricao, valor_float, data_inicio, data_fim)
        return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Erro ao adicionar meta: {e}")
        return "Erro ao salvar meta", 500

@app.route('/atualizar_meta/<int:id>', methods=['POST'])
def atualizar_meta(id):
    """Atualiza uma meta existente."""
    try:
        descricao = request.form['descricao']
        valor_alvo = request.form['valor_alvo']
        valor_atual = request.form['valor_atual']
        data_inicio = request.form['data_inicio']
        data_fim = request.form['data_fim']
        status = request.form['status']

        # Validações
        valido, valor_alvo_float, erro = validar_valor(valor_alvo)
        if not valido:
            return erro, 400

        valido, valor_atual_float, erro = validar_valor(valor_atual)
        if not valido:
            return erro, 400

        db.update_meta(id, descricao, valor_alvo_float, valor_atual_float,
                      data_inicio, data_fim, status)
        return redirect(url_for('index'))
            
    except Exception as e:
        logging.error(f"Erro ao atualizar meta: {e}")
        return "Erro ao atualizar meta", 500

@app.route('/excluir_meta/<int:id>', methods=['POST'])
def excluir_meta(id):
    """Exclui uma meta."""
    try:
        db.delete_meta(id)
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Erro ao excluir meta: {e}")
        return "Erro ao excluir meta", 500

@app.route('/atualizar_progresso_meta/<int:id>', methods=['POST'])
def atualizar_progresso_meta(id):
    """Atualiza o progresso de uma meta."""
    try:
        valor_atual = request.form['valor_atual']
        valido, valor_float, erro = validar_valor(valor_atual)
        if not valido:
            return erro, 400

        db.atualizar_progresso_meta(id, valor_float)
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Erro ao atualizar progresso da meta: {e}")
        return "Erro ao atualizar progresso", 500

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
