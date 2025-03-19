import os
import sys
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
from selenium.common.exceptions import WebDriverException

from logs.config_log import configurar_logging 
logger = configurar_logging()

data_validade = datetime.datetime(2050, 4, 22)  # Data de validade

# Variáveis globais
VERSION = "4.3"
driver = None
driver_pid = None
running_event = threading.Event()
termino_event = threading.Event()
executado = False
interval = 600
resultados_anteriores = []
timers = []
snackbars = []
termos_buscados = ["custódia", "custodia"]

sizeFontRows = 12
spinner_label = ft.Text(value="Iniciar", size=sizeFontRows)
ultima_consulta = ft.Text(f"", size=sizeFontRows, color=ft.colors.GREY_600)
proxima_consulta = ft.Text(f"", size=sizeFontRows, color=ft.colors.GREY_600)

ultima_verificacao_ativa = datetime.datetime.now()
tempo_maximo_inatividade = interval * 1.5  # 1.5x o intervalo normal

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
# hoje = '2024-11-22'
# hoje = datetime.datetime.strptime(hoje, "%Y-%m-%d")  # Converte a string para datetime


data_inicio_default = hoje.strftime("%d/%m/%Y")  # Hoje
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")  # Amanhã

mensagem_nenhum_resultado = None

ordem_colunas = [4, 1, 2, 0, 3, 5]  #Evento/Autos/Juizo/Data/Sala/Status

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
    global driver, driver_pid, executado, mensagem_nenhum_resultado, resultados_anteriores, ultima_verificacao_ativa
    executado = False
    ultima_verificacao_ativa = datetime.datetime.now()
    
    if not verificar_validade():
        logger.warning("Data de validade atingida. Encerrando consultas.")
        return

    logger.info("inicializando webdriver...")

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

        #driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")
        if not acessar_url_com_retry("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias"):
            logger.error("Não foi possível acessar o site após várias tentativas")
            mensagem_nenhum_resultado = "Não foi possível acessar o site. Verifique sua conexão ou tente novamente mais tarde."
            atualizar_resultados([])
            page.update()
            finalizar_custodias_app()
            return

        time.sleep(1)

        wait = WebDriverWait(driver, 30)
        consultar_por = wait.until(EC.presence_of_element_located((By.ID, "divColConsultarPor")))

        dropdown_button = consultar_por.find_element(By.CLASS_NAME, "dropdown-toggle")
        dropdown_button.click()

        options = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".dropdown-menu .dropdown-item")))

        for option in options:
            if "Intervalo de Data e Competência" in option.text:
                option.click()
                logger.info("Consultando por Intervalo de Data e Competência")
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

        # Verificar se há a mensagem de "Nenhum resultado encontrado"
        mensagem_erro = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
        if "Nenhum resultado encontrado" in mensagem_erro.text:
            logger.warning(f"Nenhum resultado encontrado.")
            mensagem_nenhum_resultado = "Nenhum resultado encontrado."

        # Esperar até que a tabela esteja presente
        tabela = WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.ID, "tblAudienciasEproc"))
        )
        
        linhas = tabela.find_elements(By.TAG_NAME, "tr")

        # Verifica se há resultados
        if len(linhas) == 0:
            # Caso não tenha linhas, significa que não há resultados
            logger.warning("Nenhum resultado encontrado.")
            mensagem_nenhum_resultado = "Nenhum resultado encontrado."
        else: 
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

                        # Verifica se há um erro na linha
                        if "ocorreu um erro" in td_text.lower():
                            erro_encontrado = True
                            break

                        # Adiciona apenas se não for um termo indesejado
                        # if td_text.lower() not in ["realizada", "e-proc"]:
                        if td_text.lower() not in ["e-proc"]:
                            conteudo_linha.append(td_text)

                    # Garante que a linha tenha o tamanho correto após a filtragem
                    if not erro_encontrado and len(conteudo_linha) == len(titulos) - 1:
                        resultados.append(conteudo_linha)
                
        if resultados:
            atualizar_resultados(resultados)
        else:
            resultados = []
            mensagem_nenhum_resultado = "Nenhum resultado encontrado."
            logger.warning("Nenhum resultado válido encontrado após processamento das linhas.")
            
        logger.debug("Resultado Final:")
        logger.debug(resultados)
        atualizar_resultados(resultados)

    except Exception as e:
        spinner_label.value = f"Erro: {e}"
        logger.critical(f"Erro geral: {e}")
        mensagem_nenhum_resultado = "Nenhum resultado encontrado."
        logger.warning("Tabela não encontrada, o que indica que não há resultados.")
        atualizar_resultados([])  # Atualiza a página com uma lista vazia ou uma mensagem de erro
        page.update()
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
                logger.info(f"PID do driver: {pid}")
            finalizar_driver(driver)
        if driver_pid:
            finalizar_driver_pid(driver_pid)

        running_event.clear()
        
        if not termino_event.is_set():
            logger.debug("Agendado")
            agendar_proxima_consulta(page)
        else:
            logger.debug("Não Agendado")

        logger.info("Execução finalizada")

def agendar_proxima_consulta(page):
    global timers
    cancelar_timers(timers)  # Cancela timers antigos
    next_run = datetime.datetime.now() + datetime.timedelta(seconds=interval)
    delay = (next_run - datetime.datetime.now()).total_seconds()
    logger.info(f"Próxima execução agendada para: {next_run.strftime('%d/%m/%Y %H:%M:%S')}")  # Log
    
    # Adiciona um timer para verificação de inatividade a cada 30 segundos
    verificacao_timer = threading.Timer(30, lambda: verificar_inatividade(page))
    timers.append(verificacao_timer)
    verificacao_timer.start()
    
    # Timer normal para a próxima consulta
    timer = threading.Timer(delay, lambda: executar_consulta(page))
    timers.append(timer)
    timer.start()

def verificar_inatividade(page):
    global ultima_verificacao_ativa, timers
    
    agora = datetime.datetime.now()
    tempo_inativo = (agora - ultima_verificacao_ativa).total_seconds()
    
    # Atualiza o timestamp da última verificação
    ultima_verificacao_ativa = agora
    
    # Se estiver inativo por mais tempo que o limite, reinicia a consulta
    if tempo_inativo > tempo_maximo_inatividade and not running_event.is_set():
        logger.warning(f"Detectada possível suspensão do sistema. Tempo inativo: {tempo_inativo:.2f} segundos")
        
        # Cancela todos os timers atuais
        cancelar_timers(timers)
        
        # Reinicia a consulta imediatamente
        logger.info("Reiniciando consultas após suspensão...")
        executar_consulta(page)
    else:
        # Agenda a próxima verificação se o programa ainda estiver em execução
        if not termino_event.is_set():
            verificacao_timer = threading.Timer(30, lambda: verificar_inatividade(page))
            timers.append(verificacao_timer)
            verificacao_timer.start()

def main(pg: ft.Page):
    global start_button
    global driver, driver_pid, entry_data_inicio, entry_data_fim, spinner_label, page, ultima_consulta, proxima_consulta
    page = pg

    def on_window_event(e):
        if e.data == "close":
            page.open(confirm_dialog)

    page.window.prevent_close = True
    page.window.on_event = on_window_event
    
    # Defina o ícone dinamicamente
    icon_path = get_asset_path('justice_icon.ico')
    pg.window.icon = icon_path

    def handle_yes(e):
        page.close(confirm_dialog)
        page.open(pageWait)
        time.sleep(1)
        try:
            logger.info("Destruindo programa...")
            page.window.destroy()
        except:
            logger.error(f"Erro ao fechar com close(): {e}")
            

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

    pageWait = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aguarde", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        content=ft.Text("Finalizando programa...", text_align=ft.TextAlign.CENTER),
    )
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
                        spacing=5,
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

                spacing=10,
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
        logger.info(f"Driver inicializado com sucesso com PID: {driver_pid}")
        return driver
    except Exception as e:
        logger.error(f"Erro ao inicializar o driver: {e}")
        return None

def iniciar_consulta(page, button):
    global start_button
    start_button = button  # Armazena o botão para referência
    start_button.disabled = True
    start_button.update()
    alterar_status_execucao("Buscando...")  # Atualiza o texto ao iniciar a consulta
    executar_consulta(page)

def verificar_validade():
    return datetime.datetime.now() <= data_validade


def atualizar_resultados(resultados):
    global page, resultados_anteriores, mensagem_nenhum_resultado

    # Verifica se houve diferença nos resultados
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
        )

        page.overlay.append(snack_bar)
        page.window.maximized = True
        page.window.to_front()
    resultados_anteriores = resultados.copy()

    if page:
        ultima_consulta.value = f"Última consulta: {get_formatted_datetime()}"
        proxima_consulta.value = f"Próxima consulta: {datetime.datetime.now() + datetime.timedelta(seconds=interval):%H:%M:%S}"
        
        # Verificar se o contêiner de tabelas já existe
        if not hasattr(page, 'data_table_container'):
            page.data_table_container = ft.Container(
                content=ft.Column(
                    spacing=20,  # Ajuste de espaçamento entre as tabelas
                ),
                width=1750,  # Define a largura máxima do Container
            )
            # Adicionar o contêiner de tabelas na página pela primeira vez
            page.controls.append(page.data_table_container)

        page.data_table_container.content.controls.clear()  # Limpa as tabelas antigas

        # Agrupar os resultados por status
        resultados_por_status = {}
        for resultado in resultados:
            status = resultado[5]  # Considerando que o status está na coluna de índice 5
            if status not in resultados_por_status:
                resultados_por_status[status] = []
            resultados_por_status[status].append(resultado)

        # Remover a mensagem de "Nenhum resultado encontrado"
        if hasattr(page, 'mensagem_nenhum_resultado'):
            if page.mensagem_nenhum_resultado in page.controls:
                page.controls.remove(page.mensagem_nenhum_resultado)
                del page.mensagem_nenhum_resultado

        # Verificar se existe algum resultado
        if mensagem_nenhum_resultado != None:
            if not hasattr(page, 'mensagem_nenhum_resultado'):  # Verifica se o controle não foi adicionado ainda
                # Criando a caixa de mensagem formatada
                page.mensagem_nenhum_resultado = ft.Container(
                    content=ft.Text(mensagem_nenhum_resultado, size=14),  # Texto na caixa
                    padding=ft.Padding(50, 10, 50, 10),  # Adiciona padding dentro da caixa
                    border=ft.border.all(2),
                    border_radius=8  # Bordas arredondadas
                )

            # Verifica se a mensagem não foi adicionada na página
            if page.mensagem_nenhum_resultado not in page.controls:
                page.controls.append(page.mensagem_nenhum_resultado)
        else:
            # Criar o cabeçalho uma única vez
            table_columns = [
                ft.DataColumn(ft.Text("Data/Hora", size=sizeFontRows)),
                ft.DataColumn(ft.Text("Autos", size=sizeFontRows)),
                ft.DataColumn(ft.Text("Juízo", size=sizeFontRows)),
                ft.DataColumn(ft.Text("Sala", size=sizeFontRows)),
                ft.DataColumn(ft.Text("Evento", size=sizeFontRows)),
                ft.DataColumn(ft.Text("Status", size=sizeFontRows)),
                ft.DataColumn(ft.Text("Ações", size=sizeFontRows)),
            ]

            # Mapeamento de índices para controle da ordem de criação das tabelas
            status_indices = {
                "REDESIGNADA": 1,
                "DESIGNADA": 2,
                "REALIZADA": 3  # "REALIZADA" recebe o maior índice para ser criada por último
            }

            status_colors = {
                "REDESIGNADA": ft.colors.RED_300,
                "DESIGNADA": ft.colors.BLUE_300,
                "REALIZADA": ft.colors.GREY_200,
            }

            # Criar uma lista para armazenar as tabelas
            tabelas_ordenadas = []

            # Ordenar os status por seu índice de criação
            for status in sorted(resultados_por_status.keys(), key=lambda s: status_indices.get(s, float('inf'))):
                resultados_status = resultados_por_status[status]
                bordercolor = status_colors.get(status, ft.colors.GREY)  # Cor padrão

                # Criar as linhas da tabela
                rows = []
                for resultado in resultados_status:
                    row_cells = [
                        ft.DataCell(ft.Text(resultado[0], size=sizeFontRows, width=80)),
                        ft.DataCell(ft.Text(resultado[1], size=sizeFontRows, width=190)),
                        ft.DataCell(ft.Text(resultado[2], size=sizeFontRows)),
                        ft.DataCell(ft.Text(resultado[3], size=sizeFontRows)),
                        ft.DataCell(ft.Text(resultado[4], size=sizeFontRows)),
                        ft.DataCell(ft.Text(resultado[5], size=sizeFontRows, width=110)),
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

                # Criar a tabela
                data_table = ft.DataTable(
                    columns=table_columns,  # Cabeçalho configurado aqui
                    rows=rows,
                    data_row_min_height=60,
                    data_row_max_height=80,
                    border=ft.border.all(2, bordercolor),
                    border_radius=10,
                    heading_row_color=ft.colors.BLACK12,
                    heading_row_height=50,
                    data_row_color={ft.ControlState.HOVERED: "0x30FF0000"},
                    divider_thickness=0,
                )

                tabelas_ordenadas.append(data_table)

            page.data_table_container.content.controls.extend(tabelas_ordenadas)

            page.update()

def windowSize(page):
    page.window.min_width = 1200
    page.window.min_height = 900
    page.window.maximized = True # Maximiza a janela
    page.scroll = ft.ScrollMode.ALWAYS

def atualizar_texto_botao():
    """Atualiza o texto do botão com o valor atual de spinner_label."""
    start_button.content.controls[0] = ft.Text(
        spinner_label.value,
        size=sizeFontRows,
        color=ft.colors.GREY
    )
    start_button.update()  # Atualiza o botão na interface

def alterar_status_execucao(novo_texto):
    spinner_label.value = novo_texto
    atualizar_texto_botao()  # Chama a função para atualizar o texto do botão

def get_asset_path(filename):
    """Retorna o caminho do arquivo, seja em modo executável ou desenvolvimento."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'assets', filename)
    else:
        return os.path.join(os.path.dirname(__file__), 'assets', filename)

def acessar_url_com_retry(url, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            driver.get(url)
            return True
        except WebDriverException as e:
            logger.warning(f"Tentativa {tentativa+1}/{max_tentativas} falhou: {e}")
            time.sleep(60)  # Esperar 60 seg antes de tentar novamente
    return False

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")