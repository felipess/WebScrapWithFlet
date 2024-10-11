import flet as ft
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import datetime
import pyperclip
import psutil

# Defina a data de validade
data_validade = datetime.datetime(2024, 12, 8)  # Defina sua data de validade aqui

# Variáveis globais
VERSION = "3.0"
driver = None
driver_pid = None
running_event = threading.Event()
termino_event = threading.Event()
executado = False
interval = 600
resultados_anteriores = []
   
ultima_consulta = ft.Text(f"", size=10, color=ft.colors.GREY)
proxima_consulta = ft.Text(f"", size=10, color=ft.colors.GREY)

# Define o estilo do texto dos itens do dropdown
text_style = ft.TextStyle(size=11)
sizeFontRows = 10

# Definição das datas padrão
hoje = datetime.datetime.now()
data_inicio_default = hoje.strftime("%d/%m/%Y")  # Data de hoje
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")  # Data de amanhã

# Variável global para armazenar a mensagem de nenhum resultado
mensagem_nenhum_resultado = None

# Defina a ordem desejada das colunas
ordem_colunas = [4, 1, 2, 0, 3]  # Ordem original, pode ser ajustada conforme necessário

entry_data_inicio = ft.TextField(
    label="Data Início",
    label_style=text_style,
    value=data_inicio_default,
    width=102,
    text_style=text_style,  # Tamanho da fonte ajustado para 10
    read_only=True  # BLOQUEIO DA EDIÇÃO DE DATA - Campo somente leitura
)
entry_data_fim = ft.TextField(
    label="Data Fim",
    label_style=text_style,
    value=data_fim_default,
    width=102,
    text_style=text_style,  # Tamanho da fonte ajustado para 10
    read_only=True  # BLOQUEIO DA EDIÇÃO DE DATA - Campo somente leitura
)
start_button = ft.ElevatedButton(
    text="Iniciar Consulta",
    icon=ft.icons.PLAY_ARROW,
    on_click=lambda e: iniciar_consulta(page, start_button)  # Passa o botão para a função
)

def verificar_validade():
    if datetime.datetime.now() > data_validade:        
        return False
    return True

def get_formatted_datetime():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S")

def atualizar_rodape():
    global page

def copiar_linha(conteudo_linha):
    """Função para copiar o conteúdo da linha para a área de transferência."""
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
    pyperclip.copy(texto)  # Copia o texto para a área de transferência
    print("Copiado texto: " + texto)

def atualizar_resultados(resultados):
    global page, mensagem_nenhum_resultado, resultados_anteriores

    # Comparar os novos resultados com os anteriores
    if resultados != resultados_anteriores:
        snack_bar = ft.SnackBar(ft.Text("Nova(s) custódia(s) localizada(s)!"), open=True, show_close_icon=True, duration=interval*1000-5000)
        page.overlay.append(snack_bar)
        
        # Maximiza a janela
        page.window.maximized = True  
        windowSize(page)
        # Coloca a janela em primeiro plano
        page.window.to_front()
        
    # Atualizar os resultados anteriores
    resultados_anteriores = resultados.copy()
    
    if page:
        # Atualizar os labels de data/hora
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
                        on_click=lambda e, r=resultado: copiar_linha(r),
                        icon_size=20,
                        tooltip="Copiar"
                    )
                ),
            ]
            rows.append(ft.DataRow(cells=row_cells))

        # Atualizar a página com base na variável
        atualizar_pagina(rows)

def atualizar_pagina(rows):
    global page
    global mensagem_nenhum_resultado

    if page:
        # Remover a mensagem de "Nenhum resultado encontrado" se estiver presente
        if hasattr(page, 'mensagem_nenhum_resultado'):
            if page.mensagem_nenhum_resultado in page.controls:
                page.controls.remove(page.mensagem_nenhum_resultado)
                del page.mensagem_nenhum_resultado        
        
        #Remover a tabela de resultados, se estiver presente
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
                column_spacing=20,
            )

            # Coloque o DataTable dentro de um Container
            data_table_container = ft.Container(
                content=ft.Column(
                    controls=[data_table],
                    scroll=ft.ScrollMode.ALWAYS,
                    height=600,
                ),
                padding=ft.Padding(50, 0, 50, 35),  # Padding de 50 pixels em todos os lados
            )

            page.data_table_container = data_table_container

            # Adicione o contêiner à página
            page.controls.append(page.data_table_container)

        atualizar_rodape()  # Atualiza a nota de rodapé
        page.update()

def get_text_width(text, font_size):
    average_char_width = 7
    return len(text) * average_char_width

def agendar_proxima_consulta():
    next_run = datetime.datetime.now() + datetime.timedelta(seconds=interval)  # Ajusta para 10 segundos
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, lambda: executar_consulta(page)).start()

# Função para verificar e encerrar processos do Firefox e Geckodriver
def finalizar_processos():
    firefox_processes = []
    geckodriver_processes = []
    
    # Verifica todos os processos em execução
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Verifica se o processo tem "firefox" no nome
            if 'firefox' in proc.info['name'].lower():
                firefox_processes.append(proc)
            # Verifica se o processo tem "geckodriver" no nome
            elif 'geckodriver' in proc.info['name'].lower():
                geckodriver_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Função para encerrar processos
    def encerrar_processos(process_list, process_name):
        for proc in process_list:
            try:
                proc.terminate()  # Tenta encerrar o processo educadamente
                time.sleep(3)  # Espera um pouco para ver se o processo encerra
                if proc.is_running():
                    print(f"Processo ainda em execução, forçando encerramento: {proc.pid} ({process_name})")
                    proc.kill()  # Força o encerramento do processo se não encerrar
                    print(f"Processo {process_name} encerrado forçadamente: {proc.pid}")
                else:
                    print(f"Processo {process_name} encerrado: {proc.pid}")
            except psutil.NoSuchProcess:
                print(f"Processo {process_name} já encerrado: {proc.pid}")
            except Exception as e:
                print(f"Erro ao tentar encerrar o processo {process_name}: {e}")
    # Encerra os processos do Firefox
    encerrar_processos(firefox_processes, "Firefox")
    # Encerra os processos do Geckodriver
    encerrar_processos(geckodriver_processes, "Geckodriver")

def finalizar_driver():
    """Finaliza o WebDriver e seus processos associados."""
    global driver, driver_pid
    if driver:
        driver.quit()
    if driver_pid:
        try:
            proc = psutil.Process(driver_pid)
            proc.terminate()  # Tenta encerrar o processo "educadamente"
            time.sleep(3)  # Espera um pouco para ver se o processo encerra
            if proc.is_running():
                print(f"Processo ainda em execução, forçando encerramento: {driver_pid}")
                proc.kill()  # Força o encerramento do processo
                print(f"Processo encerrado forçadamente: {driver_pid}")
        except psutil.NoSuchProcess:
            print(f"Processo do driver já encerrado: {driver_pid}")
        except Exception as e:
            print(f"Erro ao tentar encerrar o processo: {e}")

def finalizar_app_processos():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'CustodiasApp.exe':
            time.sleep(3)
            try:
                proc.terminate()
                time.sleep(3)
                if proc.is_running():
                    proc.kill()  # Força se ainda estiver rodando
                print(f"Processo CustodiasApp.exe encerrado: {proc.pid}")
            except psutil.NoSuchProcess:
                print(f"Processo já encerrado.")

# Função chamada ao fechar o programa
def on_close(e):
    """Evento chamado ao fechar a janela."""
    finalizar_driver()  # Função para finalizar o WebDriver
    finalizar_processos()  # Função para encerrar os processos do Firefox e Geckodriver
    finalizar_app_processos()
    print("Janela fechada. Programa encerrado.")

def initialize_webdriver():    
    global driver_pid
    """Initialize the Selenium WebDriver with necessary options."""
    options = Options()
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--width=1080")  # Define a largura
    options.add_argument("--height=720")  # Define a altura
    global driver

    try:
        driver = webdriver.Firefox(options=options)
        driver_pid = driver.service.process.pid  # Captura o PID do processo do driver
        print(f"Driver inicializado com sucesso com PID: {driver_pid}")
        return driver
    except Exception as e:
        print(f"Erro ao inicializar o driver: {e}")
        return None

def clear_and_send_keys(element, value):
    """Clear an input element and send keys."""
    element.clear()
    element.send_keys(value)

def iniciar_consulta(page, button):
    start_button.disabled = True # Desabilita o botão para evitar cliques duplicados
    button.text = "Em execução..."  # Muda o texto do botão
    start_button.update()
    spinner_label.value = f"Pesquisa iniciada..."
    page.update()
    executar_consulta(page)

def windowSize(page):
    page.window.min_width = 1000
    page.window.width = 1000
    page.window.height = 1000
    page.window.min_height = 500


def executar_consulta(page):
    global driver, driver_pid, executado, mensagem_nenhum_resultado, resultados_anteriores
    print("Consulta Iniciada...")

    driver = initialize_webdriver()
    if not driver:
        return  # Exit if driver initialization fails

    mensagem_nenhum_resultado = None  # Reseta a mensagem de nenhum resultado
    snack_bar = ft.SnackBar(ft.Text(""), open=False)
    page.overlay.append(snack_bar)

    running_event.set()
    
    try:
        resultados = []
        titulos = ["Data/Hora", "Autos", "Classe", "Processo", "Parte", "Status", "Sistema"]
        
        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")

        time.sleep(1)
        
        wait = WebDriverWait(driver, 30)
        consultar_por = wait.until(EC.presence_of_element_located((By.ID, "divColConsultarPor")))
        time.sleep(1)

        dropdown_button = consultar_por.find_element(By.CLASS_NAME, "dropdown-toggle")
        dropdown_button.click()
        time.sleep(1)

        # Aguarde a lista de opções ser exibida
        options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".dropdown-menu .dropdown-item")))

        for option in options:
            if "Intervalo de Data e Competência" in option.text:
                option.click()
                print("Consultando por Intervalo de Data e Competência")
                break

        time.sleep(1)

        data_inicio = entry_data_inicio.value.strip()
        data_fim = entry_data_fim.value.strip()

        print(f"Data de início: {data_inicio}, Data de fim: {data_fim}")

        campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtDataInicio")))
        driver.execute_script("arguments[0].scrollIntoView(true);", campo_data_inicio)
        time.sleep(1)  # Adicione um pequeno atraso, se necessário
        campo_data_inicio.clear()
        campo_data_inicio.send_keys(data_inicio)

        time.sleep(1)

        campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtDataTermino")))
        campo_data_fim.clear()
        campo_data_fim.send_keys(data_fim)

        time.sleep(1)
        
        botao_consultar = wait.until(EC.element_to_be_clickable((By.ID, "btnConsultar")))
        botao_consultar.click()

        time.sleep(2)


        # Verificar se há a mensagem de "Nenhum resultado encontrado"
        mensagem_erro = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
        if "Nenhum resultado encontrado" in mensagem_erro.text:
            print(f"Nenhum resultado encontrado.")
            

        # Esperar até que a tabela esteja presente
        tabela = wait.until(EC.presence_of_element_located((By.ID, "tblAudienciasEproc")))
        linhas = tabela.find_elements(By.TAG_NAME, "tr")

        for linha in linhas:
            texto_normalizado = linha.text.lower()
            if any(termo in texto_normalizado for termo in ["custódia", "custodia"]):
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
        atualizar_rodape()       

    except Exception as e:
        print(f"Erro geral: {e}")
        resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se houver um erro geral
        atualizar_resultados(resultados)
        atualizar_rodape()  
        return

        
    finally:        
        start_button.disabled = True
        start_button.update()

        if spinner_label:
            spinner_label.value = ""
            executado = True
            page.update()
        
        if driver:
            driver.quit()

        if driver_pid:
            finalizar_driver()  
        
        running_event.clear()
        if not termino_event.is_set():
            agendar_proxima_consulta()
        print("Consulta finalizada")

def main(pg: ft.Page):
    global driver, driver_pid, entry_data_inicio, entry_data_fim, spinner_label, page, ultima_consulta, proxima_consulta 
    # text_area
    page = pg
    page.on_close = on_close  
    windowSize(page)

    page.title = f"Pesquisa automatizada - Circunscrições da JF do Paraná - Versão {VERSION}"
    
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
            padding=ft.Padding(50, 50, 50, 50),  # Padding de 50 pixels em todos os lados
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "Consulta de audiências de custódia",
                            size=20,
                            weight="bold"
                        ),
                        alignment=ft.Alignment(0, 0.5),
                        padding=ft.Padding(0, 0, 0, 20)
                    ),
                    ft.Container(
                        content=ft.ResponsiveRow(
                            controls=[
                                ft.Container(
                                    content=entry_data_inicio,
                                    col={"sm": 2, "md": 2, "lg": 2, "xl": 2},  # Campos de data menores
                                ),
                                ft.Container(
                                    content=entry_data_fim,
                                    col={"sm": 2, "md": 2, "lg": 2, "xl": 2},  # Campos de data menores
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,
                        ),
                        padding=ft.Padding(0, 0, 0, 0)
                    ),
                    ft.Container(
                        padding=ft.Padding(0, 0, 0, 0)
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[spinner_label],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        padding=ft.Padding(0, 0, 0, 0)
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ultima_consulta,
                                proxima_consulta,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        padding=ft.Padding(0, 0, 0, 0)
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[start_button],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        padding=ft.Padding(0, 0, 0, 20)  # Ajuste o padding conforme necessário
                    ),
                ]
            )
        )
    )

    page.update()
    atualizar_rodape()  # Atualiza a nota de rodapé

if __name__ == "__main__":
    ft.app(target=main)