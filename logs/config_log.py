import logging
import sys

def configurar_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # Nível de log
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Exibe os logs no terminal
            logging.FileHandler('app.log', mode='w')  # Salva os logs em um arquivo 'app.log'
        ]
    )

    # Garantir que a configuração seja feita uma vez
    logger = logging.getLogger()
    return logger

