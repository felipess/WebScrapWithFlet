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
            # Cada resultado deve ser uma lista de strings para ser exibido na tabela
            row_cells = [ft.DataCell(
                content=ft.Container(
                    content=ft.Text(cell, size=10),
                    height=100,  # Aumenta a altura das células
                    padding=ft.Padding(left=15, right=15, top=10, bottom=10),  # Aumenta o padding
                )
            ) for cell in resultado]            
            rows.append(ft.DataRow(cells=row_cells))
        
        # Criar a tabela
        table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Data/Hora", size=10)),
                ft.DataColumn(ft.Text("Autos", size=10)),
                ft.DataColumn(ft.Text("Classe", size=10)),
                ft.DataColumn(ft.Text("Processo", size=10)),
                ft.DataColumn(ft.Text("Parte", size=10)),
                ft.DataColumn(ft.Text("Status", size=10)),
                ft.DataColumn(ft.Text("Sistema", size=10)),
            ],
            rows=rows,
            data_row_min_height=80,  # Altura mínima das linhas de dados
            data_row_max_height=160,  # Altura máxima das linhas de dados
            column_spacing=0,       # Espaçamento entre colunas, se necessário
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
    wait = WebDriverWait(driver, 30)  # Aumentando o tempo de espera

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

                # Verificar se há a mensagem de "Nenhum resultado encontrado"
                mensagem_erro = wait.until(EC.presence_of_element_located((By.ID, "divInfraAreaTabela")))
                if "Nenhum resultado encontrado" in mensagem_erro.text:
                    print(f"Nenhum resultado encontrado para {vara}")
                    continue

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
                            td_text = td_soup.get_text(separator=" ").strip()
                            if "ocorreu um erro" in td_text.lower():
                                erro_encontrado = True
                                break
                            conteudo_linha.append(td_text)
                        if not erro_encontrado and len(conteudo_linha) == len(titulos):
                            resultados.append(conteudo_linha)

            except Exception as e:
                print(f"Erro ao consultar a vara {vara}: {e}")

        if not resultados:
            resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se nenhum resultado válido

        atualizar_resultados(resultados)

    except Exception as e:
        print(f"Erro geral: {e}")
        resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se houver um erro geral
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

    # Mapeamento dos valores para labels personalizados
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

    # Lista de varas selecionadas iniciais com labels personalizados
    varas_selecionadas_iniciais = [
        VarasFederais.VARA_GUAIRA.value,
        # VarasFederais.VARA_FOZ_3.value,
        # VarasFederais.VARA_UMUARAMA_1.value,
        # VarasFederais.VARA_PONTA_GROSSA_1.value,
        # VarasFederais.VARA_MARINGA_3.value,
        # VarasFederais.VARA_CASCAVEL_4.value,
        # VarasFederais.VARA_FOZ_5.value,
        # VarasFederais.VARA_LONDRINA_5.value,
        # VarasFederais.VARA_CURITIBA_9.value,
        # VarasFederais.VARA_CURITIBA_13.value,
        # VarasFederais.VARA_CURITIBA_14.value,
        # VarasFederais.VARA_CURITIBA_23.value,
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
                content=ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=ft.Text(varas_labels.get(varas, varas), size=10),  # Usa o label personalizado se disponível
                            padding=ft.Padding(left=20, top=0, right=0, bottom=0),  # Espaço à esquerda do texto
                            width=get_text_width(varas_labels.get(varas, varas), 10) + 40,  # Ajustar largura para incluir espaço
                            height=25,
                            bgcolor=ft.colors.BLUE,
                            border_radius=25,
                            on_click=lambda e, v=varas: remove_varas(v),
                            tooltip="Remover",
                        ),
                    ],
                    spacing=5,  # Espaçamento interno entre os itens no ResponsiveRow
                    alignment=ft.MainAxisAlignment.START,  # Alinhar os controles horizontalmente
                ),
                padding=5,  # Padding ao redor do Container principal
                col={"xs": 6, "sm": 3, "md": 3, "lg": 2, "xl": 2, "xxl": 1},  # Ajustar para diferentes tamanhos de tela
            )
            for varas in varas_selecionadas
        ]
        page.update()







    def update_dropdown_options():
        varas_dropdown.options = [
            ft.dropdown.Option(varas)
            for varas in varas_federais if varas not in varas_selecionadas
        ]
        page.update()

    varas_dropdown = ft.Dropdown(
        options=[ft.dropdown.Option(varas) for varas in varas_federais],
        on_change=add_varas,
    )

    selected_varas_list = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=ft.Text(varas, size=10),
                            width=get_text_width(varas, 10),
                            height=25,
                            bgcolor=ft.colors.BLUE,
                            padding=0,
                            border_radius=25  # Adicionando border radius
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE_FOREVER, #or DELETE
                            icon_color=ft.colors.WHITE,
                            on_click=lambda e, v=varas: remove_varas(v),
                            icon_size=12,  # Tamanho reduzido do ícone
                        ),
                    ],
                    spacing=5,
                    col={"xs": 12, "sm": 6, "md": 4, "lg": 3, "xl": 2, "xxl": 1},  # Ajustar para diferentes tamanhos de tela
                ),
                padding=5,
            )
            for varas in varas_selecionadas
        ],
        spacing=5,
        run_spacing=10,
    )

    spinner_label = ft.Text("", size=12, color=ft.colors.BLUE_GREY_700)

    page.add(
        ft.Column(
            controls=[
                entry_data_inicio,
                entry_data_fim,
                varas_dropdown,
                selected_varas_list,
                start_button,
                spinner_label
            ]
        )
    )

    # Atualizar a lista de varas selecionadas ao carregar a página
    update_varas_selecionadas()

ft.app(target=main)
