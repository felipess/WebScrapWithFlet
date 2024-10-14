import pyperclip

def copiar_linha(conteudo_linha, ordem_colunas):
    conteudo_ordenado = [conteudo_linha[i] for i in ordem_colunas]
    
    if len(conteudo_ordenado) > 0:
        coluna_0_texto = conteudo_ordenado[0].split("Observação:")[0].strip()  
        conteudo_ordenado[0] = coluna_0_texto

    texto = ' - '.join(conteudo_ordenado).replace("Evento:", "").strip()
    if "Sala:" in texto:
        texto = texto.split("- Sala:")[0].strip()
    
    pyperclip.copy(texto)
    print("Copiado texto: " + texto)

def obter_diferenca(resultados_novos, resultados_anteriores):
    diferencas = []
    for i, resultado in enumerate(resultados_novos):
        if i >= len(resultados_anteriores) or resultado != resultados_anteriores[i]:
            diferencas.append(resultado)
    return diferencas