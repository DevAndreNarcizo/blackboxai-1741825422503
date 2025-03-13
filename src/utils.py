import re
from datetime import datetime
from typing import Union, Tuple, Optional

def validar_valor(valor: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Valida se uma string representa um valor monetário válido.
    
    Args:
        valor (str): String contendo o valor a ser validado
        
    Returns:
        Tuple[bool, Optional[float], Optional[str]]: 
            - Boolean indicando se é válido
            - Valor convertido para float se válido, None se inválido
            - Mensagem de erro se inválido, None se válido
    """
    # Remove R$ e espaços
    valor = valor.replace('R$', '').strip()
    # Remove pontos de milhar e substitui vírgula por ponto
    valor = valor.replace('.', '').replace(',', '.')
    
    try:
        valor_float = float(valor)
        if valor_float <= 0:
            return False, None, "O valor deve ser maior que zero"
        return True, valor_float, None
    except ValueError:
        return False, None, "Valor inválido. Use apenas números e vírgula"

def validar_data(data: str) -> Tuple[bool, Optional[datetime], Optional[str]]:
    """
    Valida se uma string representa uma data válida no formato dd/mm/aaaa.
    
    Args:
        data (str): String contendo a data a ser validada
        
    Returns:
        Tuple[bool, Optional[datetime], Optional[str]]:
            - Boolean indicando se é válida
            - Data convertida para datetime se válida, None se inválida
            - Mensagem de erro se inválida, None se válida
    """
    try:
        if '/' in data:
            data_obj = datetime.strptime(data, "%d/%m/%Y")
        else:
            data_obj = datetime.strptime(data, "%Y-%m-%d")
            
        if data_obj > datetime.now():
            return False, None, "A data não pode ser futura"
        return True, data_obj, None
    except ValueError:
        return False, None, "Data inválida. Use o formato dd/mm/aaaa"

def formatar_valor_monetario(valor: Union[float, str]) -> str:
    """
    Formata um valor numérico para o formato monetário brasileiro.
    
    Args:
        valor (Union[float, str]): Valor a ser formatado
        
    Returns:
        str: Valor formatado (ex: R$ 1.234,56)
    """
    if isinstance(valor, str):
        try:
            valor = float(valor.replace('R$', '').replace('.', '').replace(',', '.').strip())
        except ValueError:
            return "R$ 0,00"
    
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def formatar_data(data: Union[str, datetime]) -> str:
    """
    Formata uma data para o formato brasileiro (dd/mm/aaaa).
    
    Args:
        data (Union[str, datetime]): Data a ser formatada
        
    Returns:
        str: Data formatada
    """
    if isinstance(data, str):
        try:
            if '/' in data:
                data = datetime.strptime(data, "%d/%m/%Y")
            else:
                data = datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            return ""
    
    return data.strftime("%d/%m/%Y")

def validar_descricao(descricao: str) -> Tuple[bool, Optional[str]]:
    """
    Valida a descrição da transação.
    
    Args:
        descricao (str): Descrição a ser validada
        
    Returns:
        Tuple[bool, Optional[str]]:
            - Boolean indicando se é válida
            - Mensagem de erro se inválida, None se válida
    """
    descricao = descricao.strip()
    if len(descricao) > 100:
        return False, "A descrição deve ter no máximo 100 caracteres"
    return True, None

def gerar_cor_categoria(categoria: str) -> str:
    """
    Gera uma cor hexadecimal consistente para uma categoria.
    
    Args:
        categoria (str): Nome da categoria
        
    Returns:
        str: Código hexadecimal da cor
    """
    cores_padrao = {
        'Alimentação': '#FF6B6B',
        'Transporte': '#4ECDC4',
        'Moradia': '#45B7D1',
        'Lazer': '#96CEB4',
        'Saúde': '#D4A5A5',
        'Educação': '#9FA8DA',
        'Salário': '#81C784',
        'Investimentos': '#FFD93D',
        'Outros': '#A8A8A8'
    }
    
    return cores_padrao.get(categoria, '#808080')

def calcular_percentual(valor: float, total: float) -> float:
    """
    Calcula o percentual de um valor em relação ao total.
    
    Args:
        valor (float): Valor a ser calculado
        total (float): Valor total
        
    Returns:
        float: Percentual calculado
    """
    if total == 0:
        return 0
    return (valor / total) * 100

def validar_categoria(categoria: str) -> Tuple[bool, Optional[str]]:
    """
    Valida o nome de uma categoria.
    
    Args:
        categoria (str): Nome da categoria a ser validada
        
    Returns:
        Tuple[bool, Optional[str]]:
            - Boolean indicando se é válida
            - Mensagem de erro se inválida, None se válida
    """
    categoria = categoria.strip()
    if not categoria:
        return False, "A categoria não pode estar vazia"
    if len(categoria) > 50:
        return False, "A categoria deve ter no máximo 50 caracteres"
    if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', categoria):
        return False, "A categoria deve conter apenas letras e espaços"
    return True, None
