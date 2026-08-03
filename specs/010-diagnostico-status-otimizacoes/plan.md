# Implementation Plan: Diagnóstico de Status das Otimizações & Cache de Hardware (010 & 011)

**Branch**: `010-diagnostico-status-otimizacoes` | **Date**: 2026-07-08 | **Spec**: [spec.md](file:///c:/Users/Thiago/Desktop/phoenix-optimizer/specs/010-diagnostico-status-otimizacoes/spec.md)

**Input**: Feature specification from `/specs/010-diagnostico-status-otimizacoes/spec.md` and `/specs/011-cache-hardware/spec.md`

## Summary

Este plano aborda a implementação simultânea de duas funcionalidades críticas (010 e 011), considerando a dependência arquitetural da feature 012 (Redesign GUI + Spinner Job ID).

- **010**: Verificação em tempo real do status das otimizações aplicadas, consultando o Windows diretamente (Registro, Serviços, PowerShell), com opções de reaplicação individual ou em lote.
- **011**: Implementação de cache de hardware em JSON (`%PROGRAMDATA%\PhoenixOptimizer\cache\hardware.json`) com invalidação automática baseada em mudanças chave (CPU, RAM, GPU) ou decurso de tempo (30 dias).

## Technical Context

**Language/Version**: Python 3.12+

**Primary Dependencies**: `psutil`, `wmi`, `subprocess` (built-in), `pywebview`

**Storage**: Arquivo local JSON em `%PROGRAMDATA%\PhoenixOptimizer\cache\hardware.json`

**Testing**: Validação manual na GUI e CLI em ambiente Windows. Testes de integridade via mock de respostas do PowerShell.

**Target Platform**: Windows 10/11 (Desktop)

**Project Type**: Desktop Application (Dual-Interface CLI/GUI)

**Performance Goals**: 
- Abertura da ferramenta com cache: < 1s
- Verificação do status de otimizações: < 10s
- Reaplicação de otimização: < 5s
- Nenhuma operação pode bloquear a thread principal da GUI.

**Constraints**: Timeout de 5s máximo para consultas ao Windows; Obrigatório uso de `job_id` + `polling` (Feature 012) para tarefas demoradas.

**Scale/Scope**: Limitado ao ambiente local do usuário.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Cirúrgico e Não Destrutivo** [OK] (Consultas são apenas leitura, reaplicação já segue métodos validados).
- **Principle II: Ponto de Restauração Obrigatório** [OK] (A reaplicação chamará a rotina de backup/rollback implementada).
- **Principle III: Controle de Serviços Fixos** [OK] (Validação manter-se-á restrita a `SERVICOS_SEGUROS`).
- **Principle IV: Isolamento de Logs** [OK] (Cache será armazenado em `%PROGRAMDATA%\PhoenixOptimizer\cache\`, seguindo o padrão).
- **Principle V: Transparência de Performance** [OK] (Não promete ganhos adicionais).
- **Principle VI: Dual-Interface CLI/GUI** [OK] (Lógica será encapsulada em `modules/` e exposta para ambas).
- **Principle VII: Validação de Empacotamento** [OK] (Será validado pós-implementação).

## Project Structure

### Documentation (this feature)

```text
specs/010-diagnostico-status-otimizacoes/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
└── quickstart.md        # Phase 1 output
```

### Source Code (repository root)

```text
src/
├── modules/
│   ├── hardware.py         # Será alterado para suportar Cache (011) e Validação Rápida
│   ├── otimizacao.py       # Será alterado para suportar Verificação de Status (010)
│   ├── cli_app.py          # Integração das novas opções
│   └── gui_app.py          # Exposição das novas APIs e suporte ao padrão job_id (012)
└── ...
```

**Structure Decision**: A lógica será adicionada aos módulos existentes (`hardware.py` e `otimizacao.py`), mantendo a separação entre CLI e GUI, com o `gui_app.py` sendo preparado para o padrão `job_id`.
