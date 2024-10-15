import pyperclip
import flet as ft

def copiar_linha(conteudo_linha, page, ordem_colunas):
    conteudo_ordenado = [conteudo_linha[i] for i in ordem_colunas]

    if len(conteudo_ordenado) > 0:  # Verifica se a coluna 0 existe
        coluna_0_texto = conteudo_ordenado[0]

        if "Observação:" in coluna_0_texto:
            coluna_0_texto = coluna_0_texto.split("Observação:")[0].strip() # Remove "Observação:" e tudo o que vem depois       
        conteudo_ordenado[0] = coluna_0_texto  

    if len(conteudo_ordenado) > 4:  # Verifica se a coluna 4 existe
        coluna_4_texto = conteudo_ordenado[4]
        
        conteudo_ordenado[4] = coluna_4_texto  # Atualiza a coluna 4 com o texto modificado

    # Formata o texto final
    texto = ' - '.join(conteudo_ordenado)  # Une o conteúdo da linha em uma string

    # Remove "Evento:" do texto, se presente
    texto = texto.replace("Evento:", "").strip()
    
    # Remove "Sala:" e tudo que vem depois
    if "Sala:" in texto:
        texto = texto.split("- Sala:")[0].strip()
    
    # Copia o texto para a área de transferência
    pyperclip.copy(texto)
    exibir_alerta(page)
    print(f"Copiado texto: {texto}")

def obter_diferenca(resultados_novos, resultados_anteriores):
    diferencas = []
    for i, resultado in enumerate(resultados_novos):
        if i >= len(resultados_anteriores) or resultado != resultados_anteriores[i]:
            diferencas.append(resultado)
    return diferencas

def exibir_alerta(page):
    """Exibe um AlertDialog de confirmação."""
    dlg = ft.AlertDialog(
        title=ft.Text("Aviso", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        content=ft.Text("Texto copiado para a área de transferência."),
        actions=[ft.TextButton("Fechar", on_click=lambda e: page.close(dlg))],
        actions_alignment=ft.MainAxisAlignment.END,
        # modal=True,
        # on_dismiss=lambda e: page.add(ft.Text("Non-modal dialog dismissed")),
    )
    page.open(dlg)