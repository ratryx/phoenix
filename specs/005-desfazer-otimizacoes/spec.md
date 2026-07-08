# Feature Specification: Desfazer Otimizações Aplicadas

**Feature Branch**: `005-desfazer-otimizacoes`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Antes de cada otimização, salvar o estado atual em JSON em %PROGRAMDATA%\PhoenixOptimizer\snapshots\. Cada otimização nasce com sua função de reversão correspondente. Interface deve mostrar quais otimizações foram aplicadas e permitir reverter individualmente ou todas de uma vez. Se o snapshot não existir, desabilitar o botão de reversão para aquela otimização."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criação e Detecção do Snapshot (Priority: P1)

Como usuário do Phoenix Optimizer, quero que o sistema crie um arquivo de "foto" (snapshot) do estado atual do meu Windows antes de aplicar qualquer otimização específica, para que as minhas chaves de registro e estados de serviços originais fiquem salvos em segurança localmente.

**Why this priority**: Fundamental para garantir que qualquer modificação feita pelo software possa ser desfeita, respeitando o Princípio I (Cirúrgico e Não Destrutivo).

**Independent Test**: Ativar uma otimização (ex: desativar telemetria) e inspecionar a pasta `%PROGRAMDATA%\PhoenixOptimizer\snapshots\` para verificar se o respectivo arquivo JSON foi gerado com os valores anteriores à otimização.

**Acceptance Scenarios**:

1. **Given** que o usuário iniciou o processo de aplicação de uma otimização, **When** o script é chamado, **Then** o sistema deve ler os valores de registro ou serviços atuais, salvá-los em formato JSON na pasta `%PROGRAMDATA%\PhoenixOptimizer\snapshots\` com identificação clara e, só então, modificar as configurações do Windows.

---

### User Story 2 - Reversão Individual e Coletiva das Alterações (Priority: P1)

Como usuário do Phoenix Optimizer, quero ver uma lista das otimizações que já foram aplicadas e poder escolher se desejo reverter apenas uma otimização específica ou todas as otimizações aplicadas de uma só vez, para ter controle flexível sobre o estado do meu sistema.

**Why this priority**: Fornece flexibilidade e controle total ao usuário, evitando que ele precise desfazer tudo se apenas uma configuração específica causou problemas em seus programas cotidianos.

**Independent Test**: Aplicar duas otimizações diferentes, clicar no botão de reversão de apenas uma delas e verificar se apenas os valores daquela otimização específica retornaram ao original de fábrica, mantendo a outra ativa. Em seguida, testar o botão "Reverter Tudo" e confirmar a restauração total do sistema.

**Acceptance Scenarios**:

1. **Given** uma lista de otimizações aplicadas, **When** o usuário aciona a reversão de uma única otimização, **Then** o sistema deve carregar o snapshot correspondente, executar a função de reversão específica e alterar o status daquela otimização para "Disponível para Otimizar".
2. **Given** múltiplas otimizações aplicadas, **When** o usuário aciona a reversão total ("Reverter Tudo"), **Then** o sistema deve aplicar sequencialmente a reversão de todas as otimizações listadas na pasta de snapshots e limpar os snapshots processados de forma segura.

---

### User Story 3 - Proteção de Reversão Indisponível (Priority: P2)

Como usuário do Phoenix Optimizer, quero que o botão de reversão de uma otimização seja desabilitado se o snapshot correspondente não for encontrado no computador, para evitar falhas ou estados inconsistentes por tentar restaurar algo que não tem backup.

**Why this priority**: Evita erros silenciosos de runtime ou quebras de interface ao tentar ler arquivos inexistentes (por exemplo, se o usuário rodou um limpador de disco ou excluiu a pasta manualmente).

**Independent Test**: Apagar manualmente o arquivo JSON de snapshot de uma otimização aplicada e verificar se a interface atualiza o respectivo botão de reversão para o estado desabilitado (cinza e não clicável).

**Acceptance Scenarios**:

1. **Given** uma otimização que foi marcada como aplicada, **When** o arquivo JSON de snapshot correspondente sob `%PROGRAMDATA%\PhoenixOptimizer\snapshots\` estiver ausente ou corrompido, **Then** o sistema deve desabilitar o botão ou opção de reversão daquela otimização na interface (GUI e CLI) e informar ao usuário que o backup não foi localizado.

---

### Edge Cases

- **Modificação Manual Externa das Configurações**: Se o usuário otimizou com o Phoenix, depois alterou manualmente as chaves pelo Regedit do Windows e por fim clicou em reverter: o sistema deve simplesmente reinserir os valores salvos no snapshot JSON original, garantindo o retorno ao estado seguro anterior ao uso do Phoenix.
- **Snapshot Corrompido ou JSON Inválido**: Caso o arquivo de snapshot esteja corrompido (JSON corrompido por desligamento súbito do PC), a aplicação deve detectar a falha de decodificação de dados, mover o arquivo corrompido para uma pasta de quarentena/logs, desabilitar o botão de reversão e sugerir o uso do Ponto de Restauração do Windows (Feature 002) como fallback de emergência.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST salvar o estado de configuração pré-otimização em um arquivo JSON no diretório `%PROGRAMDATA%\PhoenixOptimizer\snapshots\` antes de aplicar as mudanças.
- **FR-002**: Cada otimização adicionada ao ecossistema do Phoenix Optimizer MUST possuir um par funcional contendo a lógica de aplicação e a lógica correspondente de reversão.
- **FR-003**: A interface MUST renderizar a lista de otimizações e mostrar dinamicamente o status (Ex: "Não Aplicado", "Otimizado", "Snapshot Ausente").
- **FR-004**: O sistema MUST verificar a presença física do arquivo de snapshot correspondente antes de habilitar a funcionalidade de reversão (individual ou bulk) para aquela otimização.
- **FR-005**: Ao clicar em "Reverter Tudo", o sistema MUST processar todos os snapshots válidos disponíveis e redefinir o estado de cada otimização restaurada.
- **FR-006**: A lógica de gravação de snapshot, leitura e restauração MUST rodar nos módulos compartilhados do core (CLI e GUI).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reversão de qualquer otimização individual é concluída em menos de 3 segundos após o clique, informando o resultado na tela.
- **SC-002**: 100% das chaves de registro restauradas recuperam o tipo de dados exato (ex: DWORD, String) e o valor original capturados no snapshot.
- **SC-003**: O botão de reversão é desabilitado instantaneamente na inicialização da tela caso o arquivo correspondente na pasta de snapshots não exista.

## Assumptions

- O aplicativo tem permissão de escrita e leitura na pasta `%PROGRAMDATA%\PhoenixOptimizer\snapshots\`.
- Cada otimização tem um identificador único de string (ex: `disable_telemetry`, `optimize_ntfs`) usado como nome do arquivo de snapshot (ex: `disable_telemetry.json`).
