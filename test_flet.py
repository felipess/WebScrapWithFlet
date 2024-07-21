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

# Definição das datas padrão
hoje = datetime.datetime.now()
data_inicio_default = hoje.strftime("%d/%m/%Y")
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")

entry_data_inicio = ft.TextField(
    label="Data Início",
    value=data_inicio_default,
    width=200,
    text_style=ft.TextStyle(size=10)  # Tamanho da fonte ajustado para 10
)
entry_data_fim = ft.TextField(
    label="Data Fim",
    value=data_fim_default,
    width=200,
    text_style=ft.TextStyle(size=10)  # Tamanho da fonte ajustado para 10
)

def atualizar_resultados(resultados):
    global page
    if page:
        # Criar as linhas da tabela com base nos resultados
        rows = []
        for resultado in resultados:
            # Cada resultado deve ser uma lista de strings para ser exibido na tabela
            row_cells = [ft.DataCell(ft.Text(cell, size=12)) for cell in resultado]
            rows.append(ft.DataRow(cells=row_cells))
        
        # Criar a tabela
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data/Hora", size=12)),
                ft.DataColumn(ft.Text("Autos", size=12)),
                ft.DataColumn(ft.Text("Classe", size=12)),
                ft.DataColumn(ft.Text("Processo", size=12)),
                ft.DataColumn(ft.Text("Parte", size=12)),
                ft.DataColumn(ft.Text("Status", size=12)),
                ft.DataColumn(ft.Text("Sistema", size=12)),
            ],
            rows=rows,
        )
        
        # Atualizar a página com a nova tabela
        if hasattr(page, 'data_table'):
            page.controls.remove(page.data_table)
        
        page.data_table = table
        page.add(table)
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

        titulos = ["Data/Hora", "Autos", "Classe", "Processo", "Parte", "Status", "Sistema"]

        for idx, vara in enumerate(varas_selecionadas):
            print(f"Consultando: {vara}")
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

                div_infra_area_tabela = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
                tabela = driver.find_element(By.ID, "tblAudienciasEproc")
                linhas = tabela.find_elements(By.TAG_NAME, "tr")

                for linha in linhas:
                    texto_normalizado = linha.text.lower()
                    if any(termo in texto_normalizado for termo in ["custódia", "custodia"]):
                        tds = linha.find_elements(By.TAG_NAME, "td")
                        conteudo_linha = []
                        for td in tds:
                            td_html = td.get_attribute('innerHTML')
                            td_soup = BeautifulSoup(td_html, 'html.parser')
                            td_text = td_soup.get_text(separator=" ").strip()
                            conteudo_linha.append(td_text)
                        if len(conteudo_linha) == len(titulos):
                            resultados.append(conteudo_linha)
                        else:
                            resultados.append([""] * len(titulos))
                if not resultados:
                    resultados.append([""] * len(titulos))

            except Exception as e:
                print(f"Erro ao consultar a vara {vara}: {e}")
                resultados.append(["Ocorreu um erro na consulta"] * len(titulos))

            atualizar_resultados(resultados)

    except Exception as e:
        print(f"Erro geral: {e}")
        resultados.append(["Ocorreu um erro durante a consulta"] * len(titulos))
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

    varas_selecionadas_iniciais = [
        VarasFederais.VARA_GUAIRA.value,
        VarasFederais.VARA_FOZ_5.value,
    ]

    varas_selecionadas = varas_selecionadas_iniciais.copy()

    # Definindo datas padrão
    hoje = datetime.datetime.now()
    data_inicio_default = hoje.strftime("%d/%m/%Y")
    data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")    

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
        if not selected_varas_list.controls:
            selected_varas_list.controls.append(
                ft.Container(
                    content=ft.Text("Nenhuma vara selecionada", size=12),
                    padding=0,
                    margin=0,
                    width=580,
                    height=25,
                )
            )
        page.update()

    def update_dropdown_options():
        varas_dropdown.options = [ft.dropdown.Option(varas) for varas in varas_federais if varas not in varas_selecionadas]
        page.update()

    varas_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(varas) for varas in varas_federais],
        on_change=add_varas,
    )

    selected_varas_list = ft.Column(
        controls=[
            ft.Container(
                content=ft.Text("Nenhuma vara selecionada", size=12),
                padding=0,
                margin=0,
                width=580,
                height=25,
            )
        ]
    )

    spinner_label = ft.Text("", size=12)
    
    page.add(
        ft.Column(
            controls=[
                entry_data_inicio,
                entry_data_fim,
                ft.Row(
                    controls=[
                        varas_dropdown,
                        ft.ElevatedButton(text="Adicionar Vara", on_click=add_varas),
                    ],
                ),
                selected_varas_list,
                start_button,
                spinner_label,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    update_varas_selecionadas()
    update_dropdown_options()

if __name__ == "__main__":
    ft.app(target=main)
