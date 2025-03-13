import matplotlib
matplotlib.use('Agg')  # Usar backend não-interativo

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QMessageBox, QDateEdit, QTextEdit, QFrame,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import logging

from .database import DatabaseManager
from .models import Transacao, ResumoFinanceiro
from .utils import (
    validar_valor, validar_data, formatar_valor_monetario,
    formatar_data, validar_descricao, gerar_cor_categoria
)

class FinAssistWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.setup_ui()
        self.carregar_dados()

    def setup_ui(self):
        """Configura a interface do usuário."""
        self.setWindowTitle("Fin Assist - Assistente Financeiro")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Tabs
        self.tabs = QTabWidget()
        self.setup_dashboard_tab()
        self.setup_nova_transacao_tab()
        self.setup_historico_tab()
        self.setup_relatorios_tab()
        
        layout.addWidget(self.tabs)

    def setup_dashboard_tab(self):
        """Configura a aba do Dashboard."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Resumo financeiro
        resumo_frame = QFrame()
        resumo_frame.setFrameStyle(QFrame.StyledPanel)
        resumo_layout = QGridLayout(resumo_frame)
        
        # Estilo para os valores
        valor_style = "QLabel { font-size: 18px; font-weight: bold; }"
        
        # Receitas
        receitas_label = QLabel("Receitas:")
        self.receitas_valor = QLabel("R$ 0,00")
        self.receitas_valor.setStyleSheet(valor_style + "color: #2ecc71;")
        resumo_layout.addWidget(receitas_label, 0, 0)
        resumo_layout.addWidget(self.receitas_valor, 0, 1)
        
        # Despesas
        despesas_label = QLabel("Despesas:")
        self.despesas_valor = QLabel("R$ 0,00")
        self.despesas_valor.setStyleSheet(valor_style + "color: #e74c3c;")
        resumo_layout.addWidget(despesas_label, 1, 0)
        resumo_layout.addWidget(self.despesas_valor, 1, 1)
        
        # Saldo
        saldo_label = QLabel("Saldo:")
        self.saldo_valor = QLabel("R$ 0,00")
        self.saldo_valor.setStyleSheet(valor_style)
        resumo_layout.addWidget(saldo_label, 2, 0)
        resumo_layout.addWidget(self.saldo_valor, 2, 1)
        
        layout.addWidget(resumo_frame)
        
        # Gráfico
        self.figura = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figura)
        layout.addWidget(self.canvas)
        
        self.tabs.addTab(tab, "Dashboard")

    def setup_nova_transacao_tab(self):
        """Configura a aba de Nova Transação."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário
        form_layout = QGridLayout()
        
        # Tipo
        form_layout.addWidget(QLabel("Tipo:"), 0, 0)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["Receita", "Despesa"])
        form_layout.addWidget(self.tipo_combo, 0, 1)
        
        # Valor
        form_layout.addWidget(QLabel("Valor (R$):"), 1, 0)
        self.valor_edit = QLineEdit()
        self.valor_edit.setPlaceholderText("0,00")
        form_layout.addWidget(self.valor_edit, 1, 1)
        
        # Data
        form_layout.addWidget(QLabel("Data:"), 2, 0)
        self.data_edit = QDateEdit()
        self.data_edit.setCalendarPopup(True)
        self.data_edit.setDate(QDate.currentDate())
        form_layout.addWidget(self.data_edit, 2, 1)
        
        # Categoria
        form_layout.addWidget(QLabel("Categoria:"), 3, 0)
        self.categoria_combo = QComboBox()
        self.categoria_combo.addItems([cat[0] for cat in self.db.get_categorias()])
        form_layout.addWidget(self.categoria_combo, 3, 1)
        
        # Descrição
        form_layout.addWidget(QLabel("Descrição:"), 4, 0)
        self.descricao_edit = QTextEdit()
        self.descricao_edit.setMaximumHeight(100)
        form_layout.addWidget(self.descricao_edit, 4, 1)
        
        layout.addLayout(form_layout)
        
        # Botão Salvar
        salvar_btn = QPushButton("Salvar Transação")
        salvar_btn.clicked.connect(self.salvar_transacao)
        layout.addWidget(salvar_btn)
        
        # Espaçador
        layout.addStretch()
        
        self.tabs.addTab(tab, "Nova Transação")

    def setup_historico_tab(self):
        """Configura a aba de Histórico."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabela de transações
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels([
            "Data", "Tipo", "Valor", "Categoria", "Descrição", "Ações"
        ])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.tabela)
        
        self.tabs.addTab(tab, "Histórico")

    def setup_relatorios_tab(self):
        """Configura a aba de Relatórios."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Gráfico de gastos por categoria
        self.figura_relatorio = plt.figure(figsize=(8, 6))
        self.canvas_relatorio = FigureCanvas(self.figura_relatorio)
        layout.addWidget(self.canvas_relatorio)
        
        self.tabs.addTab(tab, "Relatórios")

    def carregar_dados(self):
        """Carrega e atualiza todos os dados na interface."""
        self.atualizar_resumo()
        self.atualizar_historico()
        self.atualizar_graficos()

    def atualizar_resumo(self):
        """Atualiza o resumo financeiro."""
        resumo = self.db.get_resumo_financeiro()
        resumo = ResumoFinanceiro.from_dict(resumo)
        
        self.receitas_valor.setText(resumo.receitas_formatado)
        self.despesas_valor.setText(resumo.despesas_formatado)
        self.saldo_valor.setText(resumo.saldo_formatado)
        
        # Atualiza a cor do saldo
        if resumo.saldo >= 0:
            self.saldo_valor.setStyleSheet("QLabel { color: #2ecc71; font-size: 18px; font-weight: bold; }")
        else:
            self.saldo_valor.setStyleSheet("QLabel { color: #e74c3c; font-size: 18px; font-weight: bold; }")

    def atualizar_historico(self):
        """Atualiza a tabela de histórico."""
        transacoes = self.db.get_transacoes()
        self.tabela.setRowCount(len(transacoes))
        
        for i, trans in enumerate(transacoes):
            transacao = Transacao.from_dict({
                'id': trans[0],
                'tipo': trans[1],
                'valor': trans[2],
                'data': trans[3],
                'descricao': trans[4],
                'categoria': trans[5]
            })
            
            self.tabela.setItem(i, 0, QTableWidgetItem(transacao.data_formatada))
            self.tabela.setItem(i, 1, QTableWidgetItem(transacao.tipo))
            self.tabela.setItem(i, 2, QTableWidgetItem(transacao.valor_formatado))
            self.tabela.setItem(i, 3, QTableWidgetItem(transacao.categoria))
            self.tabela.setItem(i, 4, QTableWidgetItem(transacao.descricao))
            
            # Botões de ação
            acoes_widget = QWidget()
            acoes_layout = QHBoxLayout(acoes_widget)
            
            editar_btn = QPushButton("Editar")
            editar_btn.clicked.connect(lambda checked, t=transacao: self.editar_transacao(t))
            
            excluir_btn = QPushButton("Excluir")
            excluir_btn.clicked.connect(lambda checked, t=transacao: self.excluir_transacao(t))
            
            acoes_layout.addWidget(editar_btn)
            acoes_layout.addWidget(excluir_btn)
            acoes_layout.setContentsMargins(0, 0, 0, 0)
            
            self.tabela.setCellWidget(i, 5, acoes_widget)

    def atualizar_graficos(self):
        """Atualiza os gráficos do dashboard e relatórios."""
        # Limpa as figuras
        self.figura.clear()
        self.figura_relatorio.clear()
        
        # Obtém dados para os gráficos
        transacoes = self.db.get_transacoes()
        categorias = {}
        
        for trans in transacoes:
            if trans[1] == 'Despesa':  # Apenas despesas
                categoria = trans[5]
                valor = trans[2]
                categorias[categoria] = categorias.get(categoria, 0) + valor
        
        if categorias:
            # Gráfico do Dashboard (Pizza)
            ax = self.figura.add_subplot(111)
            valores = list(categorias.values())
            labels = list(categorias.keys())
            cores = [gerar_cor_categoria(cat) for cat in labels]
            
            ax.pie(valores, labels=labels, colors=cores, autopct='%1.1f%%')
            ax.set_title('Distribuição de Despesas por Categoria')
            
            # Gráfico de Relatórios (Barras)
            ax2 = self.figura_relatorio.add_subplot(111)
            ax2.bar(labels, valores, color=cores)
            ax2.set_title('Despesas por Categoria')
            ax2.set_xlabel('Categorias')
            ax2.set_ylabel('Valor (R$)')
            plt.xticks(rotation=45)
            
            self.figura_relatorio.tight_layout()
        
        # Atualiza os canvas
        self.canvas.draw()
        self.canvas_relatorio.draw()

    def salvar_transacao(self):
        """Salva uma nova transação."""
        # Validação dos dados
        tipo = self.tipo_combo.currentText()
        valor = self.valor_edit.text()
        data = self.data_edit.date().toString("yyyy-MM-dd")
        categoria = self.categoria_combo.currentText()
        descricao = self.descricao_edit.toPlainText()
        
        # Validações
        valido, valor_float, erro = validar_valor(valor)
        if not valido:
            QMessageBox.warning(self, "Erro", erro)
            return
        
        valido, _, erro = validar_data(data)
        if not valido:
            QMessageBox.warning(self, "Erro", erro)
            return
        
        valido, erro = validar_descricao(descricao)
        if not valido:
            QMessageBox.warning(self, "Erro", erro)
            return
        
        try:
            # Salva no banco de dados
            self.db.add_transacao(tipo, valor_float, data, descricao, categoria)
            
            # Limpa o formulário
            self.valor_edit.clear()
            self.data_edit.setDate(QDate.currentDate())
            self.descricao_edit.clear()
            
            # Atualiza a interface
            self.carregar_dados()
            
            QMessageBox.information(self, "Sucesso", "Transação salva com sucesso!")
            
        except Exception as e:
            logging.error(f"Erro ao salvar transação: {e}")
            QMessageBox.critical(self, "Erro", "Erro ao salvar a transação.")

    def editar_transacao(self, transacao):
        """Abre o formulário para editar uma transação."""
        # TODO: Implementar edição de transação
        pass

    def excluir_transacao(self, transacao):
        """Exclui uma transação após confirmação."""
        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir esta transação?\n\n"
            f"Data: {transacao.data_formatada}\n"
            f"Tipo: {transacao.tipo}\n"
            f"Valor: {transacao.valor_formatado}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if resposta == QMessageBox.Yes:
            try:
                self.db.delete_transacao(transacao.id)
                self.carregar_dados()
                QMessageBox.information(self, "Sucesso", "Transação excluída com sucesso!")
            except Exception as e:
                logging.error(f"Erro ao excluir transação: {e}")
                QMessageBox.critical(self, "Erro", "Erro ao excluir a transação.")
