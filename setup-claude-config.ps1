# Claude Code Configuration Setup Script (Windows PowerShell)
# This script deploys Claude Code infrastructure to any project
# Including: Skills, Hooks, Agents, CLAUDE.md, OpenSpec, MCP (Codex/Gemini)

param(
    [string]$TargetDir = "."
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Step { param($msg) Write-Host "[>] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[i] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[x] $msg" -ForegroundColor Red }
function Write-Ok { param($msg) Write-Host "[v] $msg" -ForegroundColor Green }

# Configuration
$TemplateDir = "$env:USERPROFILE\.claude\config-templates"

Write-Host "=================================================" -ForegroundColor Blue
Write-Host "  Claude Code Configuration Setup (Windows)" -ForegroundColor Blue
Write-Host "  OpenSpec + Superpowers Unified Workflow" -ForegroundColor Blue
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""

# Check if template directory exists
if (-not (Test-Path $TemplateDir)) {
    Write-Err "Template directory not found: $TemplateDir"
    Write-Host "Please ensure config-templates is properly set up."
    exit 1
}

# Determine target directory
$TargetDir = (Resolve-Path $TargetDir).Path
Write-Info "Target directory: $TargetDir"
Write-Host ""

Push-Location $TargetDir

try {
    # Step 1: Create .claude directory
    Write-Step "Creating .claude directory structure..."
    $dirs = @(
        ".claude\skills",
        ".claude\hooks",
        ".claude\agents",
        ".claude\commands"
    )
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-Ok "Directory structure created"
    Write-Host ""

    # Step 2: Copy CLAUDE.md (Multi-AI Collaboration Rules)
    Write-Step "Installing CLAUDE.md (Multi-AI Collaboration Rules)..."
    if (Test-Path "CLAUDE.md") {
        Write-Info "CLAUDE.md already exists. Backing up..."
        Move-Item "CLAUDE.md" "CLAUDE.md.backup" -Force
    }
    Copy-Item "$TemplateDir\CLAUDE.md" ".\CLAUDE.md"
    Write-Ok "CLAUDE.md installed"
    Write-Host ""

    # Step 3: Copy hooks
    Write-Step "Installing skill activation hooks..."
    $hookFiles = @(
        "skill-activation-prompt.sh",
        "skill-activation-prompt.ts",
        "post-tool-use-tracker.sh",
        "package.json"
    )
    foreach ($hookFile in $hookFiles) {
        if (Test-Path "$TemplateDir\hooks\$hookFile") {
            Copy-Item "$TemplateDir\hooks\$hookFile" ".claude\hooks\" -Force
        }
    }
    Write-Ok "Hooks installed"
    Write-Host ""

    # Step 4: Install hook dependencies
    Write-Step "Installing hook dependencies..."
    if (Test-Path ".claude\hooks\package.json") {
        Push-Location ".claude\hooks"
        try {
            npm install --silent 2>$null
            Write-Ok "Dependencies installed"
        } catch {
            Write-Info "npm install skipped"
        }
        Pop-Location
    } else {
        Write-Info "No package.json found, skipping"
    }
    Write-Host ""

    # Step 5: Copy skills
    Write-Step "Installing skills..."
    Write-Host ""
    Write-Host "Available skills:"
    Write-Host "  1) git-workflow (Git Workflow Management)"
    Write-Host "  2) python-backend-guidelines (Python/Django/FastAPI)"
    Write-Host "  3) python-error-tracking (Sentry for Python)"
    Write-Host "  4) skill-developer (Create Custom Skills)"
    Write-Host "  5) openspec-workflow (OpenSpec Spec-Driven Workflow)"
    Write-Host "  6) All of the above (Recommended)"
    Write-Host ""

    $skillChoice = Read-Host "Select skills to install (1-6, or comma-separated e.g. 1,3,5)"

    function Install-Skill {
        param($skillName)
        $skillPath = "$TemplateDir\skills\$skillName"
        if (Test-Path $skillPath) {
            Copy-Item $skillPath ".claude\skills\" -Recurse -Force
            Write-Ok "Installed: $skillName"
        } else {
            Write-Info "Skill not found: $skillName"
        }
    }

    # 技能映射表
    $skillMap = @{
        "1" = "git-workflow"
        "2" = "python-backend-guidelines"
        "3" = "python-error-tracking"
        "4" = "skill-developer"
        "5" = "openspec-workflow"
    }

    if ($skillChoice -eq "6" -or [string]::IsNullOrWhiteSpace($skillChoice)) {
        foreach ($skill in $skillMap.Values) {
            Install-Skill $skill
        }
        Write-Ok "Installed: All skills"
    } else {
        $choices = $skillChoice -split ',' | ForEach-Object { $_.Trim() }
        foreach ($choice in $choices) {
            if ($skillMap.ContainsKey($choice)) {
                Install-Skill $skillMap[$choice]
            } else {
                Write-Info "Unknown choice: $choice"
            }
        }
    }

    # 清理已废弃的 dev-workflow 技能
    if (Test-Path ".claude\skills\dev-workflow") {
        Remove-Item ".claude\skills\dev-workflow" -Recurse -Force
        Write-Info "Removed deprecated skill: dev-workflow"
    }
    Write-Host ""

    # Step 6: Copy skill-rules.json
    Write-Step "Installing skill-rules.json..."
    if (Test-Path ".claude\skills\skill-rules.json") {
        Write-Info "skill-rules.json already exists. Backing up..."
        Move-Item ".claude\skills\skill-rules.json" ".claude\skills\skill-rules.json.backup" -Force
    }
    if (Test-Path "$TemplateDir\skills\skill-rules.json") {
        Copy-Item "$TemplateDir\skills\skill-rules.json" ".claude\skills\"
        Write-Ok "skill-rules.json installed"
    } else {
        Write-Info "No skill-rules.json template found"
    }
    Write-Host ""

    # Step 7: Copy agents
    Write-Step "Installing agents..."
    $installAgents = Read-Host "Install all agents? (y/n)"
    if ($installAgents -eq "y" -or $installAgents -eq "Y") {
        if (Test-Path "$TemplateDir\agents") {
            Get-ChildItem "$TemplateDir\agents\*.md" -ErrorAction SilentlyContinue | ForEach-Object {
                Copy-Item $_.FullName ".claude\agents\" -Force
            }
            $agentCount = (Get-ChildItem ".claude\agents\*.md" -ErrorAction SilentlyContinue).Count
            Write-Ok "Installed $agentCount agents"
        }
    } else {
        Write-Info "Skipping agents installation"
    }
    Write-Host ""

    # Step 8: Create or update settings.json
    Write-Step "Configuring settings.json..."
    if (Test-Path ".claude\settings.json") {
        Write-Info "settings.json already exists. Manual merge required."
        Copy-Item "$TemplateDir\settings.json" ".claude\settings.json.template" -Force
        Write-Info "Template saved as .claude\settings.json.template"
    } else {
        if (Test-Path "$TemplateDir\settings.json") {
            Copy-Item "$TemplateDir\settings.json" ".claude\settings.json"
            Write-Ok "settings.json created"
        }
    }
    Write-Host ""

    # Step 9: OpenSpec Installation
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "  OpenSpec (Spec-Driven Workflow Tool)" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Step "OpenSpec provides: Proposal -> Review -> Implement -> Archive workflow"
    Write-Host ""
    $installOpenspec = Read-Host "Install OpenSpec? (y/n)"

    if ($installOpenspec -eq "y" -or $installOpenspec -eq "Y") {
        # Check Node.js version
        try {
            $nodeVersion = (node --version) -replace 'v', '' -split '\.' | Select-Object -First 1
            if ([int]$nodeVersion -ge 20) {
                Write-Info "Installing OpenSpec globally..."
                npm install -g @fission-ai/openspec@latest
                if ($LASTEXITCODE -eq 0) {
                    Write-Ok "OpenSpec installed"

                    # Auto-initialize OpenSpec in project
                    Write-Info "Initializing OpenSpec in project..."
                    try {
                        openspec init --tools claude
                        Write-Ok "OpenSpec initialized (openspec/ directory created)"

                        # Copy project.md template if exists
                        if (Test-Path "$TemplateDir\openspec\project.md") {
                            Copy-Item "$TemplateDir\openspec\project.md" "openspec\project.md" -Force
                            Write-Ok "OpenSpec project.md template installed"
                        }

                        # Create specs directory structure
                        if (-not (Test-Path "openspec\specs")) {
                            New-Item -ItemType Directory -Path "openspec\specs" -Force | Out-Null
                        }
                        if (-not (Test-Path "openspec\changes")) {
                            New-Item -ItemType Directory -Path "openspec\changes" -Force | Out-Null
                        }
                        Write-Ok "OpenSpec directory structure created"
                    } catch {
                        Write-Info "OpenSpec init requires manual setup: openspec init"
                    }
                } else {
                    Write-Err "OpenSpec installation failed"
                }
            } else {
                Write-Err "Node.js >= 20 required (current: $(node --version))"
            }
        } catch {
            Write-Err "Node.js not found. Please install Node.js >= 20"
        }
    } else {
        Write-Info "Skipping OpenSpec installation"
        Write-Info "You can install later: npm install -g @fission-ai/openspec@latest"
    }
    Write-Host ""

    # Step 10: MCP Tools Installation
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host "  MCP Tools (Multi-AI Collaboration)" -ForegroundColor Cyan
    Write-Host "=================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Step "MCP enables Claude to call Codex and Gemini as tools"
    Write-Host ""

    $installMcp = Read-Host "Install MCP tools (Codex + Gemini)? (y/n)"
    if ($installMcp -eq "y" -or $installMcp -eq "Y") {
        # Method 1: Copy .mcp.json template (recommended)
        if (Test-Path "$TemplateDir\.mcp.json") {
            Write-Info "Installing MCP configuration via .mcp.json..."
            if (Test-Path ".mcp.json") {
                Write-Info ".mcp.json already exists. Backing up..."
                Move-Item ".mcp.json" ".mcp.json.backup" -Force
            }
            Copy-Item "$TemplateDir\.mcp.json" ".\.mcp.json"
            Write-Ok "MCP configuration installed (.mcp.json)"
            Write-Info "Included: codex (Codex CLI), gemini-cli (Gemini)"
        } else {
            # Method 2: Fallback to claude mcp add commands
            Write-Info "No .mcp.json template found, using claude mcp add..."
            try {
                claude --version 2>$null | Out-Null

                # Codex MCP
                Write-Info "Installing Codex MCP..."
                try { claude mcp remove codex -s project 2>$null } catch {}
                try {
                    claude mcp add codex -s project -- uvx --from "git+https://github.com/GuDaStudio/codexmcp.git" codexmcp
                    Write-Ok "Codex MCP installed"
                } catch {
                    Write-Err "Codex MCP installation failed"
                }

                # Gemini MCP
                Write-Info "Installing Gemini MCP..."
                try { claude mcp remove gemini-cli -s project 2>$null } catch {}
                try {
                    claude mcp add gemini-cli -s project -- npx -y gemini-mcp-tool
                    Write-Ok "Gemini MCP installed"
                } catch {
                    Write-Err "Gemini MCP installation failed"
                }
            } catch {
                Write-Err "Claude CLI not found. Please install Claude Code first."
                Write-Info "Manual install:"
                Write-Info "  claude mcp add codex -s project -- uvx --from git+https://github.com/GuDaStudio/codexmcp.git codexmcp"
                Write-Info "  claude mcp add gemini-cli -s project -- npx -y gemini-mcp-tool"
            }
        }
    } else {
        Write-Info "Skipping MCP tools installation"
    }
    Write-Host ""

    # Step 11: Verification
    Write-Step "Verifying installation..."
    Write-Host ""

    $dirsOk = $true

    # Check JSON validity
    try {
        python --version 2>$null | Out-Null
        if (Test-Path ".claude\skills\skill-rules.json") {
            $json = Get-Content ".claude\skills\skill-rules.json" -Raw | ConvertFrom-Json
            Write-Ok "skill-rules.json is valid JSON"
        }
        if (Test-Path ".claude\settings.json") {
            $json = Get-Content ".claude\settings.json" -Raw | ConvertFrom-Json
            Write-Ok "settings.json is valid JSON"
        }
    } catch {
        Write-Info "JSON validation skipped or failed"
    }

    # Check directory structure
    $checkDirs = @(".claude\skills", ".claude\hooks")
    foreach ($dir in $checkDirs) {
        if (Test-Path $dir) {
            Write-Ok "$dir exists"
        } else {
            Write-Err "$dir missing"
            $dirsOk = $false
        }
    }

    # Check CLAUDE.md
    if (Test-Path "CLAUDE.md") {
        Write-Ok "CLAUDE.md exists"
    } else {
        Write-Err "CLAUDE.md missing"
        $dirsOk = $false
    }

    # Check MCP
    try {
        claude --version 2>$null | Out-Null
        Write-Host ""
        Write-Step "MCP Status:"
        claude mcp list
    } catch {
        Write-Info "Could not list MCP tools"
    }

    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Blue
    if ($dirsOk) {
        Write-Host "[v] Installation Complete!" -ForegroundColor Green
    } else {
        Write-Host "[!] Installation completed with warnings" -ForegroundColor Yellow
    }
    Write-Host "=================================================" -ForegroundColor Blue
    Write-Host ""

    # Next steps
    Write-Step "Next Steps:"
    Write-Host ""
    Write-Host "1. Review and customize CLAUDE.md for your project"
    Write-Host "2. Customize .claude\skills\skill-rules.json for your project paths"
    Write-Host "3. Initialize OpenSpec (if installed):"
    Write-Host "   openspec init"
    Write-Host "4. Verify MCP tools:"
    Write-Host "   claude mcp list"
    Write-Host "5. Test Multi-AI collaboration:"
    Write-Host "   - Ask Claude to call Codex for code review"
    Write-Host "   - Ask Claude to call Gemini for large text analysis"
    Write-Host ""
    Write-Host "Documentation:"
    Write-Host "  - CLAUDE.md: Multi-AI collaboration rules"
    Write-Host "  - Skills: dir .claude\skills\*\SKILL.md"
    Write-Host "  - Agents: dir .claude\agents\*.md"
    Write-Host ""
    Write-Host "Happy coding with Multi-AI Collaboration!" -ForegroundColor Green

} finally {
    Pop-Location
}
