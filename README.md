# Phoenix Optimizer V2.0

Ferramenta completa de diagnóstico, limpeza, otimização e relatório de
performance para Windows 10/11 — com dois modos de uso (CLI leve e GUI
completa), ambos compartilhando exatamente a mesma lógica de negócio.

---

## O que mudou na v2

- **Dois modos de execução**: o programa detecta o hardware automaticamente
  e recomenda Modo CLI (terminal, leve) ou Modo GUI (interface gráfica
  completa, com efeitos visuais adaptativos).
- **Visual do CLI reformulado**: a estética anterior (fogo vermelho intenso)
  foi substituída por uma paleta dourada/âmbar mais sóbria e corporativa,
  após feedback de que o visual antigo remetia a ferramentas maliciosas.
- **Detecção de hardware expandida**: além de CPU/RAM, agora detecta GPU
  (modelo, fabricante, VRAM, uso e temperatura quando suportado).
- **GUI nova**: interface em HTML/CSS/JS renderizada via `pywebview`
  (usa o WebView2 já instalado no Windows — não embute um navegador
  completo como o Electron, mantendo o programa leve).
- **Qualidade visual adaptativa**: a GUI ajusta automaticamente a
  intensidade de efeitos (glassmorphism, partículas) com base na
  capacidade do hardware detectado.

---

## Arquitetura

```
phoenix-optimizer/
├── launcher.py                 # ponto de entrada — detecta hardware, escolhe modo
├── modules/
│   ├── banner.py                # identidade visual do CLI (paleta corporativa)
│   ├── cli_app.py                # menu interativo do Modo CLI
│   ├── gui_app.py                 # backend do Modo GUI (ponte Python <-> JS)
│   ├── hardware.py                 # detecção de CPU, RAM e GPU
│   ├── diagnostico.py               # CPU, RAM, disco, processos (uso/sessão)
│   ├── limpeza.py                    # limpeza de temp/cache/lixeira
│   ├── otimizacao.py                  # performance geral + FPS + disco
│   ├── servicos.py                     # gerenciamento de serviços do Windows
│   ├── logs.py                          # histórico de atendimentos
│   └── relatorio.py                      # relatório comparativo antes/depois
├── gui/
│   ├── index.html                        # estrutura da interface gráfica
│   ├── style.css                          # tema visual (glassmorphism, cores)
│   └── app.js                              # lógica de navegação e chamadas à API
├── assets/
│   └── phoenix.ico                          # ícone do executável
├── phoenix_setup.iss                         # script do instalador (Inno Setup)
├── phoenix.spec                               # build do PyInstaller
└── requirements.txt
```

**Importante sobre a arquitetura**: tanto `cli_app.py` quanto `gui_app.py`
chamam exatamente as mesmas funções dos módulos de negócio (`diagnostico`,
`limpeza`, `otimizacao`, `servicos`, `logs`, `relatorio`). Nenhuma lógica
foi duplicada entre os dois modos — apenas a forma de exibir e interagir
com os resultados é diferente.

---

## Como rodar em modo desenvolvimento

```
pip install -r requirements.txt
python launcher.py
```

O launcher vai detectar seu hardware, mostrar uma recomendação, e perguntar
se você quer o Modo CLI ou o Modo GUI.

---

## Gerar o executável (.exe)

```
pip install pyinstaller
pyinstaller phoenix.spec
```

O executável aparece em `dist\PhoenixOptimizer.exe`. Ele já inclui:
- As fontes do `pyfiglet` (necessárias para o banner do CLI)
- A pasta `gui/` completa (HTML/CSS/JS), embutida dentro do `.exe`
- O ícone da fênix

> **Sobre a janela de console**: como o `.exe` precisa suportar tanto o
> Modo CLI (que roda em terminal) quanto o Modo GUI, o build mantém
> `console=True`. Isso significa que, mesmo escolhendo o Modo GUI, uma
> janela de terminal permanece aberta por trás da janela gráfica. Isso é
> uma limitação inerente de unificar os dois modos num único executável
> — não afeta o funcionamento, mas é visualmente menos "limpo" que um
> app puramente gráfico. Se isso for um problema no futuro, a solução é
> dividir em dois executáveis separados (um console, um windowed).

> **Importante**: como o programa altera registro e serviços do Windows,
> execute como administrador (botão direito no `.exe` → "Executar como
> administrador").

---

## Gerar o instalador (Inno Setup)

1. Baixe e instale o Inno Setup: https://jrsoftware.org/isdl.php
2. Abra `phoenix_setup.iss` no Inno Setup Compiler.
3. Compile (`F9`).
4. O instalador final aparece em `output\PhoenixOptimizer_Setup_1.0.0.exe`.

---

## Funcionalidades (idênticas em ambos os modos)

| Função | Descrição |
|--------|-----------|
| Diagnóstico completo | CPU, RAM, disco, processos mais pesados |
| Hardware detalhado | Modelo de CPU/GPU, VRAM, uso e temperatura de GPU |
| Limpeza | Temp, prefetch, Windows Update, WER, cache de navegadores, dumps, lixeira, DNS |
| Otimização geral | Plano de energia, efeitos visuais, apps em segundo plano |
| Otimização para jogos | Modo de Jogo, overlay do Game Bar, GPU scheduling, reset de rede |
| Gerenciar serviços | Ativa/desativa serviços não essenciais do Windows |
| Otimizar disco | TRIM (SSD) ou desfragmentação (HDD), automático |
| Histórico | Lista todos os atendimentos já realizados |
| Rotina completa | Diagnóstico → limpeza → otimização → diagnóstico final → relatório comparativo |

Os logs de cada atendimento ficam em `%PROGRAMDATA%\PhoenixOptimizer\logs`
— local sempre gravável, independente de onde o programa for instalado.

---

## Sobre o ganho de FPS (expectativa realista)

As otimizações de jogos (Modo de Jogo, overlay desativado, GPU scheduling,
plano de energia) tipicamente geram ganhos de **0% a 10%** de FPS,
dependendo do hardware e do que estava rodando antes. Driver de GPU
desatualizado, configurações in-game e hardware (CPU/GPU/SSD) têm impacto
muito maior no FPS do que qualquer ajuste de sistema. Evite prometer
números fixos de ganho ao cliente — a ferramenta otimiza o sistema, não
substitui hardware ou configuração de jogo.

---

## Próximos passos sugeridos

- Detecção de driver de GPU desatualizado (com link de download oficial)
- Ponto de restauração automático antes de aplicar otimizações
- Verificação de saúde do disco (S.M.A.R.T.)
- Opção de desfazer otimizações aplicadas
- Licenciamento/chave de ativação por cliente, se for vender como produto
