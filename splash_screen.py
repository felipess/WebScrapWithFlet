# splash_screen.py
import flet as ft
import time

def splash_screen(page):
    # page.window.width = 600
    # page.window.height = 150
    window_width = 400
    window_height = 300
    page.window.width = window_width
    page.window.height = window_height
    page.window.maximized = False  # Não maximiza a janela
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Centraliza a janela no monitor
    page.window.center()


    splash_container = ft.Container(
        content=ft.Column(
            controls=[
                # Logo (substitua pelo caminho do seu logo)
                # ft.Image(src="path/to/your/logo.png", width=150, height=150),  
                ft.Text("Carregando, por favor aguarde...", size=16, color=ft.colors.BLUE),
                # ProgressBar interativa
                ft.ProgressBar(width=window_width-20, value=0),
                ft.Container(height=20),  # Espaçamento
                # ft.Text("Aguarde enquanto carregamos os dados.", size=14, color=ft.colors.GREY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10  # Espaçamento entre os controles
        ),
        # width=page.width,
        # height=page.height,
        border_radius=10,  # Bordas arredondadas
    )
    
    # Adiciona a tela splash à página
    page.add(splash_container)
    page.update()
    
    # Obtém a referência para a ProgressBar
    pb = splash_container.content.controls[1]
    
    # Atualiza o valor da ProgressBar de forma interativa
    for i in range(101):
        pb.value = i * 0.01  # Atualiza o valor da ProgressBar
        time.sleep(0.03)  # Aguarda um pouco antes de atualizar novamente
        page.update()  # Atualiza a página para refletir a nova barra de progresso
    
    # Espera um momento antes de remover a tela splash
    # time.sleep(2)
    
    # Remove a tela splash
    page.controls.remove(splash_container)
    page.update()  # Atualiza a página para remover o splash