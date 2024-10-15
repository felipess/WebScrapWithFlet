# requisitos 
- Inno Setup para criar um instador - script na raiz

# cmds
PS C:\repos\Github\WebScrapWithFlet> flet run CustodiasFlet.py
# é esse:
PS C:\repos\Github\WebScrapWithFlet> flet run .\test_flet.py

# WebScrap
# execução para criação do .exe 
py -m PyInstaller --onefile --windowed .\CustodiasJFPR2.py

# para ja renomear o exe na saida
py -m PyInstaller --onefile --windowed --name CustodiasApp .\CustodiasNoFirefox.py

# Comando completo para adicionar >>> Icone na janela
Deve arquivo deve estar em assests no formato .ico
py -m PyInstaller --onefile --windowed --name CustodiasApp --icon="C:\repos\Github\WebScrapWithFlet\assets\justice_icon.ico" .\CustodiasNoFirefox.py

# ficara dentro da pasta dist


Consulta de Audiências de Custódia

Este programa foi desenvolvido para automatizar a consulta de audiências de custódia nas varas federais do Paraná. 
Requisitos:
- Internet estável.
- Navegador Chrome atualizado.
- Sistema Windows.
- Site da JFPR (https://eproc.jfpr.jus.br/) em funcionamento

Aviso: Não substitui os métodos convencionais de consulta de audiências, servindo apenas como ferramenta auxíliar.
                           
Em caso de ausência de alguma vara federal que realize audiências de custódia, informar pelo zoom.

Desenvolvido por feliped@mpf.mp.br
Prm-Foz/Nucrimj/Subjur

# README USUARIO
# Ajustes 
1. Quando tem (nova) audiência o programa maximiza a janela - funcionando como um alerta;
2. ao clicar no Botão de iniciar, ele fica inativo para evitar pesquisas em paralelo;
3. quando copia o texto da custódia, já formata e deixa pronto para colar no Zoom sem necessidade de edição, remove informações desnecessárias e coloca hífen;
4. intervalo de busca reduzido para execução a cada 10 minutos;
5. mudança de funcionamento do Chrome para Firefox para remoção do bug da janela em branco.

Observação:
Deve ter instalado o navegador Firefox no computador para funcionamento.

