from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transacao:
    """
    Classe que representa uma transação financeira.
    
    Attributes:
        tipo (str): Tipo da transação ('Receita' ou 'Despesa')
        valor (float): Valor da transação
        data (datetime): Data da transação
        categoria (str): Categoria da transação
        descricao (str): Descrição opcional da transação
        id (Optional[int]): ID único da transação no banco de dados
    """
    tipo: str
    valor: float
    data: datetime
    categoria: str
    descricao: str = ""
    id: Optional[int] = None

    def __post_init__(self):
        """Validação dos dados após a inicialização."""
        if self.tipo not in ['Receita', 'Despesa']:
            raise ValueError("Tipo deve ser 'Receita' ou 'Despesa'")
        
        if self.valor <= 0:
            raise ValueError("Valor deve ser maior que zero")
        
        if isinstance(self.data, str):
            try:
                self.data = datetime.strptime(self.data, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Data deve estar no formato YYYY-MM-DD")

    @property
    def data_formatada(self) -> str:
        """Retorna a data formatada no padrão brasileiro."""
        return self.data.strftime("%d/%m/%Y")

    @property
    def valor_formatado(self) -> str:
        """Retorna o valor formatado como moeda brasileira."""
        return f"R$ {self.valor:,.2f}"

    def to_dict(self) -> dict:
        """Converte a transação para um dicionário."""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'valor': self.valor,
            'data': self.data.strftime("%Y-%m-%d"),
            'categoria': self.categoria,
            'descricao': self.descricao
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transacao':
        """Cria uma instância de Transacao a partir de um dicionário."""
        return cls(
            tipo=data['tipo'],
            valor=float(data['valor']),
            data=data['data'],
            categoria=data['categoria'],
            descricao=data.get('descricao', ''),
            id=data.get('id')
        )

@dataclass
class ResumoFinanceiro:
    """
    Classe que representa um resumo financeiro.
    
    Attributes:
        receitas (float): Total de receitas
        despesas (float): Total de despesas
        saldo (float): Saldo (receitas - despesas)
    """
    receitas: float
    despesas: float
    saldo: float

    @property
    def receitas_formatado(self) -> str:
        """Retorna o total de receitas formatado como moeda brasileira."""
        return f"R$ {self.receitas:,.2f}"

    @property
    def despesas_formatado(self) -> str:
        """Retorna o total de despesas formatado como moeda brasileira."""
        return f"R$ {self.despesas:,.2f}"

    @property
    def saldo_formatado(self) -> str:
        """Retorna o saldo formatado como moeda brasileira."""
        return f"R$ {self.saldo:,.2f}"

    @classmethod
    def from_dict(cls, data: dict) -> 'ResumoFinanceiro':
        """Cria uma instância de ResumoFinanceiro a partir de um dicionário."""
        return cls(
            receitas=float(data['receitas']),
            despesas=float(data['despesas']),
            saldo=float(data['saldo'])
        )
