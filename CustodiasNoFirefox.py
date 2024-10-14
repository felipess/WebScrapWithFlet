import flet as ft
import time
import pyperclip
import datetime
import threading
import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from utils.utils import (copiar_linha, obter_diferenca)
from utils.data_utils import (converter_data, get_formatted_datetime)

data_validade = datetime.datetime(2024, 12, 8)  # Data de validade

# Variáveis globais
VERSION = "4.2"
driver = None
driver_pid = None
running_event = threading.Event()
termino_event = threading.Event()
executado = False
interval = 900
resultados_anteriores = []
timers = []
snackbars = []


termos_buscados = ["custódia", "custodia"]
   
ultima_consulta = ft.Text(f"", size=11, color=ft.colors.GREY_600)
proxima_consulta = ft.Text(f"", size=11, color=ft.colors.GREY_600)

text_style = ft.TextStyle(
    color=ft.colors.GREY_600,  
    size=11,  
)
sizeFontRows = 10

# Datas padrão
hoje = datetime.datetime.now()
data_inicio_default = hoje.strftime("%d/%m/%Y")  # Hoje
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")  # Amanhã

mensagem_nenhum_resultado = None

ordem_colunas = [4, 1, 2, 0, 3]  #Data/Autos/Juizo/Sala/Evento

entry_data_inicio = ft.TextField(
    label="Data Início",
    label_style=text_style,
    value=data_inicio_default,
    width=102,
    text_style=text_style, 
    read_only=True,  # BLOQUEIO DA EDIÇÃO DE DATA 
    disabled=True  # Torna o campo não clicável
)
entry_data_fim = ft.TextField(
    label="Data Fim",
    label_style=text_style,
    value=data_fim_default,
    width=102,
    text_style=text_style,
    read_only=True,  # BLOQUEIO DA EDIÇÃO DE DATA 
    disabled=True,  # Torna o campo não clicável
)

start_button = ft.CupertinoFilledButton(
    content=ft.Row(  
        controls=[
            ft.Icon(ft.icons.PLAY_ARROW, size=16),  
            ft.Text(" Iniciar Consulta", size=12),  
        ],
        alignment=ft.MainAxisAlignment.CENTER  
    ),
    opacity_on_click=0.5,
    on_click=lambda e: iniciar_consulta(page, start_button),  
)

def executar_consulta(page):
    global driver, driver_pid, executado, mensagem_nenhum_resultado, resultados_anteriores
    executado = False
    if not verificar_validade():
        print("Data de validade atingida. Encerrando consultas.")
        return
    
    print("inicializando webdriver...")

    driver = initialize_webdriver()
    if not driver:
        return  # Exit if driver initialization fails
    mensagem_nenhum_resultado = None  # Reseta a mensagem
    snack_bar = ft.SnackBar(ft.Text(""), open=False)
    page.overlay.append(snack_bar)

    running_event.set()
    
    try:
        resultados = []
        titulos = ["Data/Hora", "Autos", "Classe", "Processo", "Parte", "Status", "Sistema"]

        spinner_label.value = f"Navegando para o site da JFPR..."
        page.update()
        
        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")

        time.sleep(1)
       
        wait = WebDriverWait(driver, 30)
        consultar_por = wait.until(EC.presence_of_element_located((By.ID, "divColConsultarPor")))

        spinner_label.value = f"Preenchendo campos..."
        page.update()

        dropdown_button = consultar_por.find_element(By.CLASS_NAME, "dropdown-toggle")
        dropdown_button.click()

        options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".dropdown-menu .dropdown-item")))

        for option in options:
            if "Intervalo de Data e Competência" in option.text:
                option.click()
                print("Consultando por Intervalo de Data e Competência")
                break

        data_inicio = entry_data_inicio.value.strip()
        data_fim = entry_data_fim.value.strip()

        campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtDataInicio")))
        driver.execute_script("arguments[0].scrollIntoView(true);", campo_data_inicio)
        campo_data_inicio.clear()
        campo_data_inicio.send_keys(data_inicio)

        campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtDataTermino")))
        campo_data_fim.clear()
        campo_data_fim.send_keys(data_fim)
        
        botao_consultar = wait.until(EC.element_to_be_clickable((By.ID, "btnConsultar")))
        botao_consultar.click()

        spinner_label.value = f"Buscando dados..."
        page.update()

        # Verificar se há a mensagem de "Nenhum resultado encontrado"
        mensagem_erro = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
        if "Nenhum resultado encontrado" in mensagem_erro.text:
            print(f"Nenhum resultado encontrado.")

        # Esperar até que a tabela esteja presente
        tabela = wait.until(EC.presence_of_element_located((By.ID, "tblAudienciasEproc")))
        linhas = tabela.find_elements(By.TAG_NAME, "tr")

        for linha in linhas:
            texto_normalizado = linha.text.lower()
            if any(termo in texto_normalizado for termo in termos_buscados):
                tds = linha.find_elements(By.TAG_NAME, "td")
                conteudo_linha = []
                erro_encontrado = False
                for td in tds:
                    td_html = td.get_attribute('innerHTML')
                    td_soup = BeautifulSoup(td_html, 'html.parser')
                    td_text = td_soup.get_text(separator=" ").split("Classe:")[0].strip()  
                    if "ocorreu um erro" in td_text.lower():
                        erro_encontrado = True
                        break
                    conteudo_linha.append(td_text)
                if not erro_encontrado and len(conteudo_linha) == len(titulos):
                    resultados.append(conteudo_linha)

        if not resultados:
            resultados = []
            mensagem_nenhum_resultado = "Nenhum resultado encontrado."

        atualizar_resultados(resultados)

    except Exception as e:
        spinner_label.value = f"Erro: {e}"
        page.update()
        print(f"Erro geral: {e}")
        resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se houver um erro geral
        atualizar_resultados(resultados)
        finalizar_custodias_app()
        return
 
    finally:        
        start_button.disabled = True
        start_button.update()

        if spinner_label:
            spinner_label.value = ""
            executado = True
            page.update()
        
        if driver:
            if hasattr(driver, 'service') and hasattr(driver.service, 'process'):
                pid = driver.service.process.pid
                print(f"PID do driver: {pid}")
            driver.quit()
            print(f"Encerrado driver: {driver} e PID: {pid}")
            driver = None  # Reseta o driver para evitar chamadas repetidas

        if driver_pid:
            finalizar_driver()  
            # driver_pid.quit()
            # driver_pid = None  # Reseta o driver para evitar chamadas repetidas

        
        running_event.clear()
        # if not termino_event.is_set():
        #     print("Agendado")
        agendar_proxima_consulta(page)
        # print("Consulta finalizada")



def agendar_proxima_consulta(page):
    cancelar_timers()
    next_run = datetime.datetime.now() + datetime.timedelta(seconds=interval)
    delay = (next_run - datetime.datetime.now()).total_seconds()

    timer = threading.Timer(delay, lambda: executar_consulta(page))
    timers.append(timer)
    timer.start()

# Encerrar Firefox e Geckodriver
def finalizar_processos():
    # Obtém todos os processos do Firefox e GeckoDriver
    firefox_processes = [p for p in psutil.process_iter(['name']) if 'firefox' in p.info['name'].lower()]
    geckodriver_processes = [p for p in psutil.process_iter(['name']) if 'geckodriver' in p.info['name'].lower()]

    # Encerra os processos do Firefox individualmente
    for proc in firefox_processes:
        try:
            print(f"Encerrando processo do Firefox: {proc.pid}")
            proc.terminate()
            #proc.wait(timeout=5)  # Aguarda até 5 segundos para o processo encerrar
        except psutil.NoSuchProcess:
            print(f"Firefox - O processo {proc.pid} não existe.")
        except psutil.TimeoutExpired:
            print(f"Firefox - O processo {proc.pid} não encerrou a tempo. Tentando encerrar forçosamente.")
            proc.kill()  # Força o encerramento

    # Encerra os processos do GeckoDriver individualmente
    for proc in geckodriver_processes:
        try:
            print(f"Encerrando processo do GeckoDriver: {proc.pid}")
            proc.terminate()
            #proc.wait(timeout=5)  # Aguarda até 5 segundos para o processo encerrar
        except psutil.NoSuchProcess:
            print(f"GeckoDriver - O processo {proc.pid} não existe.")
        except psutil.TimeoutExpired:
            print(f"GeckoDriver - O processo {proc.pid} não encerrou a tempo. Tentando encerrar forçosamente.")
            proc.kill()  # Força o encerramento

def finalizar_driver():
    global driver, driver_pid
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
                #proc.wait(timeout=2)
                processos_encerrados += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if processos_encerrados == 0:
        print(f"Nenhum processo {app_name} encontrado.")
    else:
        print(f"{processos_encerrados} processo(s) {app_name} finalizado(s) com sucesso.")

def cancelar_timers():
    for timer in timers:
        timer.cancel()  # Cancela cada timer ativo
    timers.clear()  # Limpa a lista de timers

# Função chamada ao fechar o programa
def on_close(e):
    # termino_event.is_set()
    # time.sleep(1)
    page.window_close()  # Fecha a janela de forma explícita
    exit(0)  # Garante o encerramento completo do programa
    cancelar_timers()  # Cancela os timers antes de fechar
    finalizar_processos()  # Função para encerrar os processos do Firefox e Geckodriver
    finalizar_driver()  # Encerrar o driver do Selenium

    running_event.clear()
    termino_event.clear()

    # for i in range(len(timers) - 1, -1, -1):  # Itera sobre os timers de trás para frente
    #     remover_agendamento(i)  # Remove cada timer
    finalizar_custodias_app()


def main(pg: ft.Page):
    # from splash_screen import splash_screen  # Importa a função do arquivo splash_screen.py
    pg.on_close = on_close  
    global driver, driver_pid, entry_data_inicio, entry_data_fim, spinner_label, page, ultima_consulta, proxima_consulta 
    page = pg
    # splash_screen(page)

    windowSize(page)

    page.title = f"Pesquisa custódias JFPR - Versão {VERSION} - Valido até {converter_data(data_validade)}"
    
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    if not verificar_validade():
        pg.add(ft.Text("Este programa não é mais válido - permissão expirada. Entre em contato com o desenvolvedor feliped@mpf.mp.br pelo Zoom."))
        pg.update()
        return      

    spinner_label = ft.Text("", size=10, color=ft.colors.BLUE_500)
    page.update()

    page.add(
        ft.Container(
            padding=ft.Padding(5, 20, 5, 20),  # Padding ajustado
            content=ft.Column(
                controls=[
                    # Título no topo
                    ft.Container(
                        content=ft.Text(
                            "Consulta de audiências de custódia",
                            size=20,
                            weight="bold"
                        ),
                        alignment=ft.Alignment(0, 0),  # Centralizado horizontalmente
                        padding=ft.Padding(0, 0, 0, 0)  # Espaço abaixo do título
                    ),
                    # Row para todo o conteúdo centralizado
                    ft.Row(
                        controls=[
                            # Campo de Data Início
                            ft.Container(
                                content=entry_data_inicio,
                                col={"sm": 2, "md": 2, "lg": 2, "xl": 2},
                            ),
                            # Campo de Data Fim
                            ft.Container(
                                content=entry_data_fim,
                                col={"sm": 2, "md": 2, "lg": 2, "xl": 2},
                            ),
                            # Botão Start
                            start_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,  
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),                    
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                spinner_label,
                                ultima_consulta,
                                proxima_consulta,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        )
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=ft.Text(
                            "Resultados",
                            size=18,
                            weight="bold"
                        ),
                        alignment=ft.Alignment(0, 0),  
                        padding=ft.Padding(0, 0, 0, 0) 
                    ),
                ],
                alignment=ft.CrossAxisAlignment.CENTER,
                
                spacing=20,
            )
        )
    )
    page.update()

def initialize_webdriver():    
    global driver_pid
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--width=1080")
    options.add_argument("--height=720")
    global driver

    try:
        driver = webdriver.Firefox(options=options)
        driver_pid = driver.service.process.pid  # Captura o PID do processo do driver
        print(f"Driver inicializado com sucesso com PID: {driver_pid}")
        return driver
    except Exception as e:
        print(f"Erro ao inicializar o driver: {e}")
        finalizar_driver()
        return None

def iniciar_consulta(page, button):
    start_button.disabled = True # Desabilita o botão para evitar cliques duplicados
    button.content.controls[1] = ft.Text(" Em execução...", size=12, color=ft.colors.GREY)  # Atualiza apenas o texto
    button.update()  # Atualiza o botão para refletir a mudança
    spinner_label.value = f"Pesquisa iniciada..."
    page.update()
    executar_consulta(page)


###########################

def copiar_linha(conteudo_linha, page):
    conteudo_ordenado = [conteudo_linha[i] for i in ordem_colunas]

    if len(conteudo_ordenado) > 0:  # Verifica se a coluna 0 existe
        coluna_0_texto = conteudo_ordenado[0]

        if "Observação:" in coluna_0_texto:
            coluna_0_texto = coluna_0_texto.split("Observação:")[0].strip() # Remove "Observação:" e tudo o que vem depois       
        conteudo_ordenado[0] = coluna_0_texto  

    if len(conteudo_ordenado) > 4:  # Verifica se a coluna 4 existe
        coluna_4_texto = conteudo_ordenado[4]
        
        conteudo_ordenado[4] = coluna_4_texto  # Atualiza a coluna 4 com o texto modificado

    # Formata o texto final
    texto = ' - '.join(conteudo_ordenado)  # Une o conteúdo da linha em uma string

    # Remove "Evento:" do texto, se presente
    texto = texto.replace("Evento:", "").strip()
    
    # Remove "Sala:" e tudo que vem depois
    if "Sala:" in texto:
        texto = texto.split("- Sala:")[0].strip()
    
    # Copia o texto para a área de transferência
    pyperclip.copy(texto)
    exibir_alerta_js(page, "Texto copiado para a área de transferência.")
    print(f"Copiado texto: {texto}")


def verificar_validade():
    return datetime.datetime.now() <= data_validade

def atualizar_resultados(resultados):
    global page, resultados_anteriores
    diferencas = obter_diferenca(resultados, resultados_anteriores)
    if diferencas:
        mensagens = []
        for diferenca in diferencas:
            if isinstance(diferenca[1], list):
                valores_formatados = ", ".join(map(str, diferenca[1]))
            else:
                valores_formatados = str(diferenca[1])
            mensagens.append(f"{valores_formatados}")
        mensagem = " - ".join(mensagens)

        snack_bar = ft.SnackBar(
            ft.Text(f"Atualização: {mensagem}"),
            open=True,
            show_close_icon=True,
            duration=interval * 1000 - 5000,
            close_icon_color=ft.colors.RED
        )

        page.overlay.append(snack_bar)
        page.window.maximized = True
        page.window.to_front()
    resultados_anteriores = resultados.copy()
    
    if page:
        ultima_consulta.value = f"Última consulta: {get_formatted_datetime()}" 
        proxima_consulta.value = f"Próxima consulta: {datetime.datetime.now() + datetime.timedelta(seconds=interval):%H:%M:%S}"

        # Preparar a tabela com resultados
        rows = []
        for resultado in resultados:
            row_cells = [
                ft.DataCell(ft.Text(resultado[0], size=sizeFontRows)),
                ft.DataCell(ft.Text(resultado[1], size=sizeFontRows)),
                ft.DataCell(ft.Text(resultado[2], size=sizeFontRows)),
                ft.DataCell(ft.Text(resultado[3], size=sizeFontRows)),
                ft.DataCell(ft.Text(resultado[4], size=sizeFontRows)),
                ft.DataCell(
                    ft.IconButton(
                        icon=ft.icons.CONTENT_COPY,
                        icon_color=ft.colors.BLUE,
                        on_click=lambda e, r=resultado: copiar_linha(r, page),
                        icon_size=20,
                        tooltip="Copiar"
                    )
                ),
            ]
            
            rows.append(ft.DataRow(cells=row_cells))
        atualizar_pagina(rows)

def atualizar_pagina(rows):
    global page
    global mensagem_nenhum_resultado
    page.window.maximized = True


    if page:
        # Remover a mensagem de "Nenhum resultado encontrado"
        if hasattr(page, 'mensagem_nenhum_resultado'):
            if page.mensagem_nenhum_resultado in page.controls:
                page.controls.remove(page.mensagem_nenhum_resultado)
                del page.mensagem_nenhum_resultado        
        
        #Remover a tabela de resultados
        if hasattr(page, 'data_table_container') and page.data_table_container in page.controls:
            page.controls.remove(page.data_table_container)

        
        if mensagem_nenhum_resultado != None:
            if not hasattr(page, 'mensagem_nenhum_resultado'):
                page.mensagem_nenhum_resultado = ft.Text(mensagem_nenhum_resultado, size=sizeFontRows)
            
            if page.mensagem_nenhum_resultado not in page.controls:
                page.controls.append(page.mensagem_nenhum_resultado)
        else:
            data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data/Hora", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Autos", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Juízo", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Sala", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Evento", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Ações", size=sizeFontRows)),
                ],
                rows=rows,
                data_row_min_height=60,
                data_row_max_height=80,
                #width="100%",  ####aqui
            )

            # Coloque o DataTable dentro de um Container
            data_table_container = ft.Container(
                content=ft.Column(
                    controls=[data_table],
                    scroll=ft.ScrollMode.ALWAYS,
                    height=650,
                ),
                padding=ft.Padding(0, 10, 0, 10),  
            )

            page.data_table_container = data_table_container
            page.controls.append(page.data_table_container)
        page.update()

def get_text_width(text, font_size):
    average_char_width = 7
    return len(text) * average_char_width


def windowSize(page):
    page.window.min_width = 1200
    page.window.min_height = 900
    page.window.maximized = True # Maximiza a janela

def exibir_alerta_js(page, mensagem):
    alerta = ft.SnackBar(ft.Text(mensagem), open=True, duration=2000)
    page.overlay.append(alerta)
    page.overlay.extend(snackbars)  # Atualiza a lista de overlays
    page.update()

if __name__ == "__main__":
    ft.app(target=main)