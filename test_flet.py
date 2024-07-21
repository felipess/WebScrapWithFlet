import flet as ft
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import threading
import time
import datetime
from VarasFederais import VarasFederais

# Variável global para o driver Selenium
driver = None

# Definição das variáveis e funções necessárias
running_event = threading.Event()
termino_event = threading.Event()
text_area = None
spinner_label = None
page = None
varas_federais = []

def atualizar_resultados(resultados):
    global text_area, page
    if text_area and page:
        result_text = "\n".join(resultados)
        text_area.value = result_text
        page.update()

# Definir uma função para estimar a largura do texto
def get_text_width(text, font_size):
    # Ajuste esse valor conforme necessário para a precisão desejada
    average_char_width = 7  # Largura média de um caractere em pixels
    return len(text) * average_char_width

def agendar_proxima_consulta():
    next_run = datetime.datetime.now() + datetime.timedelta(minutes=30)  # Exemplo: Próxima consulta em 30 minutos
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, lambda: executar_consulta(page)).start()

def executar_consulta(page):
    global driver
    running_event.set()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Rodar em modo headless se necessário
    options.add_argument("--blink-settings=loadMediaAutomatically=2")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        resultados = []
        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")
        wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))

        campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataInicio")))
        campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataTermino")))

        # Atualize as datas usando os valores atuais dos campos de entrada
        data_inicio = entry_data_inicio.value.strip()
        campo_data_inicio.clear()
        campo_data_inicio.send_keys(data_inicio)

        data_fim = entry_data_fim.value.strip()
        campo_data_fim.clear()
        campo_data_fim.send_keys(data_fim)

        titulos = [" Data/Hora: ", " Autos:", "", "", "", "Status", "Sistema"]

        for idx, vara in enumerate(varas_federais):
            if termino_event.is_set():
                break

            try:
                # Atualiza o spinner_label com a vara atual
                if spinner_label:
                    spinner_label.value = f"Consultando {vara}..."
                    page.update()

                vara_federal_div = wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))

                # Clique no dropdown para selecionar a Vara
                dropdown_button = vara_federal_div.find_element(By.CLASS_NAME, "dropdown-toggle")
                dropdown_button.click()

                # Aguarde e selecione a opção desejada
                varas_opcoes = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//select[@id='ddlVaraFederal']/option")))
                for opcao in varas_opcoes:
                    if opcao.text == vara:
                        opcao.click()
                        break

                # Adiciona um pequeno intervalo de espera entre as mudanças de vara
                if idx > 0:
                    time.sleep(2)

                # Clique no botão "Executar Consulta"
                botao_consultar = wait.until(EC.element_to_be_clickable((By.ID, "btnConsultar")))
                botao_consultar.click()

                # Verifica se há resultados na tabela ou se encontrou a mensagem "Nenhum resultado encontrado."
                div_infra_area_tabela = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
                tabela_text = div_infra_area_tabela.text

                if "Nenhum resultado encontrado." in tabela_text:
                    resultados.append("")
                else:
                    resultados.append(f"Resultados da {vara}\n")

                    tabela = driver.find_element(By.ID, "tblAudienciasEproc")
                    linhas = tabela.find_elements(By.TAG_NAME, "tr")
                    encontrou = False
                    termos = ["custódia", "custodia"]

                    for linha in linhas:
                        texto_normalizado = linha.text.lower()
                        if any(termo in texto_normalizado for termo in termos):
                            conteudo_linha = ""
                            tds = linha.find_elements(By.TAG_NAME, "td")
                            for titulo, td in zip(titulos, tds):
                                if titulo == "Sistema" or titulo == "Status":
                                    continue
                                td_html = td.get_attribute('innerHTML')
                                td_soup = BeautifulSoup(td_html, 'html.parser')
                                td_text = td_soup.get_text(separator=" ").split("Classe:")[0].strip()
                                conteudo_linha += f"{titulo} {td_text}\n"
                            resultados.append(conteudo_linha)
                            resultados.append("\n")
                            encontrou = True

                    if not encontrou:
                        resultados.pop()
                        resultados.append("")

            except Exception as e:
                resultados.append(f"Ocorreu um erro na consulta da vara {vara}.\n")

        # Atualize a interface do Flet com os resultados
        atualizar_resultados(resultados)

    except Exception as e:
        resultados.append("Ocorreu um erro durante a consulta. Tente novamente mais tarde.")
        
    finally:
        if spinner_label:
            spinner_label.value = ""  # Limpa o spinner após a consulta
            page.update()
        running_event.clear()  # Marca a consulta como finalizada
        if driver:
            driver.quit()  # Garante que o driver seja fechado corretamente
        if not termino_event.is_set():
            agendar_proxima_consulta()

# Adiciona um botão para iniciar a consulta manualmente
start_button = ft.ElevatedButton(
    text="Iniciar Consulta",
    on_click=lambda e: executar_consulta(page)
)

def main(page: ft.Page):
    global entry_data_inicio, entry_data_fim, spinner_label, text_area, varas_federais

    # Define o tamanho inicial da janela
    page.window.width = 640
    page.window.height = 900

    # Lista de varas federais do Enum
    varas_federais = [vara.value for vara in VarasFederais]

    # Lista de varas selecionadas por padrão
    varas_selecionadas_iniciais = [
        VarasFederais.VARA_GUAIRA.value,
        VarasFederais.VARA_FOZ_3.value,
        VarasFederais.VARA_UMUARAMA_1.value,
        VarasFederais.VARA_PONTA_GROSSA_1.value,
        VarasFederais.VARA_MARINGA_3.value,
        VarasFederais.VARA_CASCAVEL_4.value,
        VarasFederais.VARA_FOZ_5.value,
        VarasFederais.VARA_LONDRINA_5.value,
        VarasFederais.VARA_CURITIBA_9.value,
        VarasFederais.VARA_CURITIBA_13.value,
        VarasFederais.VARA_CURITIBA_14.value,
        VarasFederais.VARA_CURITIBA_23.value,
    ]

    # Inicializa com as varas selecionadas por padrão
    varas_selecionadas = varas_selecionadas_iniciais.copy()

    def add_varas(e):
        if varas_dropdown.value and varas_dropdown.value not in varas_selecionadas:
            varas_selecionadas.append(varas_dropdown.value)
            update_varas_selecionadas()
            update_dropdown_options()

    def remove_varas(varas):
        if varas in varas_selecionadas:
            varas_selecionadas.remove(varas)
            update_varas_selecionadas()
            update_dropdown_options()

    def update_varas_selecionadas():
        selected_varas_list.controls = [
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(varas, size=10),
                        width=get_text_width(varas, 10) + 40,  # Ajusta a largura do container com base no tamanho do texto + margem
                        height=25,
                        bgcolor=ft.colors.BLUE,
                        padding=5,
                        margin=5
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_size=20,
                        on_click=lambda e, v=varas: remove_varas(v),
                        tooltip="Remover"
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
            for varas in varas_selecionadas
        ]
        page.update()


    def update_dropdown_options():
        available_options = [vara for vara in varas_federais if vara not in varas_selecionadas]
        varas_dropdown.options = [ft.dropdown.Option(vara) for vara in available_options]
        page.update()

    # Inicializa o Dropdown com todas as varas disponíveis, exceto as já selecionadas
    available_varas = [vara for vara in varas_federais if vara not in varas_selecionadas]
    varas_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(vara) for vara in available_varas],
        value=None,  # Nenhum valor padrão selecionado no Dropdown
        width=580,
        text_style=ft.TextStyle(size=10),  # Ajusta o tamanho da fonte no Dropdown
        height=40  # Ajusta a altura do Dropdown, o que pode ajudar a ajustar o espaçamento visual
    )

    add_button = ft.ElevatedButton(
        text="Adicionar",
        on_click=add_varas
    )

    selected_varas_list = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(varas, size=10),
                        width=get_text_width(varas, 10) + 40,  # Ajusta a largura do container com base no tamanho do texto + margem
                        height=25,
                        bgcolor=ft.colors.BLUE,
                        padding=5,
                        margin=5
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_size=20,
                        on_click=lambda e, v=varas: remove_varas(v),
                        tooltip="Remover"
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ) for varas in varas_selecionadas
        ]
    )

    # Área de texto para exibir resultados (substituindo TextArea por Text)
    text_area_content = (
        "Aqui você pode adicionar um texto longo que será exibido sem rolagem. " * 10
    )

    text_area = ft.Container(
        content=ft.Text(
            value=text_area_content,
            size=12,
            text_align=ft.TextAlign.LEFT
        ),
        width=580,
        height=250,
        bgcolor=ft.colors.BLACK,
        padding=10,
        margin=10
    )

    spinner_label = ft.Text("", size=12)

    page.add(
        ft.Column(
            controls=[
                ft.Text("Selecione a Vara", size=12),
                varas_dropdown,
                add_button,
                ft.Text("Varas Selecionadas", size=12),
                selected_varas_list,
                spinner_label,
                text_area,
                start_button  # Adiciona o botão para iniciar a consulta manualmente
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),            
    )

    # Inicia a execução da consulta quando a aplicação inicia
    # executar_consulta(page)

    # Add the event handler to close the application
    def close_app(e):
        global driver
        if driver:
            driver.quit()
        page.window.close()

    page.on_close = close_app

ft.app(target=main)
