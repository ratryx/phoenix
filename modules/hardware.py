"""
Módulo de detecção de hardware: coleta informações detalhadas de CPU, RAM
e GPU (incluindo modelo, fabricante, VRAM, uso e temperatura quando suportado).

Usado tanto pelo launcher (para recomendar modo CLI ou GUI) quanto pelo
diagnóstico completo do programa (para mostrar ao cliente o hardware real).
"""

import platform
import subprocess
import psutil


def coletar_cpu_info() -> dict:
    """Coleta informações detalhadas da CPU, incluindo o modelo do processador."""
    nome_cpu = platform.processor()

    # No Windows, platform.processor() às vezes retorna algo genérico.
    # Tentamos pegar o nome real via PowerShell/WMI quando possível.
    if platform.system() == "Windows":
        try:
            resultado = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_Processor).Name"],
                capture_output=True, text=True, timeout=10
            )
            nome_detectado = resultado.stdout.strip()
            if nome_detectado:
                nome_cpu = nome_detectado
        except Exception:
            pass

    freq = psutil.cpu_freq()

    return {
        "modelo": nome_cpu,
        "nucleos_fisicos": psutil.cpu_count(logical=False),
        "nucleos_logicos": psutil.cpu_count(logical=True),
        "frequencia_atual_mhz": round(freq.current, 0) if freq else None,
        "frequencia_max_mhz": round(freq.max, 0) if freq and freq.max else None,
        "uso_percentual": psutil.cpu_percent(interval=0.5),
    }


def coletar_ram_info() -> dict:
    """Coleta informações de memória RAM."""
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 1),
        "disponivel_gb": round(mem.available / (1024 ** 3), 1),
        "percentual_uso": round(mem.percent, 1),
    }


def _consultar_gpu_powershell() -> list:
    """
    Consulta informações básicas de GPU via WMI (funciona para qualquer
    fabricante — NVIDIA, AMD, Intel — mas não traz uso/temperatura em tempo
    real, que são específicos de cada driver).
    """
    comando_ps = (
        "Get-CimInstance Win32_VideoController | "
        "Select-Object Name, AdapterRAM, DriverVersion, AdapterCompatibility | "
        "ConvertTo-Json"
    )
    try:
        resultado = subprocess.run(
            ["powershell", "-Command", comando_ps],
            capture_output=True, text=True, timeout=15
        )
        import json
        saida = resultado.stdout.strip()
        if not saida:
            return []
        dados = json.loads(saida)
        if isinstance(dados, dict):
            dados = [dados]
        return dados
    except Exception:
        return []


def _consultar_gpu_nvidia_smi() -> list:
    """
    Consulta informações detalhadas de GPUs NVIDIA via nvidia-smi
    (uso real, temperatura, VRAM usada/total). Só funciona se o driver
    NVIDIA estiver instalado — outras marcas não têm esse utilitário.
    """
    try:
        resultado = subprocess.run(
            ["nvidia-smi",
             "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10
        )
        if resultado.returncode != 0:
            return []

        gpus = []
        for linha in resultado.stdout.strip().split("\n"):
            partes = [p.strip() for p in linha.split(",")]
            if len(partes) == 5:
                gpus.append({
                    "nome": partes[0],
                    "vram_total_mb": int(partes[1]),
                    "vram_usada_mb": int(partes[2]),
                    "uso_percentual": int(partes[3]),
                    "temperatura_c": int(partes[4]),
                })
        return gpus
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        return []


def coletar_gpu_info() -> list:
    """
    Coleta informações de todas as GPUs detectadas no sistema.

    Estratégia em duas camadas:
    1. nvidia-smi (se existir) — dá dados completos e em tempo real, mas só para NVIDIA.
    2. WMI via PowerShell — funciona para qualquer fabricante (NVIDIA, AMD, Intel),
       mas só traz nome, VRAM declarada e versão do driver (sem uso/temperatura).

    O resultado combina as duas fontes: GPUs NVIDIA aparecem com dados completos,
    outras GPUs aparecem com os dados básicos disponíveis.
    """
    gpus_resultado = []

    gpus_nvidia = _consultar_gpu_nvidia_smi()
    nomes_nvidia_detectados = {g["nome"] for g in gpus_nvidia}

    for gpu in gpus_nvidia:
        gpus_resultado.append({
            "nome": gpu["nome"],
            "fabricante": "NVIDIA",
            "vram_total_mb": gpu["vram_total_mb"],
            "vram_usada_mb": gpu["vram_usada_mb"],
            "uso_percentual": gpu["uso_percentual"],
            "temperatura_c": gpu["temperatura_c"],
            "fonte_dados": "nvidia-smi (tempo real)",
        })

    gpus_wmi = _consultar_gpu_powershell()
    for gpu in gpus_wmi:
        nome = gpu.get("Name", "GPU desconhecida")

        # Evita duplicar GPUs NVIDIA já capturadas com dados completos via nvidia-smi
        if nome in nomes_nvidia_detectados:
            continue

        ram_bytes = gpu.get("AdapterRAM")
        vram_mb = round(ram_bytes / (1024 ** 2)) if ram_bytes and ram_bytes > 0 else None

        fabricante = gpu.get("AdapterCompatibility", "Desconhecido")

        gpus_resultado.append({
            "nome": nome,
            "fabricante": fabricante,
            "vram_total_mb": vram_mb,
            "vram_usada_mb": None,
            "uso_percentual": None,
            "temperatura_c": None,
            "driver_versao": gpu.get("DriverVersion"),
            "fonte_dados": "WMI (sem dados em tempo real)",
        })

    return gpus_resultado


def coletar_hardware_completo() -> dict:
    """Coleta CPU, RAM e GPU em uma única estrutura, usada pelo launcher e pelo diagnóstico."""
    return {
        "sistema_operacional": f"{platform.system()} {platform.release()}",
        "cpu": coletar_cpu_info(),
        "ram": coletar_ram_info(),
        "gpus": coletar_gpu_info(),
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


if __name__ == "__main__":
    import json
    hw = coletar_hardware_completo()
    print(json.dumps(hw, indent=2, ensure_ascii=False))
    print("\nClassificação:", classificar_capacidade_hardware(hw))
