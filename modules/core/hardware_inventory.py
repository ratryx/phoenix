import json
import logging
import platform
import psutil
from datetime import datetime
from modules.core.windows_command import run_windows_command

logger = logging.getLogger(__name__)

# O script precisa rodar independentemente e tolerar falhas (SilentlyContinue)
# Discos precisam de permissão admin para Get-PhysicalDisk funcionar 100%, 
# mas Phoenix roda como admin então está garantido.
_PS_INVENTORY_SCRIPT = """
$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'

$cs = Get-CimInstance Win32_ComputerSystem
$os = Get-CimInstance Win32_OperatingSystem
$bb = Get-CimInstance Win32_BaseBoard
$bios = Get-CimInstance Win32_BIOS
$cpu = Get-CimInstance Win32_Processor
$mem = Get-CimInstance Win32_PhysicalMemory
$gpus = Get-CimInstance Win32_VideoController
$disks = Get-PhysicalDisk
$volumes = Get-Volume

# Helpers for objects that might be single or array
function Enumerate($obj) {
    if ($null -eq $obj) { return @() }
    if ($obj -is [array]) { return $obj }
    return @($obj)
}

$out = @{
    sistema = @{
        fabricante = $cs.Manufacturer
        modelo = $cs.Model
        nome_dispositivo = $cs.Name
        os_nome = $os.Caption
        os_versao = $os.Version
        os_build = $os.BuildNumber
        arquitetura = $os.OSArchitecture
        placa_mae = @{
            fabricante = $bb.Manufacturer
            modelo = $bb.Product
        }
        bios = @{
            fabricante = $bios.Manufacturer
            versao = $bios.SMBIOSBIOSVersion
        }
    }
    cpu = @{
        modelo = $cpu.Name
        fabricante = $cpu.Manufacturer
        nucleos_fisicos = $cpu.NumberOfCores
        threads_logicas = $cpu.NumberOfLogicalProcessors
        frequencia_max_mhz = $cpu.MaxClockSpeed
        arquitetura = $cpu.Architecture
    }
    memoria_modulos = @()
    gpus = @()
    discos_fisicos = @()
    volumes = @()
}

if ($bios.ReleaseDate) {
    try {
        $out.sistema.bios.data = $bios.ReleaseDate.ToString('yyyy-MM-dd')
    } catch {}
}

foreach ($m in Enumerate($mem)) {
    $out.memoria_modulos += @{
        slot = $m.DeviceLocator
        capacidade_bytes = $m.Capacity
        fabricante = $m.Manufacturer
        part_number = $m.PartNumber
        velocidade_mhz = $m.Speed
        velocidade_configurada_mhz = $m.ConfiguredClockSpeed
    }
}

foreach ($g in Enumerate($gpus)) {
    $out.gpus += @{
        id = $g.DeviceID
        nome = $g.Name
        fabricante = $g.AdapterCompatibility
        driver_versao = $g.DriverVersion
        driver_data = $g.DriverDate
        vram_bytes = $g.AdapterRAM
    }
}

foreach ($d in Enumerate($disks)) {
    $out.discos_fisicos += @{
        id = $d.DeviceId
        modelo = $d.FriendlyName
        tipo_midia = $d.MediaType
        barramento = $d.BusType
        capacidade_bytes = $d.Size
        saude = $d.HealthStatus
        status = $d.OperationalStatus
    }
}

foreach ($v in Enumerate($volumes)) {
    $out.volumes += @{
        unidade = $v.DriveLetter
        rotulo = $v.FileSystemLabel
        sistema_arquivos = $v.FileSystemType
        tipo = $v.DriveType
        total_bytes = $v.Size
        livre_bytes = $v.SizeRemaining
    }
}

$out | ConvertTo-Json -Depth 10 -Compress
"""

def _clean_string(val):
    if not isinstance(val, str):
        return val
    v = val.strip()
    if v.lower() in ("to be filled by o.e.m.", "default string", "desconhecido", "unknown"):
        return None
    return v if v else None

def _int_or_none(val):
    try:
        if val is None: return None
        v = int(val)
        return v if v >= 0 else None
    except (ValueError, TypeError):
        return None

def _bytes_to_gb(bytes_val):
    b = _int_or_none(bytes_val)
    if b is None: return None
    return round(b / (1024**3), 1)

def _bytes_to_mb(bytes_val):
    b = _int_or_none(bytes_val)
    if b is None: return None
    return round(b / (1024**2))

def coletar_inventario() -> dict:
    status = "completo"
    avisos = []
    
    # 1. Tentar coleta via PowerShell
    raw_data = None
    try:
        res = run_windows_command(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_INVENTORY_SCRIPT],
            operation_name="hardware_inventory_scan",
            timeout_seconds=15,
            max_output_chars=131072,
        )
        if res.ok and res.stdout:
            raw_data = json.loads(res.stdout)
    except Exception as e:
        logger.warning(f"Falha na coleta de inventário WMI/CIM: {e}")
        status = "parcial"
        avisos.append("Falha na coleta de inventário completo, usando fallback.")

    if raw_data is None:
        raw_data = {}
        status = "parcial"

    # 2. Construir modelo normalizado
    
    # Sistema
    sys_raw = raw_data.get("sistema", {})
    placa_mae = sys_raw.get("placa_mae", {})
    bios_raw = sys_raw.get("bios", {})
    
    sistema = {
        "fabricante": _clean_string(sys_raw.get("fabricante")),
        "modelo": _clean_string(sys_raw.get("modelo")),
        "nome_dispositivo": _clean_string(sys_raw.get("nome_dispositivo")) or platform.node(),
        "os_nome": _clean_string(sys_raw.get("os_nome")) or f"{platform.system()} {platform.release()}",
        "os_versao": _clean_string(sys_raw.get("os_versao")) or platform.version(),
        "os_build": _clean_string(sys_raw.get("os_build")),
        "arquitetura": _clean_string(sys_raw.get("arquitetura")) or platform.machine(),
        "placa_mae": {
            "fabricante": _clean_string(placa_mae.get("fabricante")),
            "modelo": _clean_string(placa_mae.get("modelo"))
        },
        "bios": {
            "fabricante": _clean_string(bios_raw.get("fabricante")),
            "versao": _clean_string(bios_raw.get("versao")),
            "data": _clean_string(bios_raw.get("data"))
        }
    }

    # CPU
    cpu_raw = raw_data.get("cpu", {})
    cpu_modelo = _clean_string(cpu_raw.get("modelo")) or platform.processor()
    cpu_cores = _int_or_none(cpu_raw.get("nucleos_fisicos")) or psutil.cpu_count(logical=False)
    cpu_threads = _int_or_none(cpu_raw.get("threads_logicas")) or psutil.cpu_count(logical=True)
    
    # Se ainda faltar frequência máxima, tente psutil
    freq_max = _int_or_none(cpu_raw.get("frequencia_max_mhz"))
    if not freq_max:
        try:
            freq = psutil.cpu_freq()
            freq_max = int(freq.max) if freq and freq.max else None
        except Exception:
            pass

    cpu = {
        "modelo": cpu_modelo,
        "fabricante": _clean_string(cpu_raw.get("fabricante")),
        "nucleos_fisicos": cpu_cores,
        "threads_logicas": cpu_threads,
        "frequencia_max_mhz": freq_max,
        "arquitetura": _clean_string(cpu_raw.get("arquitetura")) or platform.machine() # fallback para 32/64 bit cpu, mas no CIM ele da um numero
    }
    
    # Se architecture for int, não usar machine, mas CIM Win32_Processor Architecture:
    # 0=x86, 9=x64, 12=ARM
    if isinstance(cpu_raw.get("arquitetura"), int):
        arch_map = {0: "x86", 9: "x64", 12: "ARM64"}
        cpu["arquitetura"] = arch_map.get(cpu_raw["arquitetura"], cpu["arquitetura"])


    # Memória
    ps_mem = psutil.virtual_memory()
    modulos = []
    
    raw_modulos = raw_data.get("memoria_modulos", [])
    if isinstance(raw_modulos, dict): raw_modulos = [raw_modulos]
    
    for m in raw_modulos:
        modulos.append({
            "slot": _clean_string(m.get("slot")),
            "capacidade_gb": _bytes_to_gb(m.get("capacidade_bytes")),
            "fabricante": _clean_string(m.get("fabricante")),
            "part_number": _clean_string(m.get("part_number")),
            "velocidade_mhz": _int_or_none(m.get("velocidade_mhz")),
            "velocidade_configurada_mhz": _int_or_none(m.get("velocidade_configurada_mhz"))
        })

    total_installed = sum([m["capacidade_gb"] for m in modulos if m["capacidade_gb"]]) if modulos else None
    
    memoria = {
        "total_instalada_gb": total_installed or round(ps_mem.total / (1024**3), 1),
        "total_utilizavel_gb": round(ps_mem.total / (1024**3), 1),
        "slots_usados": len(modulos) if modulos else None,
        "slots_totais": None, # Complexo de extrair sem smbios, deixamos null
        "modulos": modulos
    }

    # GPUs
    gpus = []
    raw_gpus = raw_data.get("gpus", [])
    if isinstance(raw_gpus, dict): raw_gpus = [raw_gpus]
    
    # Detecção básica de GPU integrada vs dedicada.
    # Se o fabricante for Intel ou AMD e nome contiver "Graphics" / "Radeon(TM) Graphics", pode ser integrada.
    for i, g in enumerate(raw_gpus):
        nome = _clean_string(g.get("nome")) or "GPU desconhecida"
        fab = _clean_string(g.get("fabricante"))
        
        tipo = "desconhecida"
        nome_l = nome.lower()
        if "arc " in nome_l or "intel arc" in nome_l:
            tipo = "dedicada"
        elif "uhd" in nome_l or "iris" in nome_l or "hd graphics" in nome_l:
            tipo = "integrada"
        elif "intel" in nome_l:
            tipo = "integrada"
        elif "nvidia" in nome_l or "rtx" in nome_l or "gtx" in nome_l or "geforce" in nome_l:
            tipo = "dedicada"
        elif "rx " in nome_l or "radeon rx" in nome_l:
            tipo = "dedicada"
        elif "vega" in nome_l or "radeon(tm) graphics" in nome_l or "radeon graphics" in nome_l or "amd radeon" in nome_l or "radeon" in nome_l:
            tipo = "integrada"
            
        vram_b = _int_or_none(g.get("vram_bytes"))
        # VRAM from WMI is unreliable above 4GB because of 32-bit uint truncation.
        vram_mb = _bytes_to_mb(vram_b)
        
        vram_status = "indisponivel"
        if vram_mb:
            if vram_mb >= 4095 or vram_mb < 0: # Truncation issue
                vram_status = "estimada"
                vram_mb = None # Don't trust
            else:
                vram_status = "exata"

        gpus.append({
            "id": _clean_string(g.get("id")) or str(i),
            "nome": nome,
            "fabricante": fab,
            "tipo": tipo,
            "driver_versao": _clean_string(g.get("driver_versao")),
            "driver_data": _clean_string(g.get("driver_data")),
            "vram_total_mb": vram_mb,
            "vram_status": vram_status
        })

    # Armazenamento
    discos_fisicos = []
    raw_discos = raw_data.get("discos_fisicos", [])
    if isinstance(raw_discos, dict): raw_discos = [raw_discos]
    
    for d in raw_discos:
        midia = "desconhecido"
        # MediaType from PS: 3=HDD, 4=SSD, 5=SCM, 0=Unspecified
        mt = d.get("tipo_midia")
        if mt == 4: midia = "SSD"
        elif mt == 3: midia = "HDD"
        
        # Override based on bus type if NVMe (BusType 17)
        bt = d.get("barramento")
        bus_str = "desconhecido"
        if bt == 17:
            midia = "NVMe"
            bus_str = "NVMe"
        elif bt == 11: bus_str = "SATA"
        elif bt == 7: bus_str = "USB"
        elif bt == 8: bus_str = "RAID"

        discos_fisicos.append({
            "id": _clean_string(d.get("id")),
            "modelo": _clean_string(d.get("modelo")),
            "fabricante": None, # Not easily extracted in Get-PhysicalDisk
            "tipo_midia": midia,
            "barramento": bus_str,
            "capacidade_gb": _bytes_to_gb(d.get("capacidade_bytes")),
            "saude": _clean_string(d.get("saude")),
            "status": _clean_string(d.get("status"))
        })

    volumes = []
    raw_vols = raw_data.get("volumes", [])
    if isinstance(raw_vols, dict): raw_vols = [raw_vols]
    
    for v in raw_vols:
        drv_type = "desconhecido"
        dt = v.get("tipo")
        if dt == 3: drv_type = "fixo"
        elif dt == 2: drv_type = "removivel"
        elif dt == 4: drv_type = "rede"
        elif dt == 5: drv_type = "optico"

        tot_gb = _bytes_to_gb(v.get("total_bytes"))
        livre_gb = _bytes_to_gb(v.get("livre_bytes"))
        usado_gb = round(tot_gb - livre_gb, 1) if tot_gb and livre_gb else None
        
        pct = None
        if tot_gb and usado_gb is not None:
            pct = round((usado_gb / tot_gb) * 100, 1)

        unidade = _clean_string(v.get("unidade"))
        if not unidade: continue # Skip volumes sem letra mapeada
        
        volumes.append({
            "unidade": f"{unidade}:\\",
            "rotulo": _clean_string(v.get("rotulo")),
            "sistema_arquivos": _clean_string(v.get("sistema_arquivos")),
            "tipo": drv_type,
            "total_gb": tot_gb,
            "usado_gb": usado_gb,
            "livre_gb": livre_gb,
            "percentual_uso": pct
        })

    # Verifica capacidades dinâmicas (isso é preenchido depois no metrics ou só como flag)
    # GPU metrics support checking - try GPUtil
    has_gputil = False
    try:
        import GPUtil
        has_gputil = len(GPUtil.getGPUs()) > 0
    except ImportError:
        has_gputil = False
        
    capacidades = {
        "metricas_gpu_disponiveis": has_gputil,
        "temperatura_gpu_disponivel": has_gputil,
        "vram_gpu_disponivel": has_gputil
    }

    if status == "parcial" and not cpu.get("modelo"):
        status = "falhou"

    return {
        "schema_version": 2,
        "coletado_em": datetime.now().isoformat(),
        "status": status,
        "avisos": avisos,
        "sistema": sistema,
        "cpu": cpu,
        "memoria": memoria,
        "gpus": gpus,
        "armazenamento": {
            "discos_fisicos": discos_fisicos,
            "volumes": volumes
        },
        "capacidades": capacidades
    }
