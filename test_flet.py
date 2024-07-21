import flet as ft
from VarasFederais import VarasFederais

def main(page: ft.Page):
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
    text_area_content = (
        "Aqui você pode adicionar um texto longo que será exibido sem rolagem. " * 10
    )

    text_area = ft.Text(
        value=text_area_content,
        size=12,
        text_align=ft.TextAlign.LEFT,
        width=580,  # Ajuste a largura conforme necessário
        height=250, # Ajuste a altura conforme necessário
        #bgcolor=ft.colors.BLUE_GREY_900  # Cor de fundo para visualização
    )

    page.add(
        ft.Column(
            controls=[
                ft.Text("Selecione a Vara", size=12),
                varas_dropdown,
                add_button,
                ft.Text("Varas Selecionadas", size=12),
                selected_varas_list,
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
