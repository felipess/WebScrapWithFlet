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
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import pyperclip

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
executado = False
interval = 15

# Inicialização dos labels com datas e horas atuais
def get_formatted_datetime():
    now = datetime.datetime.now()
    #return now.strftime("%d/%m/%Y %H:%M:%S")
    return now.strftime("%H:%M:%S")


# if executado:
#     print(executado)
#     ultima_consulta = ft.Text(f"Última consulta: {get_formatted_datetime()}", size=12, color=ft.colors.RED)
#     proxima_consulta = ft.Text(f"Próxima consulta: {datetime.datetime.now() + datetime.timedelta(seconds=interval):%d/%m/%Y %H:%M:%S}", size=12, color=ft.colors.RED)
# else:    
ultima_consulta = ft.Text(f"", size=10, color=ft.colors.GREY)
proxima_consulta = ft.Text(f"", size=10, color=ft.colors.GREY)

# Define o estilo do texto dos itens do dropdown
text_style = ft.TextStyle(size=11)
sizeFontRows = 10

# Definição das datas padrão
hoje = datetime.datetime.now()
data_inicio_default = hoje.strftime("%d/%m/%Y")
data_fim_default = (hoje + datetime.timedelta(days=1)).strftime("%d/%m/%Y")

entry_data_inicio = ft.TextField(
    label="Data Início",
    label_style=text_style,
    value=data_inicio_default,
    width=102,
    text_style=text_style  # Tamanho da fonte ajustado para 10
)
entry_data_fim = ft.TextField(
    label="Data Fim",
    label_style=text_style,
    value=data_fim_default,
    width=102,
    text_style=text_style  # Tamanho da fonte ajustado para 10
)

# Defina a ordem desejada das colunas
ordem_colunas = [4, 1, 2, 0, 3]  # Ordem original, pode ser ajustada conforme necessário

def copiar_linha(conteudo_linha):
    """Função para copiar o conteúdo da linha para a área de transferência."""
    conteudo_ordenado = [conteudo_linha[i] for i in ordem_colunas]  # Organiza o conteúdo conforme a ordem definida
    texto = ' | '.join(conteudo_ordenado)  # Une o conteúdo da linha em uma string
    pyperclip.copy(texto)  # Copia o texto para a área de transferência
    print(f"Conteúdo copiado: {texto}")

# Variável global para armazenar a mensagem de nenhum resultado
mensagem_nenhum_resultado = None

def atualizar_resultados(resultados):
    global page
    global mensagem_nenhum_resultado
    
    if page:
        if resultados:

            # Atualizar o texto dos labels
            ultima_consulta.value = f"Última consulta: {get_formatted_datetime()}"
            proxima_consulta.value = f"Próxima consulta: {datetime.datetime.now() + datetime.timedelta(seconds=interval):%H:%M:%S}"

            # Preparar a tabela com resultados
            rows = []
            for resultado in resultados:
                row_cells = [
                    ft.DataCell(ft.Text(resultado[0], size=sizeFontRows)),  # Data/Hora
                    ft.DataCell(ft.Text(resultado[1], size=sizeFontRows)),  # Autos
                    ft.DataCell(ft.Text(resultado[2], size=sizeFontRows)),  # Classe
                    ft.DataCell(ft.Text(resultado[3], size=sizeFontRows)),  # Processo
                    ft.DataCell(ft.Text(resultado[4], size=sizeFontRows)),  # Parte
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

            # Remover qualquer mensagem anterior
            if hasattr(page, 'mensagem_nenhum_resultado'):
                if page.mensagem_nenhum_resultado in page.controls:
                    page.controls.remove(page.mensagem_nenhum_resultado)

            # Atualizar a tabela
            if hasattr(page, 'data_table'):
                if page.data_table in page.controls:
                    page.controls.remove(page.data_table)

            page.data_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Data/Hora", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Autos", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Classe", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Processo", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Parte", size=sizeFontRows)),
                    ft.DataColumn(ft.Text("Ações", size=sizeFontRows)),  # Coluna para o botão de copiar
                ],
                rows=rows,
                data_row_min_height=60,
                data_row_max_height=80,
                column_spacing=20,
            )
            
            mensagem_nenhum_resultado = None

        else:
            # Se não houver resultados, definir a mensagem de nenhum resultado
            mensagem_nenhum_resultado = "Nenhum resultado encontrado."

            # Atualizar a página com base na variável
        atualizar_pagina()


def atualizar_pagina():
    global page
    global mensagem_nenhum_resultado


    
    if page:
        page.update()

        # Remover a tabela de resultados, se estiver presente
        if hasattr(page, 'data_table') and page.data_table in page.controls:
            page.controls.remove(page.data_table)
        
        if mensagem_nenhum_resultado:
            # Exibir a mensagem de nenhum resultado
            if not hasattr(page, 'mensagem_nenhum_resultado'):
                page.mensagem_nenhum_resultado = ft.Text(mensagem_nenhum_resultado, size=sizeFontRows)
            
            if page.mensagem_nenhum_resultado not in page.controls:
                page.add(page.mensagem_nenhum_resultado)
        else:
            # Exibir a tabela de resultados
            if hasattr(page, 'data_table'):
                page.add(page.data_table)

        # Adicionar os labels de data/hora
        # if not hasattr(page, 'data_labels'):
        #     page.data_labels = ft.Container(
        #         content=ft.Row(
        #             controls=[
        #                 ultima_consulta,
        #                 proxima_consulta
        #             ],
        #             alignment=ft.MainAxisAlignment.CENTER  # Centraliza os botões
        #         ),
        #         padding=ft.Padding(20, 0, 0, 0)  # Adiciona espaço abaixo da linha
        #     )
        #     page.controls.append(page.data_labels)

        page.update()




def get_text_width(text, font_size):
    average_char_width = 7
    return len(text) * average_char_width

def agendar_proxima_consulta():
    next_run = datetime.datetime.now() + datetime.timedelta(seconds=interval)  # Ajusta para 10 segundos
    delay = (next_run - datetime.datetime.now()).total_seconds()
    threading.Timer(delay, lambda: executar_consulta(page)).start()

def executar_consulta(page):
    global driver
    global executado
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
                            td_text = td_soup.get_text(separator=" ").split("Classe:")[0].strip()  # Modificação aqui
                            if "ocorreu um erro" in td_text.lower():
                                erro_encontrado = True
                                break
                            conteudo_linha.append(td_text)
                        if not erro_encontrado and len(conteudo_linha) == len(titulos):
                            resultados.append(conteudo_linha)

            except Exception as e:
                print(f"Erro ao consultar a vara {vara}: {e}")

        if not resultados:
            resultados = []
            #resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se nenhum resultado válido

        atualizar_resultados(resultados)
        

    except Exception as e:
        print(f"Erro geral: {e}")
        resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se houver um erro geral
        atualizar_resultados(resultados)
        
    finally:
        if spinner_label:
            spinner_label.value = ""
            executado = True
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
    global entry_data_inicio, entry_data_fim, spinner_label, text_area, varas_federais, varas_selecionadas, page, ultima_consulta, proxima_consulta

    page = pg

    page.window.min_width = 1000
    page.window.width = 1000
    page.window.height = 900
    page.window.min_height = 500
    page.title = "Pesquisa automatizada - Circurscrições da JF do Paraná"
    page.vertical_alignment = ft.MainAxisAlignment.START  # Alinhar ao topo verticalmente
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # # Adicione os rótulos ao layout da página
    # page.add(ultima_consulta)
    # page.add(proxima_consulta)

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
            page.update()



    def remove_varas(varas):
        if varas in varas_selecionadas:
            varas_selecionadas.remove(varas)
            update_varas_selecionadas()
            update_dropdown_options()
            page.update()

    
    def update_varas_selecionadas():
        # Cria os containers individuais para cada vara selecionada
        varas_items = [ 
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
        

        # Adiciona um container ao redor de todos os itens
        selected_varas_list.controls = [
            ft.Text(
            "Selecionados",
            size=16,               # Tamanho da fonte para o título
            weight=ft.FontWeight.BOLD,  # Negrito
            color=ft.colors.WHITE,  # Cor do texto
            ),
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=varas_items,
                    spacing=10,  # Espaço entre os containers das varas
                ),
                padding=10,  # Padding ao redor do container principal
                #bgcolor=ft.colors.RED,  # Cor de fundo para o container principal
                ink=True,
                border_radius=10,  # Borda arredondada do container principal
                border=ft.border.all(1, ft.colors.GREY_900)  # Borda do container principal
            )
        ]
        page.update()

    def update_dropdown_options():
        varas_dropdown.options = [
            ft.dropdown.Option(varas)
            for varas in varas_federais if varas not in varas_selecionadas
        ]
        page.update()

    varas_dropdown = ft.Dropdown(
        text_style=text_style,  # Define o estilo do texto para o dropdown
        options=[ft.dropdown.Option(varas) for varas in varas_federais],
        on_change=add_varas,
        label="Adicionar outras localidades para pesquisa",
        label_style=text_style,
        #hint_text="Selecione",
        width=640,  # Ajuste a largura conforme necessário
        border_radius=5
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

    spinner_label = ft.Text("", size=10, color=ft.colors.BLUE_500)

    page.update()

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    # Contêiner para o título com padding inferior e alinhamento centralizado
                    ft.Container(
                        content=ft.Text(
                            "Consulta de audiências de custódia",
                            size=20,
                            weight="bold"
                        ),
                        alignment=ft.Alignment(0, 0.5),  # Centraliza o texto horizontalmente
                        padding=ft.Padding(0, 0, 0, 20)  # Adiciona espaço abaixo do título
                    ),
                    # Linha com os controles
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                # Entrada de data de início com borda cinza
                                ft.Container(
                                    content=entry_data_inicio,
                                    #border=ft.border.all(1, ft.colors.GREY_900),  # Borda cinza
                                ),
                                # Entrada de data de fim com borda cinza
                                ft.Container(
                                    content=entry_data_fim,
                                    #border=ft.border.all(1, ft.colors.GREY_900),  # Borda cinza
                                ),
                                # Dropdown de varas com borda cinza
                                ft.Container(
                                    content=varas_dropdown,
                                    #border=ft.border.all(1, ft.colors.GREY_900),  # Borda cinza
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            spacing=10,  # Espaçamento entre os elementos
                        ),
                        padding=ft.Padding(0, 0, 0, 0)  # Adiciona espaço abaixo da linha
                    ),
                    # Contêiner para selected_varas_list com padding inferior
                    ft.Container(
                        content=selected_varas_list,
                        padding=ft.Padding(0, 0, 0, 0)  # Adiciona espaço abaixo de selected_varas_list
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                spinner_label                                
                            ],
                            alignment=ft.MainAxisAlignment.CENTER  # Centraliza os botões
                        ),
                        padding=ft.Padding(0, 0, 0, 0)  # Adiciona espaço abaixo da linha
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                #ft.Divider(height=30, thickness=12),
                                ultima_consulta,
                                proxima_consulta,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER  # Centraliza os botões
                        ),
                        padding=ft.Padding(0, 0, 0, 0)  # Adiciona espaço abaixo da linha
                    ),
                    # Linha com start_button e spinner_label centralizados
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                start_button,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER  # Centraliza os botões
                        ),
                        padding=ft.Padding(0, 0, 0, 0)  # Adiciona espaço abaixo da linha
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10  # Espaçamento entre os controles da coluna
            ),
            padding=ft.Padding(left=50, top=50, right=50, bottom=50)  # Definindo padding do Container Janela geral
        ),
    )

    # Atualizar a lista de varas selecionadas ao carregar a página
    update_varas_selecionadas()

ft.app(target=main)