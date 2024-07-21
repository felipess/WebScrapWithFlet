import flet as ft
from VarasFederais import VarasFederais
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import threading

# Definição dos eventos globais
running_event = threading.Event()
termino_event = threading.Event()

def executar_consulta():
    running_event.set()
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')  # Desativado o modo headless para observação
    options.add_argument("--blink-settings=loadMediaAutomatically=2")  # Configuração adicional
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)  # Aumentando o tempo de espera para 20 segundos

    try:
        resultados = []
        driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")
        wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))
        campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataInicio")))

        # Atualize as datas usando os valores atuais dos campos de entrada
        data_inicio = entry_data_inicio.value.strip()
        campo_data_inicio.clear()
        campo_data_inicio.send_keys(data_inicio)           
        
        data_fim = entry_data_fim.value.strip()
        campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataTermino")))
        campo_data_fim.clear()
        campo_data_fim.send_keys(data_fim)

        titulos = [" Data/Hora: ", " Autos:", "", "", "", "Status", "Sistema"]
        
        for idx, vara in enumerate(varas_federais):
            if termino_event.is_set():  # Verifica se o evento de término foi sinalizado
                break
            
            try:
                # Atualiza o spinner_label com a vara atual
                spinner_label.value = f"Consultando {vara}..."
                page.update()

                vara_federal_div = wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))
                dropdown_button = vara_federal_div.find_element(By.CLASS_NAME, "dropdown-toggle")
                dropdown_button.click()
                vara_federal_option = wait.until(EC.element_to_be_clickable((By.XPATH, f"//option[text()='{vara}']")))
                vara_federal_option.click()

                # Adiciona um pequeno intervalo de espera entre as mudanças de vara
                if idx > 0:
                    time.sleep(2)  # Ajuste o tempo conforme necessário

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
        spinner_label.value = ""  # Limpa o spinner após a consulta
        page.update()
        running_event.clear()  # Marca a consulta como finalizada
        driver.quit()
        if not termino_event.is_set():
            agendar_proxima_consulta()

# Função para atualizar o resultado na interface do Flet
def atualizar_resultados(resultados):
    result_text = "\n".join(resultados)
    text_area.value = result_text
    page.update()

def iniciar_consulta(e):
    threading.Thread(target=executar_consulta).start()

def main(page: ft.Page):
    global varas_federais, varas_dropdown, selected_varas_list, text_area, spinner_label, entry_data_inicio, entry_data_fim
    
    # Define o tamanho inicial da janela
    page.window_width = 640
    page.window_height = 900

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

    def update_varas_selecionadas():
        selected_varas_list.controls = [
            ft.Text(varas, width=580, size=10) for varas in varas_selecionadas
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
        controls=[ft.Text(varas, width=580, size=10) for varas in varas_selecionadas]
    )

    # Área de texto para exibir resultados
    text_area_content = "Aqui você pode adicionar um texto longo que será exibido sem rolagem. " * 10
    text_area = ft.Text(
        value=text_area_content,
        size=12,
        text_align=ft.TextAlign.LEFT,
        width=580,
        height=250,
        bgcolor=ft.colors.BLACK,  # Cor de fundo para visualização
    )

    spinner_label = ft.Text("", size=12, text_align=ft.TextAlign.CENTER)
    entry_data_inicio = ft.TextField(label="Data Início", width=580, height=40)
    entry_data_fim = ft.TextField(label="Data Fim", width=580, height=40)
    
    consulta_button = ft.ElevatedButton(
        text="Iniciar Consulta",
        on_click=iniciar_consulta
    )

    page.add(
        ft.Column(
            controls=[
                ft.Text("Selecione a Vara", size=12),
                varas_dropdown,
                add_button,
                ft.Text("Varas Selecionadas", size=12),
                selected_varas_list,
                spinner_label,
                entry_data_inicio,
                entry_data_fim,
                consulta_button,
                ft.Container(
                    content=text_area,
                    margin=10,
                    padding=10,
                    alignment=ft.alignment.center,
                    bgcolor=ft.colors.BLACK,  # Ajuste a cor de fundo conforme necessário
                    width=580,
                    height=250,
                    border_radius=10,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        ),
    )

ft.app(target=main)
