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
varas_selecionadas = []

entry_data_inicio = ft.TextField(label="Data Início", value="15/07/2024")
entry_data_fim = ft.TextField(label="Data Fim", value="19/07/2024")

def atualizar_resultados(resultados):
    global text_area, page
    if text_area and text_area.content and page:
        result_text = "\n".join(resultados)
        text_area.content.value = result_text
        page.update()

def get_text_width(text, font_size):
    average_char_width = 7
    return len(text) * average_char_width

def agendar_proxima_consulta():
    next_run = datetime.datetime.now() + datetime.timedelta(minutes=30)
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, lambda: executar_consulta(page)).start()

def executar_consulta(pg):
    global driver, page
    page = pg
    running_event.set()
    options = webdriver.ChromeOptions()
    options.add_argument("--blink-settings=loadMediaAutomatically=2")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

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

        titulos = [" Data/Hora: ", " Autos:", "", "", "", "Status", "Sistema"]

        for idx, vara in enumerate(varas_selecionadas):
            print(vara)
            if termino_event.is_set():
                break

            try:
                # Atualiza o spinner_label com a vara atual
                if spinner_label:
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

            atualizar_resultados(resultados)

    except Exception as e:
        resultados.append("Ocorreu um erro durante a consulta. Tente novamente mais tarde.")
        
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
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(varas, size=10),
                            width=get_text_width(varas, 10),
                            height=25,
                            bgcolor=ft.colors.BLUE,
                            padding=0,
                            margin=0,
                            alignment=ft.alignment.center,
                            border_radius=25,
                            ink=True,
                            on_click=lambda e: print("Clickable with Ink clicked!"),
                        ),
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            icon_size=15,
                            on_click=lambda e, v=varas: remove_varas(v),
                            tooltip="Remover",
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
            )
            for varas in varas_selecionadas
        ]
        page.update()

    def update_dropdown_options():
        available_options = [vara for vara in varas_federais if vara not in varas_selecionadas]
        varas_dropdown.options = [ft.dropdown.Option(vara) for vara in available_options]
        page.update()

    available_varas = [vara for vara in varas_federais if vara not in varas_selecionadas]
    varas_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(vara) for vara in available_varas],
        value=None,
        width=580,
        text_style=ft.TextStyle(size=10),
        height=40
    )

    add_button = ft.ElevatedButton(
        text="Adicionar Vara",
        on_click=add_varas,
    )

    selected_varas_list = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(varas, size=10),
                        width=get_text_width(varas, 10),
                        height=25,
                        bgcolor=ft.colors.BLUE,
                        padding=0,
                        margin=0,
                        alignment=ft.alignment.center,
                        border_radius=25,
                        ink=True,
                        on_click=lambda e: print("Clickable with Ink clicked!"),
                    ),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        icon_size=15,
                        on_click=lambda e, v=varas: remove_varas(v),
                        tooltip="Remover",
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
            )
            for varas in varas_selecionadas
        ]
    )

    entry_data_inicio = ft.TextField(label="Data Início", value="15/07/2024", width=150)
    entry_data_fim = ft.TextField(label="Data Fim", value="19/07/2024", width=150)
    spinner_label = ft.Text("")

    text_area = ft.Container(content=ft.Text("Resultados..."))

    update_varas_selecionadas()

    page.add(
        ft.Column(
            [
                ft.Row([entry_data_inicio, entry_data_fim]),
                ft.Row([varas_dropdown, add_button]),
                selected_varas_list,
                ft.Row([start_button]),
                spinner_label,
                text_area,
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
