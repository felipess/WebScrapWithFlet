import pyperclip
import flet as ft
import time

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

    # Remove termo "Evento:" do texto, se presente
    texto = texto.replace("Evento:", "").strip()

    # Remove termo "Sala:" do texto, se presente
    texto = texto.replace("Sala:", "").strip()
    
    # Remove "Sala:" e tudo que vem depois
    # if "Sala:" in texto:
    #     texto = texto.split("- Sala:")[0].strip()
    
    # Copia o texto para a área de transferência
    pyperclip.copy(texto)
    exibir_alerta(page)
    print(f"Copiado texto: {texto}")

def obter_diferenca(resultados_novos, resultados_anteriores):
    diferencas = []
    for i, resultado in enumerate(resultados_novos):
        if i >= len(resultados_anteriores):
            diferencas.append(resultado)
        else:
            # Normaliza os textos para comparação
            resultado_normalizado = [normalizar_texto(campo) for campo in resultado]
            anterior_normalizado = [normalizar_texto(campo) for campo in resultados_anteriores[i]]

            if resultado_normalizado != anterior_normalizado:
                diferencas.append(resultado)
    return diferencas

def exibir_alerta(page):
    """Exibe um AlertDialog de confirmação."""
    copyAlert = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aviso", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        content=ft.Text("Texto copiado para área de transferência.", text_align=ft.TextAlign.CENTER),
    )
    page.open(copyAlert)
    time.sleep(2)
    page.close(copyAlert)


def exibir_alerta_fechamento(page):
    dlg = ft.AlertDialog(
        title=ft.Text("Aviso", size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
        content=ft.Text("Programa encerrando...", text_align=ft.TextAlign.CENTER),
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dlg)
    
def normalizar_texto(texto):
    """Remove espaços extras e normaliza o texto para evitar diferenças invisíveis."""
    return " ".join(texto.split()).strip()