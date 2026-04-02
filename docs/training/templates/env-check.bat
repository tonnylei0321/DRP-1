@echo off
chcp 65001 >nul 2>&1
REM =============================================================================
REM AI 驱动开发培训 - 环境自检脚本（Windows 版）
REM
REM 用法：双击运行 或 在 CMD/PowerShell 中执行 env-check.bat
REM 培训前一天运行，确保所有工具就绪。
REM =============================================================================

setlocal EnableDelayedExpansion

set PASS=0
set FAIL=0
set WARN=0

echo ============================================
echo   AI 驱动开发培训 - 环境自检（Windows）
echo ============================================
echo.

REM --- 1. 基础工具 ---
echo [1/8] 基础工具

git --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('git --version') do echo   [OK] %%v
    set /a PASS+=1
) else (
    echo   [FAIL] Git 未安装
    echo     修复方法：https://git-scm.com/download/win
    set /a FAIL+=1
)

node --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('node --version') do echo   [OK] Node.js %%v
    set /a PASS+=1
) else (
    echo   [WARN] Node.js 未安装（前端组需要）
    echo     安装：https://nodejs.org/
    set /a WARN+=1
)

python --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   [OK] %%v
    set /a PASS+=1
) else (
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%v in ('python3 --version 2^>^&1') do echo   [OK] %%v
        set /a PASS+=1
    ) else (
        echo   [WARN] Python 未安装（Python/算法组需要）
        echo     安装：https://www.python.org/downloads/
        set /a WARN+=1
    )
)

java --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('java --version 2^>^&1') do (
        echo   [OK] Java %%v
        goto :java_done
    )
) else (
    echo   [WARN] Java 未安装（Java 组需要）
    set /a WARN+=1
)
:java_done

mvn --version >nul 2>&1
if !errorlevel! equ 0 (
    echo   [OK] Maven 已安装
    set /a PASS+=1
) else (
    echo   [WARN] Maven 未安装（Java 组需要）
    set /a WARN+=1
)

echo.

REM --- 2. Claude Code ---
echo [2/8] Claude Code

claude --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('claude --version 2^>^&1') do echo   [OK] Claude Code: %%v
    set /a PASS+=1
) else (
    echo   [FAIL] Claude Code 未安装
    echo     修复方法：npm install -g @anthropic-ai/claude-code
    set /a FAIL+=1
)

echo.

REM --- 3. Codex CLI ---
echo [3/8] Codex CLI

codex --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('codex --version 2^>^&1') do echo   [OK] Codex: %%v
    set /a PASS+=1
) else (
    echo   [WARN] Codex CLI 未安装
    echo     修复方法：npm install -g @openai/codex
    set /a WARN+=1
)

echo.

REM --- 4. OpenSpec ---
echo [4/8] OpenSpec

openspec --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('openspec --version 2^>^&1') do echo   [OK] OpenSpec: %%v
    set /a PASS+=1
) else (
    echo   [WARN] OpenSpec 未安装
    echo     修复方法：npm install -g openspec-dev
    set /a WARN+=1
)

echo.

REM --- 5. API 连通性 ---
echo [5/8] API 连通性

if defined ANTHROPIC_API_KEY (
    echo   [OK] ANTHROPIC_API_KEY 已设置
    set /a PASS+=1
) else (
    echo   [WARN] ANTHROPIC_API_KEY 未设置（可能在 Claude Code 配置中）
    set /a WARN+=1
)

curl -s --connect-timeout 5 https://api.anthropic.com >nul 2>&1
if !errorlevel! equ 0 (
    echo   [OK] Anthropic API 网络可达
    set /a PASS+=1
) else (
    echo   [FAIL] Anthropic API 网络不可达
    echo     修复方法：检查代理设置，确保梯子已开启
    set /a FAIL+=1
)

echo.

REM --- 6. MCP 工具配置 ---
echo [6/8] MCP 工具配置

if exist "%USERPROFILE%\.claude" (
    echo   [OK] Claude 配置目录存在
    set /a PASS+=1
) else (
    echo   [WARN] Claude 配置目录不存在（首次启动 Claude Code 会自动创建）
    set /a WARN+=1
)

if exist "%USERPROFILE%\.claude.json" (
    echo   [OK] Claude 配置文件存在
    set /a PASS+=1
) else (
    echo   [WARN] Claude 配置文件不存在
    set /a WARN+=1
)

echo.

REM --- 7. 技术栈专项 ---
echo [7/8] 技术栈专项检查

pip --version >nul 2>&1
if !errorlevel! equ 0 (
    echo   [OK] pip 可用
    set /a PASS+=1

    python -c "import fastapi" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] FastAPI 已安装
        set /a PASS+=1
    ) else (
        echo   [WARN] FastAPI 未安装（Python 组需要: pip install fastapi）
        set /a WARN+=1
    )

    python -c "import pytest" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] pytest 已安装
        set /a PASS+=1
    ) else (
        echo   [WARN] pytest 未安装（pip install pytest）
        set /a WARN+=1
    )
) else (
    pip3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo   [OK] pip3 可用
        set /a PASS+=1
    )
)

npm --version >nul 2>&1
if !errorlevel! equ 0 (
    for /f "tokens=*" %%v in ('npm --version') do echo   [OK] npm %%v
    set /a PASS+=1
)

echo.

REM --- 8. 系统资源 ---
echo [8/8] 系统资源

for /f "tokens=3" %%a in ('dir /-c %SystemDrive%\ ^| findstr "bytes free"') do (
    set DISK_FREE=%%a
)
echo   [OK] 可用磁盘空间: !DISK_FREE! bytes
set /a PASS+=1

echo.

REM --- 汇总 ---
echo ============================================
echo   检查结果汇总
echo ============================================
echo   通过：!PASS!
echo   失败：!FAIL!
echo   警告：!WARN!
echo.

if !FAIL! equ 0 (
    echo   环境就绪！请在群里发送"环境检查通过"。
) else (
    echo   有 !FAIL! 项检查失败，请按提示修复后重新运行此脚本。
    echo   如需帮助，请联系培训助教。
)

echo.
pause
endlocal
