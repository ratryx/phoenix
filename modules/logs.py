"""
Módulo de logs: registra cada atendimento feito com o Phoenix Optimizer
em arquivos JSON (dados estruturados, fáceis de comparar depois) e também
em um arquivo .txt legível, para você ter histórico por cliente/PC.

Os logs ficam salvos em uma pasta "logs" ao lado do executável, organizados
por data, então você consegue mostrar pro cliente o histórico de manutenções.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()


def obter_pasta_logs() -> Path:
    """
    Retorna a pasta de logs em um local sempre gravável.

    Importante: NÃO usamos a pasta do executável aqui, porque quando o
    programa é instalado em "C:\\Program Files\\..." (padrão do Inno Setup),
    o Windows bloqueia escrita nessa pasta para a aplicação, mesmo rodando
    como administrador. Isso fazia o programa travar/fechar ao tentar
    salvar qualquer log.

    Em vez disso, usamos %PROGRAMDATA%\\PhoenixOptimizer\\logs no Windows
    (pasta padrão para dados de aplicações, sempre gravável), ou uma pasta
    local "logs" ao lado do script quando em modo desenvolvimento/Linux.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("PROGRAMDATA", Path.home())) / "PhoenixOptimizer"
    elif getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent

    pasta = base / "logs"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def gerar_id_atendimento() -> str:
    """Gera um identificador único de atendimento baseado em data/hora."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def salvar_snapshot(id_atendimento: str, tipo: str, dados: dict, nome_cliente: str = ""):
    """
    Salva um snapshot de dados (ex: diagnóstico 'antes' ou 'depois') em JSON.
    tipo: 'antes' ou 'depois'
    """
    pasta = obter_pasta_logs()
    nome_arquivo = f"{id_atendimento}_{tipo}.json"
    caminho = pasta / nome_arquivo

    registro = {
        "id_atendimento": id_atendimento,
        "tipo": tipo,
        "cliente": nome_cliente or "não informado",
        "data_hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "dados": dados,
    }

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

    return caminho


def carregar_snapshot(id_atendimento: str, tipo: str) -> dict | None:
    """Carrega um snapshot salvo anteriormente (antes ou depois)."""
    pasta = obter_pasta_logs()
    caminho = pasta / f"{id_atendimento}_{tipo}.json"
    if not caminho.exists():
        return None
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def registrar_acao(id_atendimento: str, acao: str, detalhe: str = "", nome_cliente: str = ""):
    """
    Adiciona uma linha no log de texto legível (.txt) do atendimento,
    registrando cada ação realizada (limpeza, otimização, etc).
    """
    pasta = obter_pasta_logs()
    caminho = pasta / f"{id_atendimento}_atendimento.txt"

    cabecalho_necessario = not caminho.exists()

    with open(caminho, "a", encoding="utf-8") as f:
        if cabecalho_necessario:
            f.write("=" * 60 + "\n")
            f.write(f"PHOENIX OPTIMIZER - Registro de Atendimento\n")
            f.write(f"ID: {id_atendimento}\n")
            f.write(f"Cliente: {nome_cliente or 'não informado'}\n")
            f.write(f"Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

        agora = datetime.now().strftime("%H:%M:%S")
        linha = f"[{agora}] {acao}"
        if detalhe:
            linha += f" — {detalhe}"
        f.write(linha + "\n")


def listar_atendimentos() -> list:
    """Lista todos os atendimentos já registrados, ordenados do mais recente para o mais antigo."""
    pasta = obter_pasta_logs()
    atendimentos = {}

    for arquivo in pasta.glob("*_antes.json"):
        id_atendimento = arquivo.stem.replace("_antes", "")
        with open(arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
        atendimentos[id_atendimento] = dados

    return sorted(atendimentos.values(), key=lambda x: x["id_atendimento"], reverse=True)


def exibir_historico():
    """Exibe uma tabela com todos os atendimentos já feitos (histórico de uso do programa)."""
    atendimentos = listar_atendimentos()

    if not atendimentos:
        console.print(Panel(
            "[yellow]Nenhum atendimento registrado ainda.[/yellow]\n"
            "Use a opção de 'Rotina completa' para gerar o primeiro registro.",
            border_style="orange3"
        ))
        return

    tabela = Table(title="Histórico de Atendimentos", box=box.ROUNDED, border_style="orange3")
    tabela.add_column("ID", style="dim")
    tabela.add_column("Cliente", style="bold white")
    tabela.add_column("Data/Hora", style="yellow")

    for at in atendimentos:
        tabela.add_row(at["id_atendimento"], at["cliente"], at["data_hora"])

    console.print(tabela)
    console.print(f"\n[dim]Logs salvos em: {obter_pasta_logs()}[/dim]")


if __name__ == "__main__":
    exibir_historico()
