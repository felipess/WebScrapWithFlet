import flet as ft
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import threading
import time
import datetime
import pyperclip
from VarasFederais import VarasFederais

# Variáveis globais
driver = None
running_event = threading.Event()
termino_event = threading.Event()
text_area = None
spinner_label = None
page = None
varas_federais = []
varas_selecionadas = []

# Data defaults
hoje = datetime.datetime.now()
data_inicio_default = hoje.strftime("%d/%m/%Y")
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")

entry_data_inicio = ft.TextField(
    label="Data Início",
    value=data_inicio_default,
    width=200,
    text_style=ft.TextStyle(size=10)
)
entry_data_fim = ft.TextField(
    label="Data Fim",
    value=data_fim_default,
    width=200,
    text_style=ft.TextStyle(size=10)
)

ordem_colunas = [4, 1, 2, 0, 3]

def copiar_linha(conteudo_linha):
    conteudo_ordenado = [conteudo_linha[i] for i in ordem_colunas]
    texto = ' | '.join(conteudo_ordenado)
    pyperclip.copy(texto)
    print(f"Conteúdo copiado: {texto}")

def atualizar_resultados(resultados):
    global page
    if page:
        rows = []
        for resultado in resultados:
            row_controls = [
                ft.Container(content=ft.Text(resultado[i], size=12), width=200) for i in range(5)
            ]
            row_controls.append(
                ft.IconButton(
                    icon=ft.icons.CONTENT_COPY,
                    icon_color=ft.colors.BLUE,
                    on_click=lambda e, r=resultado: copiar_linha(r),
                    icon_size=20,
                    tooltip="Copiar"
                )
            )
            rows.append(
                ft.ResponsiveRow(
                    controls=row_controls,
                    spacing=5,
                    alignment=ft.MainAxisAlignment.START
                )
            )

        responsive_container = ft.Container(
            content=ft.Column(controls=rows),
            width=page.window.width,  # Ajusta a largura ao tamanho da janela
            padding=5,
            margin=10
        )

        if hasattr(page, 'data_table'):
            page.controls.remove(page.data_table)

        page.data_table = responsive_container
        page.add(responsive_container)
        page.update()

def get_text_width(text, font_size):
    average_char_width = 7
    return len(text) * average_char_width

def agendar_proxima_consulta():
    next_run = datetime.datetime.now() + datetime.timedelta(minutes=30)
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, lambda: executar_consulta(page)).start()

def executar_consulta(page):
    global driver
    running_event.set()
    options = webdriver.ChromeOptions()
    options.add_argument("--blink-settings=loadMediaAutomatically=2")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)

    try:
        resultados = []
        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")
        wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))

        data_inicio = entry_data_inicio.value.strip()
        data_fim = entry_data_fim.value.strip()

        campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataInicio")))
        campo_data_inicio.clear()
        campo_data_inicio.send_keys(data_inicio)

        campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataTermino")))
        campo_data_fim.clear()
        campo_data_fim.send_keys(data_fim)

        titulos = ["Data/Hora", "Autos", "Classe", "Processo", "Parte", "Status", "Sistema"]

        for idx, vara in enumerate(varas_selecionadas):
            if termino_event.is_set():
                break

            try:
                spinner_label.value = f"Consultando {vara}..."
                page.update()

                vara_federal_div = wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))
                dropdown_button = vara_federal_div.find_element(By.CLASS_NAME, "dropdown-toggle")
                dropdown_button.click()
                vara_federal_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//option[text()='{vara}']")))
                vara_federal_option.click()

                if idx > 0:
                    time.sleep(2)

                botao_consultar = wait.until(EC.element_to_be_clickable((By.ID, "btnConsultar")))
                botao_consultar.click()

                mensagem_erro = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
                if "Nenhum resultado encontrado" in mensagem_erro.text:
                    continue

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

            except Exception as e:
                print(f"Erro ao consultar a vara {vara}: {e}")

        if not resultados:
            resultados.append([""] * len(titulos))

        atualizar_resultados(resultados)

    except Exception as e:
        print(f"Erro geral: {e}")
        resultados.append([""] * len(titulos))
        atualizar_resultados(resultados)
        
    finally:
        if spinner_label:
            spinner_label.value = ""
            page.update()
        running_event.clear()
        if driver:
            driver.quit()
        if not termino_event.is_set():
            agendar_proxima_consulta()

start_button = ft.ElevatedButton(
    text="Iniciar Consulta",
    on_click=lambda e: executar_consulta(page)
)

def main(pg: ft.Page):
    global entry_data_inicio, entry_data_fim, spinner_label, text_area, varas_federais, varas_selecionadas, page

    page = pg

    page.window.width = 640
    page.window.height = 900
    page.title = "Containers - clickable and not"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    varas_federais = [vara.value for vara in VarasFederais]

    varas_labels = {
        VarasFederais.VARA_GUAIRA.value: "1ª VF Guaira",
        VarasFederais.VARA_FOZ_3.value: "3 VF de Foz",
        VarasFederais.VARA_UMUARAMA_1.value: "1ª VF Umuarama",
        VarasFederais.VARA_PONTA_GROSSA_1.value: "1ª VF Ponta Grossa",
        VarasFederais.VARA_MARINGA_3.value: "3ª VF Maringá",
        VarasFederais.VARA_CASCAVEL_4.value: "4ª VF Cascavel",
        VarasFederais.VARA_FOZ_5.value: "5ª VF Foz",
        VarasFederais.VARA_LONDRINA_5.value: "5ª VF Londrina",
        VarasFederais.VARA_CURITIBA_9.value: "9ª VF Curitiba",
        VarasFederais.VARA_CURITIBA_13.value: "13ª VF Curitiba",
        VarasFederais.VARA_CURITIBA_14.value: "14ª VF Curitiba",
        VarasFederais.VARA_CURITIBA_23.value: "23ª VF Curitiba",
    }

    varas_selecionadas_iniciais = [
        VarasFederais.VARA_GUAIRA.value,
    ]

    varas_selecionadas = varas_selecionadas_iniciais.copy()

    def add_varas(e):
        if varas_dropdown.selected:
            vara = varas_dropdown.selected
            if vara not in varas_selecionadas:
                varas_selecionadas.append(vara)
                page.update()

    def remove_varas(e):
        if varas_dropdown.selected:
            vara = varas_dropdown.selected
            if vara in varas_selecionadas:
                varas_selecionadas.remove(vara)
                page.update()

    varas_dropdown = ft.Dropdown(
        label="Selecionar Vara Federal",
        options=[ft.dropdown.Option(label, value) for value, label in varas_labels.items()],
        on_change=add_varas
    )

    page.add(
        ft.Column(
            controls=[
                entry_data_inicio,
                entry_data_fim,
                varas_dropdown,
                start_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    )

    spinner_label = ft.Text("")
    text_area = ft.Text()
    page.add(spinner_label)
    page.add(text_area)

ft.app(target=main)
