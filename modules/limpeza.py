"""
Módulo de limpeza CLI: interface de linha de comando para cleanup_service.
Sempre soma o espaço liberado para exibir no relatório final.
"""

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from modules.shared import console
from modules.core.cleanup_service import executar_limpeza

def bytes_para_mb(valor: int) -> float:
    return round(valor / (1024 ** 2), 2)

def executar_limpeza_completa(id_atendimento: str = None):
    """Executa a limpeza completa do sistema e exibe relatório de espaço liberado no terminal."""
    console.print(Panel("[bold yellow]Iniciando limpeza do sistema...[/bold yellow]", border_style="orange3"))

    total_liberado_bytes = 0
    resultados = None
    
    with Progress(
        SpinnerColumn(style="orange3"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(complete_style="orange3"),
        console=console,
    ) as progress:
        
        tarefa = progress.add_task("Preparando limpeza...", total=100)
        
        def progress_cb(mensagem, progresso, detalhes):
            progress.update(tarefa, description=mensagem, completed=progresso)
            
        try:
            resultados = executar_limpeza(
                progress_callback=progress_cb,
                incluir_lixeira=False
            )
        except Exception:
            resultados = {"ok": False, "parcial": False, "erro": "Cancelado ou falhou", "categorias": [], "avisos": [], "espaco_liberado_bytes": 0, "espaco_liberado_mb": 0}
            
    if resultados:
        total_liberado_bytes = resultados.get("espaco_liberado_bytes", 0)
        
    console.print()
    
    if resultados and "categorias" in resultados:
        for cat in resultados["categorias"]:
            nome = cat["nome"]
            mb = bytes_para_mb(cat["espaco_liberado_bytes"])
            status = cat.get("status")
            
            if status == "concluido":
                if mb > 0:
                    console.print(f"  [green]\\[OK][/green] {nome}: [yellow]{mb} MB[/yellow] liberados")
                else:
                    console.print(f"  [dim]\\[INFO][/dim] {nome}: [dim]nada a limpar[/dim]")
            elif status == "parcial":
                console.print(f"  [yellow]\\[AVISO][/yellow] {nome}: [yellow]{mb} MB[/yellow] liberados (com ignorados)")
            elif status == "falhou":
                console.print(f"  [red]\\[ERRO][/red] {nome}: Falha na limpeza")
            elif status == "cancelado":
                console.print(f"  [red]\\[ERRO][/red] {nome}: Cancelado")
            else:
                console.print(f"  [dim]\\[INFO][/dim] {nome}: [dim]status desconhecido[/dim]")
                
        for aviso in resultados.get("avisos", []):
            console.print(f"  [yellow]\\[AVISO][/yellow] {aviso}")

    console.print()
    
    ok = resultados.get("ok", False)
    parcial = resultados.get("parcial", False)
    mb_total = resultados.get("espaco_liberado_mb", 0)
    
    if ok and not parcial:
        console.print(Panel(
            f"[bold green]Limpeza concluída! Total liberado: {mb_total} MB[/bold green]",
            border_style="green"
        ))
        res_str = f"Limpeza integral com {mb_total} MB liberados"
    elif ok and parcial:
        console.print(Panel(
            f"[bold yellow]Limpeza concluída parcialmente! Total liberado: {mb_total} MB[/bold yellow]",
            border_style="yellow"
        ))
        res_str = f"Limpeza parcial com {mb_total} MB liberados"
    else:
        console.print(Panel(
            f"[bold red]Limpeza falhou ou foi cancelada![/bold red]",
            border_style="red"
        ))
        res_str = "Falha na limpeza ou cancelamento"

    if id_atendimento:
        from modules import logs
        logs.registrar_acao(id_atendimento, "Limpeza", res_str)

    return total_liberado_bytes


if __name__ == "__main__":
    executar_limpeza_completa()
