import sys
import logging
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from .fin_assist_ui import FinAssistWindow

# Configurar o backend Qt para usar offscreen
os.environ["QT_QPA_PLATFORM"] = "offscreen"

def setup_logging():
    """Configura o sistema de logging da aplicação."""
    # Cria o diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configura o logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "fin_assist.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_font():
    """Configura a fonte padrão da aplicação."""
    font = QFont()
    font.setFamily("Segoe UI")  # Fonte moderna e legível
    font.setPointSize(10)
    QApplication.setFont(font)

def main():
    """Função principal que inicia a aplicação."""
    try:
        # Configura o logging
        setup_logging()
        logging.info("Iniciando Fin Assist...")
        
        # Cria a aplicação Qt
        app = QApplication(sys.argv)
        
        # Configura a fonte padrão
        setup_font()
        
        # Cria e exibe a janela principal
        window = FinAssistWindow()
        window.show()
        
        # Inicia o loop de eventos
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"Erro ao iniciar a aplicação: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
