[CmdletBinding()]
param(
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [ValidateRange(1, 65535)]
    [int]$Port = 3000,
    [string]$NodePath
)

$ErrorActionPreference = "Stop"

$frontendRoot = $PSScriptRoot
$viteScript = Join-Path $frontendRoot "node_modules\vite\bin\vite.js"
if (-not (Test-Path -LiteralPath $viteScript)) {
    throw "Не найден Vite. Выполните npm install в $frontendRoot."
}

if (-not $NodePath) {
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeCommand) {
        $NodePath = $nodeCommand.Source
    }
}

if (-not $NodePath) {
    # Этот fallback доступен в локальной среде Codex и нужен, когда Node/npm
    # не добавлены в системный PATH.
    $codexNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    if (Test-Path -LiteralPath $codexNode) {
        $NodePath = $codexNode
    }
}

if (-not $NodePath -or -not (Test-Path -LiteralPath $NodePath)) {
    throw "Node.js не найден. Установите Node.js 18+ или передайте -NodePath 'C:\путь\к\node.exe'."
}

$env:VITE_API_URL = $ApiUrl
Write-Host "Запускаю Course Brief UI на http://127.0.0.1:$Port/create"
& $NodePath $viteScript --host 127.0.0.1 --port $Port --strictPort
