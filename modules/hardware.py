"""
Módulo de detecção de hardware: coleta informações detalhadas de CPU, RAM
e GPU (incluindo modelo, fabricante, VRAM, uso e temperatura quando suportado).

Usado tanto pelo launcher (para recomendar modo CLI ou GUI) quanto pelo
diagnóstico completo do programa (para mostrar ao cliente o hardware real).
"""

import platform
import psutil
import concurrent.futures

try:
    import wmi
except ImportError:
    wmi = None

try:
    import GPUtil
except ImportError:
    GPUtil = None


def coletar_cpu_info() -> dict:
    nome_cpu = platform.processor()
    
    # Tenta WMI com timeout de 3 segundos
    def _wmi_cpu():
        w = wmi.WMI()
        return w.Win32_Processor()[0].Name.strip()
    
    if platform.system() == "Windows" and wmi is not None:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(_wmi_cpu)
                nome_detectado = future.result(timeout=3)
                if nome_detectado:
                    nome_cpu = nome_detectado
        except Exception:
            pass  # timeout ou erro → usa platform.processor()
    
    freq = psutil.cpu_freq()
    return {
        "modelo": nome_cpu,
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "frequencia_atual_mhz": round(freq.current, 0) if freq else None,
        "frequencia_max_mhz": round(freq.max, 0) if freq and freq.max else None,
        "uso_percentual": psutil.cpu_percent(interval=0.1),
    }


def coletar_ram_info() -> dict:
    """Coleta informações de memória RAM."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 1),
        "disponivel_gb": round(mem.available / (1024 ** 3), 1),
        "percentual_uso": round(mem.percent, 1),
    }


def _consultar_gpu_wmi() -> list:
    if not wmi:
        return []
    
    def _wmi_gpu():
        w = wmi.WMI()
        gpus = []
        for placa in w.Win32_VideoController():
            ram_bytes = placa.AdapterRAM
            try:
                ram_bytes = int(ram_bytes) if ram_bytes else None
            except:
                ram_bytes = None
            vram_mb = round(ram_bytes / (1024 ** 2)) if ram_bytes and ram_bytes > 0 else None
            gpus.append({
                "nome": placa.Name or "GPU desconhecida",
                "fabricante": placa.AdapterCompatibility or "Desconhecido",
                "vram_total_mb": vram_mb,
                "driver_versao": placa.DriverVersion
            })
        return gpus
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_wmi_gpu)
            return future.result(timeout=3)
    except Exception:
        return []

def _consultar_gpu_gputil() -> list:
    """Consulta NVIDIA GPUs usando GPUtil."""
    if not GPUtil:
        return []
    try:
        placas = GPUtil.getGPUs()
        gpus = []
        for placa in placas:
            gpus.append({
                "nome": placa.name,
                "vram_total_mb": int(placa.memoryTotal),
                "vram_usada_mb": int(placa.memoryUsed),
                "uso_percentual": int(placa.load * 100),
                "temperatura_c": int(placa.temperature),
            })
        return gpus
    except Exception:
        return []

def coletar_gpu_info() -> list:
    """
    Coleta informações de todas as GPUs detectadas no sistema,
    usando GPUtil como primário e WMI como fallback estático.
    """
    gpus_resultado = []
    
    # Primário: NVIDIA via GPUtil
    gpus_nvidia = _consultar_gpu_gputil()
    nomes_nvidia = {g["nome"] for g in gpus_nvidia}
    
    for gpu in gpus_nvidia:
        gpus_resultado.append({
            "nome": gpu["nome"],
            "fabricante": "NVIDIA",
            "vram_total_mb": gpu["vram_total_mb"],
            "vram_usada_mb": gpu["vram_usada_mb"],
            "uso_percentual": gpu["uso_percentual"],
            "temperatura_c": gpu["temperatura_c"],
            "fonte_dados": "GPUtil (tempo real)",
        })
        
    # Fallback: Todas as GPUs via WMI
    gpus_wmi = _consultar_gpu_wmi()
    for gpu in gpus_wmi:
        if gpu["nome"] in nomes_nvidia:
            continue
            
        gpus_resultado.append({
            "nome": gpu["nome"],
            "fabricante": gpu["fabricante"],
            "vram_total_mb": gpu["vram_total_mb"],
            "vram_usada_mb": None,
            "uso_percentual": None,
            "temperatura_c": None,
            "driver_versao": gpu.get("driver_versao"),
            "fonte_dados": "WMI (sem dados em tempo real)",
        })
        
    return gpus_resultado


def coletar_hardware_completo(progress_callback=None) -> dict:
    """Coleta CPU, RAM e GPU em uma única estrutura, usada pelo launcher e pelo diagnóstico."""
    
    if progress_callback: progress_callback("Coletando CPU...")
    cpu = coletar_cpu_info()
    
    if progress_callback: progress_callback("Coletando RAM...")
    ram = coletar_ram_info()
    
    if progress_callback: progress_callback("Coletando GPU...")
    gpus = coletar_gpu_info()
    
    if progress_callback: progress_callback("Finalizando...")
    return {
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "cpu": cpu,
        "ram": ram,
        "gpus": gpus,
    }


def classificar_capacidade_hardware(hardware: dict) -> str:
    """
    Classifica o hardware em 'baixo', 'medio' ou 'alto' com base em
    núcleos de CPU, RAM total e presença de GPU dedicada.
    Usado pelo launcher para recomendar CLI ou GUI automaticamente.
    """
    pontos = 0

    nucleos = hardware["cpu"]["nucleos_logicos"] or 2
    ram_gb = hardware["ram"]["total_gb"]
    tem_gpu_dedicada = any(
        g.get("vram_total_mb") and g["vram_total_mb"] >= 1024
        for g in hardware["gpus"]
    )

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


def obter_validacao_rapida() -> dict:
    """
    Retorna métricas super rápidas para validar se o hardware mudou
    desde o último cache (usado pela Feature 011).
    Evita chamadas lentas WMI se possível.
    """
    cpu = platform.processor()
    if not cpu or cpu.isspace():
        cpu = "Desconhecido"
    
    mem = psutil.virtual_memory()
    ram_gb = round(mem.total / (1024 ** 3), 1)

    return {
        "cpu_modelo": cpu,
        "ram_total_gb": ram_gb
    }


def obter_hardware_com_cache(forcar_rescan: bool = False, progress_callback=None) -> dict:
    """
    Tenta carregar o hardware do cache (hardware.json).
    Se o cache for inválido, expirado (30 dias) ou forcar_rescan for True,
    refaz a varredura completa e atualiza o cache.
    """
    import os
    import json
    from datetime import datetime
    from modules.shared import CACHE_DIR
    
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "hardware.json"
    
    if not forcar_rescan and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                
            # Se o cache existir, retorna imediatamente e lança thread para validar/atualizar
            if "dados" in cache_data:
                import threading
                def _background_update():
                    try:
                        validacao_atual = obter_validacao_rapida()
                        validacao_cache = cache_data.get("validacao", {})
                        
                        data_scan = datetime.fromisoformat(cache_data.get("data_scan", "2000-01-01T00:00:00"))
                        dias_passados = (datetime.now() - data_scan).days
                        
                        if dias_passados >= 30 or validacao_atual["cpu_modelo"] != validacao_cache.get("cpu_modelo") or abs(validacao_atual["ram_total_gb"] - validacao_cache.get("ram_total_gb", 0)) >= 1.0:
                            forcar_rescan_hardware()
                        else:
                            pass
                    except Exception:
                        pass
                
                threading.Thread(target=_background_update, daemon=True).start()
                return cache_data["dados"]
        except Exception:
            pass # Se o cache estiver corrompido, ignora e refaz

    # Refaz scan
    dados_completos = coletar_hardware_completo(progress_callback=progress_callback)
    validacao = obter_validacao_rapida()
    
    # Prepara objeto de cache
    novo_cache = {
        "data_scan": datetime.now().isoformat(),
        "validacao": validacao,
        "dados": dados_completos
    }
    
    # Salva cache de forma silenciosa
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(novo_cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
        
    return dados_completos

def forcar_rescan_hardware() -> dict:
    """Força um rescan completo do hardware, deletando o cache existente."""
    from modules.shared import CACHE_DIR
    cache_file = CACHE_DIR / "hardware.json"
    try:
        if cache_file.exists():
            cache_file.unlink()
    except Exception:
        pass
    
    return obter_hardware_com_cache(forcar_rescan=True)


if __name__ == "__main__":
    import json
    hw = obter_hardware_com_cache()
    print(json.dumps(hw, indent=2, ensure_ascii=False))
    print("\nClassificação:", classificar_capacidade_hardware(hw))
