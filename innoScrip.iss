# ajustar nome do arquivo / caminho etc
[Setup]
AppName=CustodiasFoz
AppVersion=1.0
DefaultDirName={pf}\CustodiasApp
DefaultGroupName=SeuApp
OutputDir=C:\Users\felip\OneDrive\Área de Trabalho\InnoBuilds
OutputBaseFilename=instalador
Compression=lzma
SolidCompression=yes

[Files]
Source: "C:\Users\felip\OneDrive\Área de Trabalho\dist\test3e5VF.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SeuApp"; Filename: "{app}\test3e5VF.exe"
Name: "{commondesktop}\SeuApp"; Filename: "{app}\test3e5VF.exe"