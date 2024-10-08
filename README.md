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
py -m PyInstaller --onefile --windowed --name CustodiasApp_v1.5 .\CustodiasNoFirefox.py


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
