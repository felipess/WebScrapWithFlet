import flet as ft
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from VarasFederais import VarasFederais
from bs4 import BeautifulSoup
import datetime
import pyperclip

# Defina a data de validade
data_validade = datetime.datetime(2024, 12, 8)  # Defina sua data de validade aqui
VERSION = "1.9"

# Variável global para o driver Selenium
driver = None

# Definição das variáveis e funções necessárias
running_event = threading.Event()
termino_event = threading.Event()
text_area = None
spinner_label = None
page = None
varas_federais = []
executado = False
interval = 600  # 10 min
# Variável global para armazenar os resultados anteriores
resultados_anteriores = []


def verificar_validade():
    if datetime.datetime.now() > data_validade:        
        return False
    return True

# Inicialização dos labels com datas e horas atuais
def get_formatted_datetime():
    now = datetime.datetime.now()
    #return now.strftime("%d/%m/%Y %H:%M:%S")
    return now.strftime("%H:%M:%S")

# Chame essa função após driver.quit()
# def close_specific_chrome_process(pid):
#     try:
#         p = psutil.Process(pid)
#         p.terminate()
#     except Exception as e:
#         print(f"Erro ao fechar o processo: {e}")


def atualizar_rodape():
    global page
    # global label_dev
   
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

# Defina a ordem desejada das colunas
ordem_colunas = [4, 1, 2, 0, 3]  # Ordem original, pode ser ajustada conforme necessário

def copiar_linha(conteudo_linha):
    """Função para copiar o conteúdo da linha para a área de transferência."""
    conteudo_ordenado = [conteudo_linha[i] for i in ordem_colunas]  # Organiza o conteúdo conforme a ordem definida

    # Modifica o conteúdo da coluna 0
    if len(conteudo_ordenado) > 0:  # Verifica se a coluna 0 existe
        coluna_0_texto = conteudo_ordenado[0]

        # Remove "Observação:" e tudo o que vem depois
        if "Observação:" in coluna_0_texto:
            coluna_0_texto = coluna_0_texto.split("Observação:")[0].strip()  # Corta até antes de "Observação:"
        
        conteudo_ordenado[0] = coluna_0_texto  # Atualiza a coluna 0

    # Modifica o conteúdo da coluna 4
    if len(conteudo_ordenado) > 4:  # Verifica se a coluna 4 existe
        coluna_4_texto = conteudo_ordenado[4]

        # Remove tudo após "Observação:" e a própria palavra
        if "Observação:" in coluna_4_texto:
            coluna_4_texto = coluna_4_texto.split("Observação:")[0].strip()  # Corta até antes de "Observação:"
        
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

# Variável global para armazenar a mensagem de nenhum resultado
mensagem_nenhum_resultado = None

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


def initialize_webdriver():
    """Initialize the Selenium WebDriver with necessary options."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--width=1080")  # Define a largura
    options.add_argument("--height=720")  # Define a altura
    global driver

    try:
        driver = webdriver.Firefox(options=options)
        print("Driver inicializado com sucesso")
        return driver
    except Exception as e:
        print(f"Erro ao inicializar o driver: {e}")
        return None

def clear_and_send_keys(element, value):
    """Clear an input element and send keys."""
    element.clear()
    element.send_keys(value)


def executar_consulta(page):
    global driver, executado, mensagem_nenhum_resultado, resultados_anteriores
    
    print("Consulta Iniciada...")

    driver = initialize_webdriver()
    if not driver:
        return  # Exit if driver initialization fails

    mensagem_nenhum_resultado = None  # Reseta a mensagem de nenhum resultado
    snack_bar = ft.SnackBar(ft.Text(""), open=False)
    page.overlay.append(snack_bar)

    running_event.set()
    #options = webdriver.ChromeOptions()
    
    try:
        resultados = []
        titulos = ["Data/Hora", "Autos", "Classe", "Processo", "Parte", "Status", "Sistema"]
        
        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")

        time.sleep(1)

        
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))

        data_inicio = entry_data_inicio.value.strip()
        data_fim = entry_data_fim.value.strip()

        campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataInicio")))
        campo_data_inicio.clear()
        campo_data_inicio.send_keys(data_inicio)

        campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataTermino")))
        campo_data_fim.clear()
        campo_data_fim.send_keys(data_fim)

        for idx, vara in enumerate(varas_selecionadas):
            print(f"Consultando: {vara}")  # Certifique-se que o valor está correto

            if termino_event.is_set():
                break

            try:
                spinner_label.value = f"Consultando {vara}..."
                page.update()

                vara_federal_div = wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))
                dropdown_button = vara_federal_div.find_element(By.CLASS_NAME, "dropdown-toggle")
                dropdown_button.click()

                # Captura o campo de entrada do dropdown
                search_input = vara_federal_div.find_element(By.CSS_SELECTOR, "input.form-control")  # Ajuste o seletor se necessário

                # Foca no campo de entrada
                search_input.click()  # Clica para garantir que está ativo

                # Digita o nome da vara
                search_input.send_keys(vara)

                # Pressiona Enter para selecionar a primeira opção filtrada
                search_input.send_keys(Keys.RETURN)

                # Botão de consultar
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
                return

        if not resultados:
            resultados = []
            mensagem_nenhum_resultado = "Nenhum resultado encontrado."

        atualizar_resultados(resultados)
        atualizar_rodape()  # Atualiza a nota de rodapé

        

    except Exception as e:
        print(f"Erro geral: {e}")
        resultados.append([""] * len(titulos))  # Adiciona uma linha vazia se houver um erro geral
        atualizar_resultados(resultados)
        atualizar_rodape()  # Atualiza a nota de rodapé
        return

        
    finally:
        # Mantem Deabilitado ou Reabilita o botão no final da execução da consulta
        start_button.disabled = True 
        start_button.update()

        if spinner_label:
            spinner_label.value = ""
            executado = True
            page.update()
        running_event.clear()
        if driver:
            driver.quit()
        if not termino_event.is_set():
            agendar_proxima_consulta()
        print("Executada consulta")


start_button = ft.ElevatedButton(
    text="Iniciar Consulta",
    icon=ft.icons.PLAY_ARROW,
    on_click=lambda e: iniciar_consulta(page, start_button)  # Passa o botão para a função
)

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

def main(pg: ft.Page):
    global entry_data_inicio, entry_data_fim, spinner_label, text_area, varas_federais, varas_selecionadas, page, ultima_consulta, proxima_consulta 
    # selected_varas_list
    page = pg
    windowSize(page)

    page.title = f"Pesquisa automatizada - Circunscrições da JF do Paraná - Versão {VERSION}"
    
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    if not verificar_validade():
        pg.add(ft.Text("Este programa não é mais válido - permissão expirada. Entre em contato com o desenvolvedor feliped@mpf.mp.br pelo Zoom."))
        pg.update()
        return  # Encerra a execução se a validade não for atendida

    varas_federais = [vara.value for vara in VarasFederais]

    # Mapeamento dos valores para labels personalizados
    varas_labels = {
        VarasFederais.VARA_GUAIRA.value: "1ª VF Guaira",
        VarasFederais.VARA_FOZ_3.value: "3 VF de Foz",
        VarasFederais.VARA_UMUARAMA_1.value: "1ª VF Umuarama",
        VarasFederais.VARA_PONTA_GROSSA_1.value: "1ª VF Ponta Grossa",
        VarasFederais.VARA_MARINGA_3.value: "3ª VF Maringá",
        #VarasFederais.VARA_MARINGA_6.value: "6ª VF Maringá", #Somente previdenciarios
        VarasFederais.VARA_CASCAVEL_4.value: "4ª VF Cascavel",
        VarasFederais.VARA_FOZ_5.value: "5ª VF Foz",
        VarasFederais.VARA_LONDRINA_5.value: "5ª VF Londrina",
        VarasFederais.VARA_CURITIBA_9.value: "9ª VF Curitiba",
        VarasFederais.VARA_CURITIBA_13.value: "13ª VF Curitiba",
        VarasFederais.VARA_CURITIBA_14.value: "14ª VF Curitiba",
        VarasFederais.VARA_CURITIBA_23.value: "23ª VF Curitiba",
    }

    varas_selecionadas_iniciais = [
        VarasFederais.VARA_GUAIRA.value, #
        VarasFederais.VARA_FOZ_3.value, #
        VarasFederais.VARA_UMUARAMA_1.value, #
        VarasFederais.VARA_PONTA_GROSSA_1.value, #
        VarasFederais.VARA_MARINGA_3.value, #
        #VarasFederais.VARA_MARINGA_6.value, #Somente previdenciarios
        VarasFederais.VARA_CASCAVEL_4.value, #
        VarasFederais.VARA_FOZ_5.value, #
        VarasFederais.VARA_LONDRINA_5.value, #
        VarasFederais.VARA_CURITIBA_9.value, #
        VarasFederais.VARA_CURITIBA_13.value, #
        VarasFederais.VARA_CURITIBA_14.value, #
        VarasFederais.VARA_CURITIBA_23.value, #
    ]

    varas_selecionadas = varas_selecionadas_iniciais.copy()    

    def update_varas_selecionadas():
        varas_items = [
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=ft.Text(varas_labels.get(varas, varas), size=10),  # Usa o label personalizado se disponível
                            padding=ft.Padding(left=20, top=2, right=0, bottom=0),  # Espaço à esquerda do texto
                            width=get_text_width(varas_labels.get(varas, varas), 10) + 40,  # Ajustar largura para incluir espaço
                            height=25,
                            bgcolor=ft.colors.BLUE,
                            border_radius=5,
                            #on_click=lambda e, v=varas: remove_varas(v),
                            tooltip="Remover",
                        ),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.START,
                ),
                padding=5,
                col={"xs": 6, "sm": 3, "md": 3, "lg": 2, "xl": 2, "xxl": 1},
            )
            for varas in varas_selecionadas
        ]

        selected_varas_list.controls = [
            ft.Text(
                "Varas Federais selecionadas",
                size=16,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=varas_items,
                    spacing=10,
                ),
                padding=10,
                ink=True,
                border_radius=10,
                border=ft.border.all(1, ft.colors.GREY_900)
            )
        ]
        # Atualiza a página para refletir as mudanças
        page.update()    
    
    #Initialize selected_varas_list
    selected_varas_list = ft.ResponsiveRow(
        controls=[
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=[
                        ft.Container(
                            content=ft.Text(varas_labels.get(varas, varas), size=10),
                            padding=ft.Padding(left=20, top=2, right=0, bottom=0),
                            width=get_text_width(varas_labels.get(varas, varas), 10) + 40,
                            height=25,
                            bgcolor=ft.colors.BLUE,
                            border_radius=5,
                            #on_click=lambda e, v=varas: remove_varas(v),
                            tooltip="Remover",
                        ),
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.START,
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


    # Adiciona todos os elementos em uma única chamada
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
                        content=selected_varas_list,
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
    update_varas_selecionadas()
    atualizar_rodape()  # Atualiza a nota de rodapé

if __name__ == "__main__":
    ft.app(target=main)
