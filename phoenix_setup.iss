; ============================================================
; Phoenix Optimizer - Script Inno Setup
; ============================================================
; Este script gera um instalador profissional (.exe) para o
; Phoenix Optimizer, incluindo:
;   - Ícone personalizado (fênix)
;   - Atalho no Menu Iniciar e, opcionalmente, na Área de Trabalho
;   - Desinstalador automático
;   - Solicitação de privilégios de administrador (necessário,
;     já que o programa altera registro/serviços do Windows)
;
; COMO USAR:
;   1. Antes de compilar este script, gere o .exe do programa com:
;        pyinstaller --onefile --name PhoenixOptimizer --icon=assets\phoenix.ico phoenix.py
;      Isso vai criar o arquivo em: dist\PhoenixOptimizer.exe
;
;   2. Baixe e instale o Inno Setup (gratuito):
;        https://jrsoftware.org/isdl.php
;
;   3. Abra este arquivo (phoenix_setup.iss) no Inno Setup Compiler
;      e clique em "Compile" (ou aperte F9).
;
;   4. O instalador final vai aparecer na pasta "output" definida abaixo,
;      pronto para distribuir/vender aos seus clientes.
; ============================================================

#define MyAppName "Phoenix Optimizer"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Phoenix"
#define MyAppExeName "PhoenixOptimizer.exe"
#define MyAppIcon "assets\phoenix.ico"

[Setup]
; Identificador único do app (gerado uma vez, não mude entre versões
; para que atualizações substituam a instalação anterior corretamente)
AppId={{B4F3E7A1-9C2D-4A6E-8F1B-3D5C7E9A2B4F}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Exige privilégios de administrador na instalação E na execução,
; já que o programa precisa alterar registro e serviços do Windows
PrivilegesRequired=admin
OutputDir=output
OutputBaseFilename=PhoenixOptimizer_Setup_{#MyAppVersion}
SetupIconFile={#MyAppIcon}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Cores do instalador (tema escuro combinando com a marca fênix)
WizardImageStretch=no
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na Área de Trabalho"; GroupDescription: "Ícones adicionais:"

[Files]
; Executável principal (gerado pelo PyInstaller).
; Observação: como o build usa --onefile, os arquivos da pasta gui/
; (HTML/CSS/JS do Modo GUI) já ficam embutidos dentro do próprio .exe
; e são extraídos automaticamente em uma pasta temporária ao executar
; — não é necessário copiá-los separadamente aqui.
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Ícone da marca
Source: "{#MyAppIcon}"; DestDir: "{app}\assets"; Flags: ignoreversion
; Documentação
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\phoenix.ico"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\phoenix.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName} agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Os logs de atendimento agora ficam em %PROGRAMDATA%\PhoenixOptimizer\logs,
; fora da pasta de instalação — não são removidos automaticamente ao
; desinstalar, para preservar o histórico de atendimentos do usuário.
; Caso queira removê-los manualmente, apague:
;   C:\ProgramData\PhoenixOptimizer

[Messages]
brazilianportuguese.WelcomeLabel2=Este assistente vai instalar o [name/ver] no seu computador.%n%nRecomendamos fechar outros programas de otimização antes de continuar.
