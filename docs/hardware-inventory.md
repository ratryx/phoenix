# Phoenix Optimizer - Subsistema de Hardware (v2)

O subsistema de hardware foi completamente reescrito para fornecer informações altamente precisas, seguras (isoladas) e padronizadas.

## Separação de Responsabilidades

1. **`hardware_inventory.py`**: Responsável *exclusivamente* por consultar o WMI/CIM do Windows para montar o inventário físico estático da máquina. 
2. **`hardware_metrics.py`**: Responsável *exclusivamente* por obter as métricas em tempo real (CPU, RAM, Disco e GPU). Adiciona suporte stateful ao monitoramento de Disco (I/O rate) que o PSUtil nativamente não suporta facilmente.
3. **`hardware_cache.py`**: Responsável por persistir o inventário no disco (`hardware.json`). Aplica proteção contra vazamento de métricas dinâmicas para o cache e gerencia a concorrência.
4. **`hardware_service.py`**: Serviço stateful na camada da aplicação (GUI) que mantém o inventário carregado na memória, e gerencia o lifecycle (uptime real).

## Contrato de Dados (Inventário - `hardware.json` e `obter_inventario_atual`)

O inventário retornado agora é fortemente estruturado.

```json
{
  "schema_version": 2,
  "status": "completo | parcial | falhou",
  "coletado_em": "ISO-8601",
  "capacidades": {
    "metricas_gpu_disponiveis": true
  },
  "sistema": {
    "fabricante": "...",
    "modelo": "...",
    "nome_dispositivo": "...",
    "os_nome": "Microsoft Windows 11 Pro",
    "os_versao": "10.0.26100",
    "os_build": "26100",
    "arquitetura": "64 bits",
    "placa_mae": { "fabricante": "...", "modelo": "..." },
    "bios": { "fabricante": "...", "versao": "...", "data": "2023-01-01" }
  },
  "cpu": {
    "modelo": "AMD Ryzen...",
    "fabricante": "AuthenticAMD",
    "nucleos_fisicos": 8,
    "threads_logicas": 16,
    "frequencia_max_mhz": 4000,
    "arquitetura": "x64"
  },
  "memoria": {
    "total_instalada_gb": 32.0,
    "total_utilizavel_gb": 31.8,
    "slots_usados": 2,
    "modulos": [
      {
        "slot": "DIMM 0",
        "capacidade_gb": 16.0,
        "fabricante": "Samsung",
        "velocidade_mhz": 6400,
        "part_number": "..."
      }
    ]
  },
  "gpus": [
    {
      "nome": "AMD Radeon(TM) Graphics",
      "fabricante": "Advanced Micro Devices",
      "tipo": "integrada | dedicada | desconhecida",
      "vram_total_mb": 512,
      "vram_status": "exata | estimada | desconhecida",
      "driver_versao": "...",
      "driver_data": "..."
    }
  ],
  "armazenamento": {
    "discos_fisicos": [
      {
        "modelo": "NVMe WD...",
        "tipo_midia": "NVMe",
        "barramento": "NVMe",
        "capacidade_gb": 1024.2,
        "saude": "Healthy"
      }
    ],
    "volumes": [
      {
        "unidade": "C:\\",
        "rotulo": "Windows",
        "tipo": "Local Disk",
        "sistema_arquivos": "NTFS",
        "total_gb": 931.5,
        "livre_gb": 120.0,
        "percentual_uso": 87.1
      }
    ]
  }
}
```

## Tratamento de Falhas e Tipos

- **Memória VRAM Acima de 4GB**: WMI usa UInt32, o que causa overflow/truncamento em placas com mais de 4GB. Se a placa for `dedicada` mas reportar um número distorcido (ex: 4294967295 bytes), a propriedade `vram_status` será marcada como `estimada` e o valor poderá ser substituído ou omitido.
- **Detecção Integrada/Dedicada**: A determinação do `tipo` de GPU é feita inspecionando o nome do dispositivo e características da VRAM, sendo robusta para placas Intel, AMD (incluindo nomenclaturas legadas) e NVIDIA.
- **Cache Seguro**: Modificações feitas via WMI demoram e causam pequenos travamentos em interfaces. Por isso, usamos o cache. O cache *somente* suporta a `schema_version = 2` e abortará/limpará se houver qualquer tentativa de salvar as propriedades `uso_percentual` ou `temperatura_c` (evitando poluição do state com dados antigos ou voláteis).
