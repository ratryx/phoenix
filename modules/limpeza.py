"""
Módulo de limpeza CLI: interface de linha de comando para cleanup_service.
Sempre soma o espaço liberado para exibir no relatório final.
"""

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from modules.shared import console
from modules.core.cleanup_service import executar_limpeza, _obter_alvos_limpeza

def bytes_para_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)

def executar_limpeza_completa(id_atendimento: str = None):
    """Executa a limpeza completa do sistema e exibe relatório de espaço liberado no terminal."""
    console.print(Panel("[bold yellow]Iniciando limpeza do sistema...[/bold yellow]", border_style="orange3"))

    total_liberado_mb = 0.0
    
    with Progress(
        SpinnerColumn(style="orange3"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(complete_style="orange3"),
        console=console,
    ) as progress:
        
        tarefa = progress.add_task("Preparando limpeza...", total=100)
        
        def progress_cb(mensagem, progresso, detalhes):
            progress.update(tarefa, description=mensagem, completed=progresso)
            
        resultados = executar_limpeza(
            progress_callback=progress_cb,
            incluir_lixeira=False # Comportamento original
        )
        total_liberado_mb = resultados["espaco_liberado_mb"]
        
    console.print()
    
    for cat in resultados["categorias"]:
        nome = cat["nome"]
        mb = bytes_para_mb(cat["espaco_liberado_bytes"])
        if cat["status"] == "concluido" and mb > 0:
            console.print(f"  [green]\\[OK][/green] {nome}: [yellow]{mb} MB[/yellow] liberados")
        elif cat["status"] == "parcial":
            console.print(f"  [yellow]\\[AVISO][/yellow] {nome}: [yellow]{mb} MB[/yellow] liberados (com ignorados)")
        elif cat["status"] == "falhou":
            console.print(f"  [red]\\[ERRO][/red] {nome}: Falha na limpeza")
        elif cat["status"] == "cancelado":
            console.print(f"  [red]\\[ERRO][/red] {nome}: Cancelado")
        else:
            console.print(f"  [dim]\\[INFO][/dim] {nome}: [dim]nada a limpar[/dim]")
            
    for aviso in resultados["avisos"]:
        console.print(f"  [yellow]\\[AVISO][/yellow] {aviso}")

    console.print()
    console.print(Panel(
        f"[bold green]Limpeza concluída! Total liberado: {total_liberado_mb} MB[/bold green]",
        border_style="green"
    ))

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Limpeza executada", f"{total_liberado_mb} MB liberados")

    return int(total_liberado_mb * (1024 ** 2)) # Compatibilidade com retorno em bytes


if __name__ == "__main__":
    executar_limpeza_completa()
