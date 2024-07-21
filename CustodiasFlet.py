import time
import threading
from datetime import datetime, timedelta
from VarasFederais import * 
import flet as ft
from flet import Page, TextField, IconButton, ElevatedButton, Column, Row, Timer, SnackBar, Text, CheckBox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Definir eventos globais
termino_event = threading.Event()
running_event = threading.Event()

# Intervalo entre consultas (em segundos)
intervalo_consulta = 300  # 5 minutos

def mostrar_splash_screen(page):
    # Função para exibir a splash screen
    splash_page = ft.Page()
    splash_page.add(ft.Text("Aguarde, carregando...", size=20))
    splash_page.update()
    splash_page.show()
    time.sleep(2)
    splash_page.close()

def importar_bibliotecas():
    global webdriver, By, WebDriverWait, EC
    global datetime, timedelta
    global BeautifulSoup

def iniciar_programa_principal(page):
    # Configuração inicial
    importar_bibliotecas()
    
    # Lista inicial de varas federais
    varas_federais = [
        VarasFederais.VARA_GUAIRA.value, 
        VarasFederais.VARA_PONTA_GROSSA_1.value,
        VarasFederais.VARA_UMUARAMA_1.value, 
        VarasFederais.VARA_FOZ_3.value,
        VarasFederais.VARA_MARINGA_3.value, 
        VarasFederais.VARA_CASCAVEL_4.value, 
        VarasFederais.VARA_FOZ_5.value, 
        VarasFederais.VARA_LONDRINA_5.value, 
        VarasFederais.VARA_CURITIBA_9.value,
        VarasFederais.VARA_CURITIBA_13.value,            
        VarasFederais.VARA_CURITIBA_14.value,
        VarasFederais.VARA_CURITIBA_23.value
    ]
    
    # Obtém a data atual
    data_atual = datetime.now().strftime('%d/%m/%Y')

    # Criação dos elementos Flet
    text_area = ft.TextField(label="Resultados", multiline=True, expand=True)
    
    # Listas para varas
    lista_varas_selecionadas = ft.Column()
    lista_varas_disponiveis = ft.Column()
    
    for vara in varas_federais:
        lista_varas_selecionadas.controls.append(ft.CheckBox(label=vara, value=True))
    
    for vara in [vara.value for vara in VarasFederais if vara.value not in varas_federais]:
        lista_varas_disponiveis.controls.append(ft.CheckBox(label=vara))

    # Campo de entrada para datas
    entry_data_inicio = ft.TextField(label="Inicio", value=data_atual, width=100)
    entry_data_fim = ft.TextField(label="Final", value=data_atual, width=100)
    
    # Horários
    ultimo_horario = ft.TextField(label="Última Consulta", value="", width=200)
    proximo_horario = ft.TextField(label="Próxima Consulta", value="", width=200)
    
    # Botões
    btn_adicionar = ft.IconButton(icon="add", on_click=lambda e: adicionar_vara())
    btn_remover = ft.IconButton(icon="remove", on_click=lambda e: remover_vara())
    btn_consultar = ft.ElevatedButton(text="Consultar", on_click=lambda e: iniciar_consulta())
    
    # Funções para adicionar e remover varas
    def adicionar_vara():
        selecionadas = [cb.label for cb in lista_varas_disponiveis.controls if cb.value]
        if not selecionadas:
            page.snack_bar(ft.SnackBar("Selecione uma ou mais varas para adicionar."))
            return
        for vara in selecionadas:
            varas_federais.append(vara)
            lista_varas_selecionadas.controls.append(ft.CheckBox(label=vara, value=True))
            for cb in lista_varas_disponiveis.controls:
                if cb.label == vara:
                    lista_varas_disponiveis.controls.remove(cb)
                    break
        page.update()

    def remover_vara():
        selecionadas = [cb.label for cb in lista_varas_selecionadas.controls if cb.value]
        if not selecionadas:
            page.snack_bar(ft.SnackBar("Selecione uma ou mais varas para remover."))
            return
        for vara in selecionadas:
            varas_federais.remove(vara)
            lista_varas_disponiveis.controls.append(ft.CheckBox(label=vara))
            for cb in lista_varas_selecionadas.controls:
                if cb.label == vara:
                    lista_varas_selecionadas.controls.remove(cb)
                    break
        page.update()

    def atualizar_horarios():
        agora = datetime.now()
        ultimo_horario.value = f"Última Consulta: {agora.strftime('%H:%M:%S')}"
        proximo_horario.value = f"Próxima Consulta: {(agora + timedelta(seconds=intervalo_consulta)).strftime('%H:%M:%S')}"
        page.update()
    
    def iniciar_consulta():
        consulta_thread = threading.Thread(target=executar_consulta)
        consulta_thread.start()

    def atualizar_resultados(resultados):
        text_area.value = "\n".join(resultados)
        page.update()
    
    def executar_consulta():
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        resultados = []

        try:
            driver.get("https://eproc.jfpr.jus.br/eprocV2/externo_controlador.php?acao=pauta_audiencias")
            wait.until(EC.presence_of_element_located((By.ID, "divRowVaraFederal")))
            campo_data_inicio = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataInicio")))
            data_inicio = entry_data_inicio.value.strip()
            campo_data_inicio.clear()
            campo_data_inicio.send_keys(data_inicio)
            data_fim = entry_data_fim.value.strip()
            campo_data_fim = wait.until(EC.presence_of_element_located((By.ID, "txtVFDataTermino")))
            campo_data_fim.clear()
            campo_data_fim.send_keys(data_fim)
            
            titulos = [" Data/Hora: ", " Autos:", "", "", "", "Status", "Sistema"]

            for idx, vara in enumerate(varas_federais):
                try:
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

            atualizar_horarios()
            atualizar_resultados(resultados)

        except Exception as e:
            resultados.append("Ocorreu um erro durante a consulta. Tente novamente mais tarde.")
            
        finally:
            driver.quit()
            if not termino_event.is_set():
                agendar_proxima_consulta()

    def agendar_proxima_consulta():
        if running_event.is_set():
            return
        page.add(ft.Timer(seconds=intervalo_consulta, on_timeout=iniciar_consulta))

    # Adiciona elementos à página
    page.add(
        ft.Column(
            [
                text_area,
                ft.Row([entry_data_inicio, entry_data_fim]),
                ft.Row([btn_adicionar, btn_remover]),
                ft.Row([lista_varas_selecionadas, btn_consultar, lista_varas_disponiveis]),
                ft.Row([ultimo_horario, proximo_horario])
            ]
        )
    )
    
    # Função para fechar a página
    def fechar_pagina(e):
        termino_event.set()
        page.close()
    
    # Eventos
    page.on_close = fechar_pagina

    mostrar_splash_screen(page)
    iniciar_consulta()

# Cria e mostra a página principal
ft.app(target=iniciar_programa_principal)
