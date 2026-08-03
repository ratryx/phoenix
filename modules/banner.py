"""
Módulo responsável pelo banner/identidade visual do Phoenix Optimizer no
modo CLI (terminal).

Reformulado para transmitir confiança e profissionalismo, em vez da
estética anterior (fogo vermelho intenso + fonte pesada), que recebeu
feedback de remeter a ferramentas de uso malicioso. A nova versão usa
uma paleta contida (dourado/âmbar sobre cinza-escuro), tipografia limpa
e um painel estruturado de status, no estilo de CLIs corporativas
(ex: ferramentas de DevOps e dashboards de terminal modernos).
"""

import pyfiglet
from rich.text import Text
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich import box

from modules.shared import console

# Paleta corporativa: dourado/âmbar contido, sem vermelho vivo.
# Usa cores nomeadas do Rich em vez de gradiente "fogo", para um efeito
# sóbrio e consistente — combina com a marca sem parecer agressivo.
COR_PRIMARIA = "#D89B4A"      # dourado/âmbar — cor de marca
COR_SECUNDARIA = "#8C8C8C"    # cinza neutro — texto de apoio
COR_DESTAQUE = "#E8B96A"      # âmbar claro — para realces pontuais
COR_SUCESSO = "#6FAE7C"
COR_ALERTA = "#D9A23B"
COR_ERRO = "#C2554A"


def gerar_logo_ascii(texto: str = "PHOENIX", fonte: str = "slant") -> str:
    """Gera o texto em ASCII art usando uma fonte limpa e moderna."""
    return pyfiglet.figlet_format(texto, font=fonte)


def exibir_banner(subtitulo: str = "Diagnóstico e Otimização de Performance",
                   versao: str = "2.0", modo: str = "CLI"):
    """
    Renderiza o banner no terminal: logo em ASCII art numa cor única
    (dourado contido), seguido de um painel de status com versão e modo.
    """
    logo = gerar_logo_ascii("PHOENIX")
    linhas = [l for l in logo.split("\n") if l.strip()]

    texto_logo = Text()
    for linha in linhas:
        texto_logo.append(linha + "\n", style=f"bold {COR_PRIMARIA}")

    console.print()
    console.print(Align.center(texto_logo))
    console.print(Align.center(f"[{COR_SECUNDARIA}]{subtitulo}[/{COR_SECUNDARIA}]"))
    console.print()

    # Painel de status — reforça a sensação de produto, não de script solto
    tabela_status = Table.grid(padding=(0, 2))
    tabela_status.add_column(justify="right", style=COR_SECUNDARIA)
    tabela_status.add_column(style="white")
    tabela_status.add_row("Versão:", f"[bold]{versao}[/bold]")
    tabela_status.add_row("Modo:", f"[bold]{modo}[/bold]")
    tabela_status.add_row("Sistema:", "Windows 10 / 11")

    console.print(Align.center(Panel(
        tabela_status,
        border_style=COR_PRIMARIA,
        box=box.ROUNDED,
        padding=(0, 3),
    )))
    console.print()


def exibir_secao(titulo: str):
    """Exibe um cabeçalho de seção padronizado, usado antes de cada bloco de ação."""
    console.print()
    console.print(Panel(
        f"[bold white]{titulo}[/bold white]",
        border_style=COR_PRIMARIA,
        box=box.ROUNDED,
        expand=True,
    ))


def exibir_separador():
    """Linha separadora discreta entre blocos de conteúdo."""
    console.rule(style=COR_SECUNDARIA)


def msg_sucesso(texto: str):
    console.print(f"[{COR_SUCESSO}][OK][/{COR_SUCESSO}] {texto}")


def msg_alerta(texto: str):
    console.print(f"[{COR_ALERTA}][AVISO][/{COR_ALERTA}] {texto}")


def msg_erro(texto: str):
    console.print(f"[{COR_ERRO}][ERRO][/{COR_ERRO}] {texto}")


def msg_info(texto: str):
    console.print(f"[{COR_SECUNDARIA}]•[/{COR_SECUNDARIA}] {texto}")


if __name__ == "__main__":
    exibir_banner()
    exibir_secao("Exemplo de seção")
    msg_sucesso("Mensagem de sucesso")
    msg_alerta("Mensagem de alerta")
    msg_erro("Mensagem de erro")
    msg_info("Mensagem informativa")
