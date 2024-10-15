

import flet as ft
import time
import datetime
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from utils.utils import (copiar_linha, obter_diferenca)
from utils.utils_data import (converter_data, get_formatted_datetime)
from utils.utils_closures import (cancelar_timers, finalizar_custodias_app, finalizar_driver, finalizar_driver_pid)

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

sizeFontRows = 12
spinner_label = ft.Text(value="Iniciar", size=sizeFontRows)
ultima_consulta = ft.Text(f"", size=sizeFontRows, color=ft.colors.GREY_600)
proxima_consulta = ft.Text(f"", size=sizeFontRows, color=ft.colors.GREY_600)

text_style = ft.TextStyle(
    color=ft.colors.GREY_600,
    size=sizeFontRows,
)

date_text_style = ft.TextStyle(
    color=ft.colors.GREY_600,
    size=sizeFontRows,
)

# Datas padrão
hoje = datetime.datetime.now()
data_inicio_default = hoje.strftime("%d/%m/%Y")  # Hoje
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")  # Amanhã

mensagem_nenhum_resultado = None

ordem_colunas = [4, 1, 2, 0, 3]  #Data/Autos/Juizo/Sala/Evento

entry_data_inicio = ft.TextField(
    label="Data Início",
    label_style=date_text_style,
    value=data_inicio_default,
    width=106,
    text_style=date_text_style,
    read_only=True,  # BLOQUEIO DA EDIÇÃO DE DATA
    disabled=True  # Torna o campo não clicável
)
entry_data_fim = ft.TextField(
    label="Data Fim",
    label_style=date_text_style,
    value=data_fim_default,
    width=106,
    text_style=date_text_style,
    read_only=True,  # BLOQUEIO DA EDIÇÃO DE DATA
    disabled=True,  # Torna o campo não clicável
)

start_button = ft.CupertinoFilledButton(
    content=ft.Row(
        controls=[
            # ft.Icon(ft.icons.PLAY_ARROW, size=16),
            ft.Text(spinner_label.value, size=sizeFontRows),  # Inicialmente exibe o valor de spinner_label
        ],
        alignment=ft.MainAxisAlignment.CENTER
    ),
    opacity_on_click=0.5,
    on_click=lambda e: iniciar_consulta(page, start_button),
    width=200,  # Define a largura mínima do botão
    height=49,  # Altura do botão
    border_radius=ft.BorderRadius(4,4,4,4),  # Define o border radius
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

        # spinner_label.value = f"Navegando..."
        # atualizar_texto_botao()

        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")

        time.sleep(1)

        wait = WebDriverWait(driver, 30)
        consultar_por = wait.until(EC.presence_of_element_located((By.ID, "divColConsultarPor")))

        # spinner_label.value = f"Preenchendo..."
        # atualizar_texto_botao()

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

        # spinner_label.value = f"Buscando..."
        # atualizar_texto_botao()

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
        # Garantir que o botão permaneça desabilitado
        start_button.disabled = True
        start_button.update()

        if spinner_label:
            spinner_label.value = f"Agendada"
            atualizar_texto_botao()
            executado = True
            page.update()

        if driver:
            if hasattr(driver, 'service') and hasattr(driver.service, 'process'):
                pid = driver.service.process.pid
                print(f"PID do driver: {pid}")
            finalizar_driver(driver)
        if driver_pid:
            finalizar_driver_pid(driver_pid)


        running_event.clear()
        if not termino_event.is_set():
            print("Agendado")
            agendar_proxima_consulta(page)
        else:
            print("Não Agendado")

        print("Execução finalizada")

def agendar_proxima_consulta(page):
    cancelar_timers(timers)
    next_run = datetime.datetime.now() + datetime.timedelta(seconds=interval)
    delay = (next_run - datetime.datetime.now()).total_seconds()
    timer = threading.Timer(delay, lambda: executar_consulta(page))
    timers.append(timer)
    timer.start()

def main(pg: ft.Page):
    global start_button
    # from splash_screen import splash_screen  # Importa a função do arquivo splash_screen.py
    global driver, driver_pid, entry_data_inicio, entry_data_fim, spinner_label, page, ultima_consulta, proxima_consulta
    page = pg

    def on_window_event(e):
        if e.data == "close":
            page.open(confirm_dialog)

    # Impede o fechamento direto e define o evento personalizado de fechamento
    page.window.prevent_close = True
    page.window.on_event = on_window_event
    pg.window.icon = "C:\\repos\\Github\\WebScrapWithFlet\\assets\\justice_icon.ico"

    def handle_yes(e):
        page.window.destroy()

    def handle_no(e):
        page.close(confirm_dialog)

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Confirmação", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        content=ft.Text("Você realmente quer sair do programa?"),
        actions=[
            ft.ElevatedButton("Sim", on_click=handle_yes),
            ft.OutlinedButton("Não", on_click=handle_no),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

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
                                # spinner_label,
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
    global driver_pid, driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    try:
        driver = webdriver.Firefox(options=options)
        driver_pid = driver.service.process.pid  # Captura o PID do processo do driver
        print(f"Driver inicializado com sucesso com PID: {driver_pid}")
        return driver
    except Exception as e:
        print(f"Erro ao inicializar o driver: {e}")
        return None

def iniciar_consulta(page, button):
    global start_button
    start_button = button  # Armazena o botão para referência
    start_button.disabled = True
    start_button.update()
    alterar_status_execucao("Buscando...")  # Atualiza o texto ao iniciar a consulta
    executar_consulta(page)

###########################

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
            ft.Text(f"Atualizado: {mensagem}", size=sizeFontRows),
            open=True,
            show_close_icon=True,
            duration=interval * 1000 - 5000,
            # close_icon_color=ft.colors.RED
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
                        on_click=lambda e, r=resultado: copiar_linha(r, page, ordem_colunas),
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
    # page.window.maximized = True

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

def windowSize(page):
    page.window.min_width = 1200
    page.window.min_height = 900
    page.window.maximized = True # Maximiza a janela

# Função para atualizar o texto do botão dinamicamente
def atualizar_texto_botao():
    """Atualiza o texto do botão com o valor atual de spinner_label."""
    start_button.content.controls[0] = ft.Text(
        spinner_label.value,
        size=sizeFontRows,
        color=ft.colors.GREY
    )
    start_button.update()  # Atualiza o botão na interface

# Exemplo de como alterar o valor do spinner_label e refletir no botão
def alterar_status_execucao(novo_texto):
    spinner_label.value = novo_texto
    atualizar_texto_botao()  # Chama a função para atualizar o texto do botão

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")

