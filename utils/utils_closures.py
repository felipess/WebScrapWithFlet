import psutil
import time

from logs.config_log import configurar_logging 
logger = configurar_logging()

# Encerrar Firefox e Geckodriver
def finalizar_processos():
    firefox_processes = [p for p in psutil.process_iter(['name']) if 'firefox' in p.info['name'].lower()]
    geckodriver_processes = [p for p in psutil.process_iter(['name']) if 'geckodriver' in p.info['name'].lower()]
    for proc in firefox_processes:
        try:
            logger.info(f"Encerrando processo do Firefox: {proc.pid}")
            proc.terminate()
            proc.wait(timeout=1)  # Aguarda para o processo encerrar
        except psutil.NoSuchProcess:
            logger.warning(f"Firefox - O processo {proc.pid} não existe.")
        except psutil.TimeoutExpired:
            logger.warning(f"Firefox - O processo {proc.pid} não encerrou a tempo. Tentando encerrar forçosamente.")
            proc.kill()  

    for proc in geckodriver_processes:
        try:
            logger.info(f"Encerrando processo do GeckoDriver: {proc.pid}")
            proc.terminate()
            proc.wait(timeout=1)  # Aguarda para o processo encerrar
        except psutil.NoSuchProcess:
            logger.warning(f"GeckoDriver - O processo {proc.pid} não existe.")
        except psutil.TimeoutExpired:
            logger.warning(f"GeckoDriver - O processo {proc.pid} não encerrou a tempo. Tentando encerrar forçosamente.")
            proc.kill()  # Força o encerramento

def finalizar_driver(driver):
    if driver:
        try:
            logger.info("Encerrando o driver do Selenium...")
            driver.quit()  # Fecha o Firefox e encerra o driver
            time.sleep(1)  # Adiciona um delay para garantir que o processo feche
            driver = None  # Reseta o driver para evitar chamadas repetidas
            logger.info("Driver do Selenium encerrado com sucesso.")
        except Exception as e:
            logger.error(f"Ocorreu um erro ao encerrar o driver: {e}")
    else:
        logger.warning("Nenhum driver para encerrar.")
        return
    
def finalizar_driver_pid(driver_pid):    
    try:
        proc = psutil.Process(driver_pid)
        logger.info(f"Processo: {proc} atribuido")
        if proc.is_running():
            logger.info(f"Tentando encerrar processo: {proc}")
            proc.kill()  # Força o encerramento do processo
            logger.info(f"Processo do WebDriver com PID {driver_pid} encerrado.")
    except psutil.NoSuchProcess:
        logger.warning(f"O processo com PID {driver_pid} não existe.")
    except Exception as e:
        logger.error(f"Ocorreu um erro ao finalizar o driver: {e}")

def finalizar_custodias_app():
    app_name = "CustodiasApp.exe"
    processos_encerrados = 0

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == app_name.lower():
                proc.terminate()
                proc.wait(timeout=2)
                processos_encerrados += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if processos_encerrados == 0:
        logger.warning(f"Nenhum processo {app_name} encontrado.")
    else:
        logger.info(f"{processos_encerrados} processo(s) {app_name} finalizado(s) com sucesso.")

def cancelar_timers(timers):
    for timer in timers:
        timer.cancel()  # Cancela cada timer ativo
    timers.clear()  # Limpa a lista de timers
