import datetime
from logs.config_log import configurar_logging 
logger = configurar_logging()

def converter_data(data_str):
    if isinstance(data_str, datetime.datetime):
        return data_str.strftime("%d/%m/%Y")
    try:
        data_obj = datetime.datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
        return data_obj.strftime("%d/%m/%Y")
    except ValueError as e:
        logger.error(f"Erro ao converter a data: {e}")
        return None

def get_formatted_datetime():
    return datetime.datetime.now().strftime("%H:%M:%S")
