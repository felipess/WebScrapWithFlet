import psutil
import time

# Encerrar Firefox e Geckodriver
def finalizar_processos():
    firefox_processes = [p for p in psutil.process_iter(['name']) if 'firefox' in p.info['name'].lower()]
    geckodriver_processes = [p for p in psutil.process_iter(['name']) if 'geckodriver' in p.info['name'].lower()]
    for proc in firefox_processes:
        try:
            print(f"Encerrando processo do Firefox: {proc.pid}")
            proc.terminate()
            proc.wait(timeout=1)  # Aguarda para o processo encerrar
        except psutil.NoSuchProcess:
            print(f"Firefox - O processo {proc.pid} não existe.")
        except psutil.TimeoutExpired:
            print(f"Firefox - O processo {proc.pid} não encerrou a tempo. Tentando encerrar forçosamente.")
            proc.kill()  

    for proc in geckodriver_processes:
        try:
            print(f"Encerrando processo do GeckoDriver: {proc.pid}")
            proc.terminate()
            proc.wait(timeout=1)  # Aguarda para o processo encerrar
        except psutil.NoSuchProcess:
            print(f"GeckoDriver - O processo {proc.pid} não existe.")
        except psutil.TimeoutExpired:
            print(f"GeckoDriver - O processo {proc.pid} não encerrou a tempo. Tentando encerrar forçosamente.")
            proc.kill()  # Força o encerramento

def finalizar_driver(driver, driver_pid):
    if driver:
        try:
            print("Encerrando o driver do Selenium...")
            driver.quit()  # Fecha o Firefox e encerra o driver
            time.sleep(1)  # Adiciona um delay para garantir que o processo feche
            driver = None  # Reseta o driver para evitar chamadas repetidas
            print("Driver do Selenium encerrado com sucesso.")
        except Exception as e:
            print(f"Ocorreu um erro ao encerrar o driver: {e}")
    else:
        print("Nenhum driver para encerrar.")
        return
    
    try:
        proc = psutil.Process(driver_pid)
        print(f"Processo: {proc} atribuido")
        if proc.is_running():
            print(f"Tentando encerrar processo: {proc}")
            proc.kill()  # Força o encerramento do processo
            print(f"Processo do WebDriver com PID {driver_pid} encerrado.")
    except psutil.NoSuchProcess:
        print(f"O processo com PID {driver_pid} não existe.")
    except Exception as e:
        print(f"Ocorreu um erro ao finalizar o driver: {e}")

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
        print(f"Nenhum processo {app_name} encontrado.")
    else:
        print(f"{processos_encerrados} processo(s) {app_name} finalizado(s) com sucesso.")

def cancelar_timers(timers):
    for timer in timers:
        timer.cancel()  # Cancela cada timer ativo
    timers.clear()  # Limpa a lista de timers
