"""
Módulo de hardware (Fachada/Legado)

Mantém compatibilidade com a versão anterior exportando métodos
que internamente delegam para a nova arquitetura em `modules/core/hardware_*`.
"""

import threading
from modules.core import hardware_inventory
from modules.core import hardware_cache

# Para single-flight de rescan em background
_rescan_lock = threading.Lock()

def classificar_capacidade_hardware(hardware: dict) -> str:
    """
    Classifica o hardware em 'baixo', 'medio' ou 'alto'.
    Agora lida com os dados do inventário (v2).
    """
    pontos = 0
    
    # Se for formato antigo (tem 'ram' e 'gpus'), adapta
    cpu = hardware.get("cpu", {})
    if "nucleos_logicos" in cpu:
        # Formato antigo
        nucleos = cpu.get("nucleos_logicos") or 2
        ram_gb = hardware.get("ram", {}).get("total_gb", 0)
        tem_gpu_dedicada = any(
            g.get("vram_total_mb") and g["vram_total_mb"] >= 1024
            for g in hardware.get("gpus", [])
        )
    else:
        # Formato v2
        nucleos = cpu.get("threads_logicas") or 2
        ram_gb = hardware.get("memoria", {}).get("total_instalada_gb") or 0
        tem_gpu_dedicada = False
        for g in hardware.get("gpus", []):
            # Só considera dedicada se o status de confiabilidade permitir e for "dedicada"
            if g.get("tipo") == "dedicada" and g.get("vram_status") in ("exata", "estimada") and g.get("vram_total_mb", 0) >= 1024:
                tem_gpu_dedicada = True
                break

    if nucleos >= 8:
        pontos += 2
    elif nucleos >= 4:
        pontos += 1

    if ram_gb >= 16:
        pontos += 2
    elif ram_gb >= 8:
        pontos += 1

    if tem_gpu_dedicada:
        pontos += 1

    if pontos >= 4:
        return "alto"
    elif pontos >= 2:
        return "medio"
    else:
        return "baixo"


def obter_hardware_com_cache(forcar_rescan: bool = False, progress_callback=None) -> dict:
    """
    Tenta carregar o inventário do cache (hardware.json).
    Se for inválido ou forcar_rescan for True, refaz a varredura completa.
    Retorna SEMPRE o contrato v2.
    """
    if not forcar_rescan:
        cache = hardware_cache.carregar_cache_estatico()
        if cache:
            # Em background, sempre atualiza pelo menos 1 vez por sessão se quiser
            # (No plano, atualizamos no frontend via job)
            return cache

    # Faz o rescan
    return coletar_hardware_completo(progress_callback)


def coletar_hardware_completo(progress_callback=None) -> dict:
    """Delega para o novo coletor PowerShell/CIM e salva em cache."""
    # Garante que não haja dois scans ao mesmo tempo (single-flight em nível de hardware.py)
    with _rescan_lock:
        if progress_callback: progress_callback("Coletando inventário de hardware...")
        inventario = hardware_inventory.coletar_inventario()
        
        if progress_callback: progress_callback("Salvando cache...")
        hardware_cache.salvar_cache_estatico(inventario)
        
        if progress_callback: progress_callback("Finalizando...")
        return inventario


def forcar_rescan_hardware() -> dict:
    hardware_cache.deletar_cache()
    return obter_hardware_com_cache(forcar_rescan=True)


if __name__ == "__main__":
    import json
    hw = obter_hardware_com_cache(forcar_rescan=True)
    print(json.dumps(hw, indent=2, ensure_ascii=False))
    print("\nClassificação:", classificar_capacidade_hardware(hw))
