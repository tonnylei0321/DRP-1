# Claude Code Complete Setup Script (Windows PowerShell)
# This script sets up Claude Code with all plugins, MCP tools, and configurations
# Run this on a new machine to get a fully configured Claude Code environment

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($msg) Write-Host "[>] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[i] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[x] $msg" -ForegroundColor Red }
function Write-Ok { param($msg) Write-Host "[v] $msg" -ForegroundColor Green }

Write-Host "=================================================" -ForegroundColor Blue
Write-Host "  Claude Code Complete Setup (Windows)" -ForegroundColor Blue
Write-Host "  Multi-AI Collaboration + Plugins + MCP" -ForegroundColor Blue
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""

# Check prerequisites
Write-Step "Checking prerequisites..."

# Check Node.js
$nodeVersion = $null
try {
    $nodeVersion = (node --version 2>$null) -replace 'v', '' -split '\.' | Select-Object -First 1
    if ([int]$nodeVersion -ge 20) {
        Write-Ok "Node.js v$((node --version)) installed"
    } else {
        Write-Err "Node.js >= 20 required (current: $(node --version))"
        exit 1
    }
} catch {
    Write-Err "Node.js not found. Please install Node.js >= 20"
    exit 1
}

# Check Python
try {
    python --version 2>$null | Out-Null
    Write-Ok "Python installed"
} catch {
    Write-Info "Python not found (optional, some features may not work)"
}

# Check uv (for Codex MCP)
try {
    uvx --version 2>$null | Out-Null
    Write-Ok "uv installed"
} catch {
    Write-Info "uv not found. Please install from: https://astral.sh/uv"
}

Write-Host ""

# =================================================
# Step 0: Install AI CLI Tools
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 0: AI CLI Tools Installation" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check and install Claude Code
try {
    claude --version 2>$null | Out-Null
    Write-Ok "Claude Code installed"
} catch {
    Write-Info "Claude Code not found. Installing..."
    npm install -g @anthropic-ai/claude-code
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Claude Code installed"
    } else {
        Write-Err "Failed to install Claude Code"
        Write-Info "Manual install: npm install -g @anthropic-ai/claude-code"
        exit 1
    }
}

# Check and install Codex CLI
try {
    codex --version 2>$null | Out-Null
    Write-Ok "Codex CLI installed"
} catch {
    Write-Info "Codex CLI not found. Installing..."
    npm install -g @openai/codex 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Codex CLI installed"
    } else {
        Write-Err "Failed to install Codex CLI"
        Write-Info "Manual install: npm install -g @openai/codex"
    }
}

# Check and install Gemini CLI
try {
    gemini --version 2>$null | Out-Null
    Write-Ok "Gemini CLI installed"
} catch {
    Write-Info "Gemini CLI not found. Installing..."
    npm install -g @google/gemini-cli 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Ok "Gemini CLI installed"
    } else {
        Write-Err "Failed to install Gemini CLI"
        Write-Info "Manual install: npm install -g @google/gemini-cli"
    }
}

Write-Host ""

# =================================================
# Step 1: Global CLAUDE.md
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 1: Global CLAUDE.md" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClaudeDir = "$env:USERPROFILE\.claude"

Write-Step "Installing global CLAUDE.md..."

# Create .claude directory if not exists
if (-not (Test-Path $ClaudeDir)) {
    New-Item -ItemType Directory -Path $ClaudeDir -Force | Out-Null
}

if (Test-Path "$ClaudeDir\CLAUDE.md") {
    Write-Info "CLAUDE.md already exists. Backing up..."
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    Move-Item "$ClaudeDir\CLAUDE.md" "$ClaudeDir\CLAUDE.md.backup.$timestamp"
}

if (Test-Path "$ScriptDir\global") {
    if (Test-Path "$ScriptDir\global\CLAUDE.md") {
        Copy-Item "$ScriptDir\global\CLAUDE.md" "$ClaudeDir\CLAUDE.md"
        Write-Ok "Global CLAUDE.md installed"
    } else {
        Write-Info "No global/CLAUDE.md template found, skipping"
    }
} else {
    Write-Info "No global/ template directory found, skipping"
}

Write-Host ""

# Ensure marketplaces exist
Write-Step "Configuring plugin marketplaces..."

function Ensure-Marketplace {
    param(
        [Parameter(Mandatory = $true)][string]$marketplaceRepo
    )

    # marketplaceRepo 形如: "thedotmack/claude-mem" / "anthropics/claude-plugins-official" / "obra/superpowers-marketplace"
    $marketplaceId = ($marketplaceRepo -split "/")[0]

    # 1) 先 list，已存在直接跳过（把 "already installed" 当成 OK）
    $listOutput = & claude plugin marketplace list 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Could not list marketplaces"
        Write-Host $listOutput
        return
    }

    # list 输出里包含 marketplaceId 即认为已安装（例如 thedotmack / anthropics / obra）
    if ($listOutput -match "(^|\s)$([regex]::Escape($marketplaceId))(\s|$)") {
        Write-Ok "Marketplace already installed: $marketplaceId (skip)"
        return
    }

    # 2) 添加 marketplace（关键：try/catch，避免 claude.ps1 Write-Error 触发 Stop）
    Write-Info "Adding marketplace: $marketplaceRepo"

    $addOutput = $null
    $exitCode = $null

    try {
        $addOutput = & claude plugin marketplace add $marketplaceRepo 2>&1
        $exitCode = $LASTEXITCODE
    } catch {
        # 捕获 PowerShell 级别的终止错误（来自 claude.ps1 的 Write-Error）
        $addOutput = ($_ | Out-String)
        $exitCode = 1
    }

    # 统一把“already installed”当成功（无论是正常输出还是异常输出）
    if ($addOutput -match "already installed") {
        Write-Ok "Marketplace already installed: $marketplaceId (skip)"
        return
    }

    if ($exitCode -eq 0) {
        Write-Ok "Marketplace added: $marketplaceRepo"
        return
    }

    Write-Err "Failed to add marketplace: $marketplaceRepo"
    Write-Host $addOutput
}

Ensure-Marketplace "thedotmack/claude-mem"
Ensure-Marketplace "anthropics/claude-plugins-official"
Ensure-Marketplace "obra/superpowers-marketplace"

# =================================================
# Step 2: Plugins Installation
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 2: Plugins Installation" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "Installing Claude Code plugins..."
Write-Host ""
Write-Host "Available plugins:"
Write-Host "  1) claude-mem (Memory/History plugin)"
Write-Host "  2) superpowers (Enhanced capabilities with 13 skills)"
Write-Host "  3) pyright-lsp (Python LSP)"
Write-Host "  4) pinecone (Vector database for RAG)"
Write-Host "  5) commit-commands (Git commit helpers)"
Write-Host "  6) code-review (Code review helpers)"
Write-Host "  7) All of the above (Recommended)"
Write-Host ""

$pluginChoice = Read-Host "Select plugins to install (1-7, or comma-separated)"

# function Install-Plugin {
#     param($pluginName, $marketplace)
#     Write-Info "Installing $pluginName from $marketplace..."
#     try {
#         claude plugin install "${pluginName}@${marketplace}" 2>$null
#         Write-Ok "Installed: $pluginName"
#     } catch {
#         Write-Err "Failed to install: $pluginName"
#     }
# }

function Install-Plugin {
    param(
        [string]$pluginName,
        [string]$marketplace
    )

    $spec = "$pluginName@$marketplace"

    Write-Info "Installing plugin $spec ..."

    $output = & claude plugin install $spec 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Ok "Installed: $pluginName"
    } else {
        Write-Err "Failed to install: $pluginName"
        Write-Host $output
    }
}

switch ($pluginChoice) {
    "1" { Install-Plugin "claude-mem" "thedotmack" }
    "2" { Install-Plugin "superpowers" "superpowers-marketplace" }
    "3" { Install-Plugin "pyright-lsp" "claude-plugins-official" }
    "4" { Install-Plugin "pinecone" "claude-plugins-official" }
    "5" { Install-Plugin "commit-commands" "claude-plugins-official" }
    "6" { Install-Plugin "code-review" "claude-plugins-official" }
    default {
        Install-Plugin "claude-mem" "thedotmack"
        Install-Plugin "superpowers" "superpowers-marketplace"
        Install-Plugin "pyright-lsp" "claude-plugins-official"
        Install-Plugin "pinecone" "claude-plugins-official"
        Install-Plugin "commit-commands" "claude-plugins-official"
        Install-Plugin "code-review" "claude-plugins-official"
    }
}

Write-Host ""

# =================================================
# Step 3: MCP Tools Installation
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 3: MCP Tools (Multi-AI Collaboration)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "MCP enables Claude to call Codex and Gemini as tools"
Write-Host ""

# Codex MCP
$installCodex = Read-Host "Install Codex MCP? (y/n)"
if ($installCodex -eq "y" -or $installCodex -eq "Y") {
    Write-Info "Installing Codex MCP..."
    try {
        claude mcp remove codex 2>$null
    } catch {}
    try {
        claude mcp add codex -s user --transport stdio -- codex mcp-server
        Write-Ok "Codex MCP installed"
    } catch {
        Write-Err "Codex MCP installation failed"
        Write-Info "Manual install: claude mcp add codex -s user --transport stdio -- codex mcp-server"
    }
} else {
    Write-Info "Skipping Codex MCP"
}
Write-Host ""

# Gemini MCP
$installGemini = Read-Host "Install Gemini MCP? (y/n)"
if ($installGemini -eq "y" -or $installGemini -eq "Y") {
    Write-Info "Installing Gemini MCP..."
    try {
        claude mcp remove gemini-cli 2>$null
    } catch {}
    try {
        claude mcp add gemini-cli -- npx -y gemini-mcp-tool
        Write-Ok "Gemini MCP installed"
    } catch {
        Write-Err "Gemini MCP installation failed"
        Write-Info "Manual install: claude mcp add gemini-cli -- npx -y gemini-mcp-tool"
    }
} else {
    Write-Info "Skipping Gemini MCP"
}
Write-Host ""

# =================================================
# Step 4: Codex & Gemini Skills Sync
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 4: Codex & Gemini Skills Sync" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$CodexDir = "$env:USERPROFILE\.codex"
$GeminiDir = "$env:USERPROFILE\.gemini"

# Sync Codex Skills
try {
    codex --version 2>$null | Out-Null
    Write-Step "Syncing skills to Codex..."

    if (-not (Test-Path "$CodexDir\skills")) {
        New-Item -ItemType Directory -Path "$CodexDir\skills" -Force | Out-Null
    }

    if (Test-Path "$ScriptDir\global\codex-skills") {
        $skillCount = 0
        Get-ChildItem "$ScriptDir\global\codex-skills" -Directory | ForEach-Object {
            Copy-Item $_.FullName "$CodexDir\skills\" -Recurse -Force
            $skillCount++
        }
        Write-Ok "Synced $skillCount skills to Codex (superpowers)"
    } else {
        Write-Info "No Codex skills template found"
    }
} catch {
    Write-Info "Codex CLI not installed, skipping skills sync"
}
Write-Host ""

# Sync Gemini Config
try {
    gemini --version 2>$null | Out-Null
    Write-Step "Syncing config to Gemini..."

    if (-not (Test-Path $GeminiDir)) {
        New-Item -ItemType Directory -Path $GeminiDir -Force | Out-Null
    }

    if (Test-Path "$ScriptDir\global\GEMINI.md") {
        Copy-Item "$ScriptDir\global\GEMINI.md" "$GeminiDir\GEMINI.md"
        Write-Ok "Synced GEMINI.md from template"
    } else {
        Write-Info "No GEMINI.md template found, creating default..."
        @"
# Gemini CLI Configuration

## Role
You are Gemini, a large text analyst in a multi-AI collaboration system.

## Responsibilities
- Multi-document and long document analysis
- Large codebase pattern discovery
- Global view and pattern finding
- Frontend code development (your strength)

## Collaboration Rules
- Work with Claude (coordinator) and Codex (engineer)
- Provide analysis and insights, not final decisions
- Focus on patterns, summaries, and recommendations
"@ | Out-File "$GeminiDir\GEMINI.md" -Encoding UTF8
        Write-Ok "Created default GEMINI.md"
    }
} catch {
    Write-Info "Gemini CLI not installed, skipping config sync"
}
Write-Host ""

# =================================================
# Step 5: OpenSpec Installation
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 5: OpenSpec (SDD Workflow Tool)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "OpenSpec provides: Proposal -> Review -> Implement -> Archive workflow"
Write-Host ""
$installOpenspec = Read-Host "Install OpenSpec? (y/n)"

if ($installOpenspec -eq "y" -or $installOpenspec -eq "Y") {
    Write-Info "Installing OpenSpec globally..."
    try {
        npm install -g @fission-ai/openspec@latest
        Write-Ok "OpenSpec installed"
        Write-Info "Run 'openspec init' in your project to initialize"
    } catch {
        Write-Err "OpenSpec installation failed"
        Write-Info "Manual install: npm install -g @fission-ai/openspec@latest"
    }
} else {
    Write-Info "Skipping OpenSpec installation"
}
Write-Host ""

# =================================================
# Step 6: Global Hooks
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 6: Global Hooks" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "Installing global hooks..."

$hooksDir = "$ClaudeDir\hooks"
if (-not (Test-Path $hooksDir)) {
    New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
}

if (Test-Path "$ScriptDir\hooks") {
    Get-ChildItem "$ScriptDir\hooks\*.sh" -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName $hooksDir -Force
    }
    Get-ChildItem "$ScriptDir\hooks\*.ts" -ErrorAction SilentlyContinue | ForEach-Object {
        Copy-Item $_.FullName $hooksDir -Force
    }
    if (Test-Path "$ScriptDir\hooks\package.json") {
        Copy-Item "$ScriptDir\hooks\package.json" $hooksDir -Force

        # Install hook dependencies
        Push-Location $hooksDir
        try {
            npm install --silent 2>$null
        } catch {}
        Pop-Location
    }
    Write-Ok "Global hooks installed"
} else {
    Write-Info "No hooks template found, skipping"
}
Write-Host ""

# =================================================
# Step 7: Verification
# =================================================
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  Step 7: Verification" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

Write-Step "Verifying installation..."
Write-Host ""

# Check CLAUDE.md
if (Test-Path "$ClaudeDir\CLAUDE.md") {
    Write-Ok "Global CLAUDE.md exists"
} else {
    Write-Info "Global CLAUDE.md not found"
}

# Check plugins
Write-Step "Installed plugins:"
try {
    claude plugin list
} catch {
    Write-Info "Could not list plugins"
}
Write-Host ""

# Check MCP
Write-Step "MCP Status:"
try {
    claude mcp list
} catch {
    Write-Info "Could not list MCP tools"
}
Write-Host ""

# Check OpenSpec
try {
    openspec --version 2>$null | Out-Null
    Write-Ok "OpenSpec installed"
} catch {
    Write-Info "OpenSpec not installed"
}

# Check Codex skills
if (Test-Path "$CodexDir\skills") {
    $skillCount = (Get-ChildItem "$CodexDir\skills" -Directory).Count
    Write-Ok "Codex skills: $skillCount installed"
} else {
    Write-Info "Codex skills directory not found"
}

# Check Gemini config
if (Test-Path "$GeminiDir\GEMINI.md") {
    Write-Ok "Gemini GEMINI.md exists"
} else {
    Write-Info "Gemini GEMINI.md not found"
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Blue
Write-Host "[v] Global Setup Complete!" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""

# Next steps
Write-Step "Next Steps:"
Write-Host ""
Write-Host "1. Configure API keys (if needed):"
Write-Host "   - ANTHROPIC_API_KEY for Claude"
Write-Host "   - OPENAI_API_KEY for Codex"
Write-Host "   - GOOGLE_API_KEY for Gemini"
Write-Host ""
Write-Host "2. Deploy to a project:"
Write-Host "   .\setup-claude-config.ps1 C:\path\to\your\project"
Write-Host ""
Write-Host "3. Verify MCP tools work:"
Write-Host "   claude mcp list"
Write-Host ""
Write-Host "4. Test plugins:"
Write-Host "   claude plugin list"
Write-Host ""
Write-Host "Happy coding with Multi-AI Collaboration!" -ForegroundColor Green
