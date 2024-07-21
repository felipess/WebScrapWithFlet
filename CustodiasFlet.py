import flet as ft
from datetime import datetime, timedelta
import threading
import time

def main(page: ft.Page):
    running_event = threading.Event()
    global terminando  # Usa a variável global

    # Função para atualizar horários
    def atualizar_horarios():
        agora = datetime.now()
        proximo = agora + timedelta(seconds=10)
        proximo_horario.value = f"Próxima consulta: {proximo.strftime('%H:%M:%S')}"
        ultimo_horario.value = f"Última consulta: {agora.strftime('%H:%M:%S')}"
        page.update()
        page.timer(10000, atualizar_horarios)  # Atualiza a cada 10 segundos

    # Função para adicionar vara
    def adicionar_vara(e):
        selecionadas = lista_varas_disponiveis.selected_items
        for vara in selecionadas:
            lista_varas_selecionadas.items.append(vara)
            lista_varas_disponiveis.items.remove(vara)
        page.update()

    # Função para remover vara
    def remover_vara(e):
        selecionadas = lista_varas_selecionadas.selected_items
        for vara in selecionadas:
            lista_varas_disponiveis.items.append(vara)
            lista_varas_selecionadas.items.remove(vara)
        page.update()

    # Função para iniciar a busca
    def iniciar_busca(e):
        global terminando
        running_event.set()
        terminando = False

        def buscar():
            while running_event.is_set() and not terminando:
                try:
                    text_field.value += f"Buscando informações em {datetime.now().strftime('%H:%M:%S')}\n"
                    page.update()
                    time.sleep(5)
                except Exception as e:
                    text_field.value += f"Erro: {e}\n"
                    page.update()

            running_event.clear()

        busca_thread = threading.Thread(target=buscar)
        busca_thread.start()

        def parar_busca(e):
            global terminando
            terminando = True
            running_event.clear()
            page.update()

        btn_parar.visible = True
        btn_parar.on_click = parar_busca
        page.update()

    # Configura a tela principal
    page.title = "Programa Principal"
    
    ultimo_horario = ft.TextField(value="Última consulta", read_only=True)
    proximo_horario = ft.TextField(value="Próxima consulta", read_only=True)
    
    lista_varas_disponiveis = ft.ListView()
    lista_varas_selecionadas = ft.ListView()
    
    text_field = ft.TextField(multiline=True, height=200)  # Usando TextField como área de texto
    
    # Criando os botões com base na documentação
    btn_iniciar = ft.buttons.Button(text="Iniciar Busca", on_click=iniciar_busca)
    btn_parar = ft.buttons.Button(text="Parar Busca", visible=False)
    
    page.add(
        ft.Column(
            controls=[
                ultimo_horario,
                proximo_horario,
                ft.Row(
                    controls=[
                        ft.Column(
                            controls=[
                                lista_varas_disponiveis,
                                ft.buttons.Button(text="Adicionar Vara", on_click=adicionar_vara),
                                ft.buttons.Button(text="Remover Vara", on_click=remover_vara),
                            ]
                        ),
                        lista_varas_selecionadas,
                    ]
                ),
                text_field,
                btn_iniciar,
                btn_parar,
            ],
        )
    )

    # Inicia a atualização de horários
    atualizar_horarios()

# Inicia a aplicação
ft.app(target=main)
