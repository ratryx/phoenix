# Data Model and State Transitions: Windows GUI Validation

Purely infrastructural feature; no persistent business entities are added. However, we track the application's runtime execution state and environment detection.

## Application Execution State

### Execution Mode State Machine

The launcher determines the execution path based on the presence of a parent console and command-line arguments.

```mermaid
stateDiagram-v2
    [*] --> DetectEnvironment : App Start
    DetectEnvironment --> TryAttachConsole : Windows OS
    DetectEnvironment --> StandardLaunch : Linux/macOS OS
    
    TryAttachConsole --> Attached : AttachConsole() Success
    TryAttachConsole --> Headless : AttachConsole() Fails (Double-click)
    
    StandardLaunch --> PromptModeSelection
    
    Attached --> CLI_Forced : CLI argument passed (e.g., --cli)
    Attached --> GUI_Forced : GUI argument passed (e.g., --gui)
    Attached --> PromptModeSelection : No argument
    
    Headless --> StartGUI : Default fallback
    
    PromptModeSelection --> StartCLI : Selected "1" (CLI)
    PromptModeSelection --> StartGUI : Selected "2" (GUI)
    PromptModeSelection --> Exit : Selected "0" (Exit)
    
    StartCLI --> [*]
    StartGUI --> [*]
    Exit --> [*]
```

### State Fields

We represent the runtime context using the following parameters:

| Variable | Type | Description |
| :--- | :--- | :--- |
| `has_parent_console` | `bool` | True if successfully attached to parent terminal via `AttachConsole`. |
| `selected_mode` | `str` | `"CLI"`, `"GUI"`, or `"EXIT"`. |
| `hw_info` | `dict` | Hardware information dictionary collected via `modules.hardware`. |
