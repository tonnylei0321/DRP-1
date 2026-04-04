# DRP 前端拆分：管理后台 + 监管大屏

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 DRP 前端拆分为两个独立入口：管理后台（5173）和监管大屏（5174），共享 API client 和组件库。

**Architecture:** Vite + React SPA，监管大屏独立为 `frontend/dashboard/` 子目录（独立 vite.config.ts），管理后台在 `frontend/` 根目录。共享 API client 和组件库。

**Tech Stack:** Vite 8, React 19, TypeScript, 现有 Dashboard.tsx / D3Graphs.tsx / GeoMap.tsx 组件复用。

---

## 文件变更总览

| 操作 | 文件 |
|------|------|
| 创建 | `frontend/dashboard/` 目录（独立部署） |
| 创建 | `frontend/dashboard/index.html` |
| 创建 | `frontend/dashboard/main.tsx` |
| 创建 | `frontend/dashboard/vite.config.ts` |
| 创建 | `frontend/src/DashboardApp.tsx` |
| 创建 | `frontend/src/dashboard/LoginPanel.tsx` |
| 创建 | `frontend/src/dashboard/StatusBar.tsx` |
| 修改 | `frontend/package.json`（添加 dev:dashboard / build:dashboard） |
| 修改 | `frontend/index.html`（添加 `data-app="admin"`） |
| 修改 | `scripts/restart.sh`（同时启动两个前端） |
| 创建 | `frontend/src/dashboard-main.tsx` |
| 创建 | `frontend/src/DashboardApp.tsx` |
| 创建 | `frontend/src/dashboard/StatusBar.tsx` |
| 创建 | `frontend/src/dashboard/LoginPanel.tsx` |
| 修改 | `scripts/restart.sh` |

---

## Task 1: 修改 vite.config.ts 为 multi-page 配置

**Files:**
- Modify: `frontend/vite.config.ts`

**Steps:**

- [ ] **Step 1: 重写 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
      },
    },
  },
})
```

Run: `cat frontend/vite.config.ts | grep -A5 rollupOptions`
Expected: `input:` with main and dashboard keys

---

## Task 2: 创建 dashboard.html 入口文件

**Files:**
- Create: `frontend/dashboard.html`

**Steps:**

- [ ] **Step 1: 创建 dashboard.html**

```html
<!doctype html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DRP 监管大屏</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;600&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/dashboard-main.tsx"></script>
  </body>
</html>
```

Run: `grep "监管大屏" frontend/dashboard.html`
Expected: `<title>DRP 监管大屏</title>`

---

## Task 3: 创建 dashboard-main.tsx 入口脚本

**Files:**
- Create: `frontend/src/dashboard-main.tsx`

**Steps:**

- [ ] **Step 1: 创建 dashboard-main.tsx**

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import DashboardApp from './DashboardApp'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <DashboardApp />
  </StrictMode>,
)
```

Run: `grep "DashboardApp" frontend/src/dashboard-main.tsx`
Expected: `import DashboardApp from './DashboardApp'`

---

## Task 4: 创建 LoginPanel.tsx 大屏登录页

**Files:**
- Create: `frontend/src/dashboard/LoginPanel.tsx`

**Steps:**

- [ ] **Step 1: 创建 LoginPanel.tsx**

```typescript
import { useState } from 'react'
import { authApi, setToken } from '../api/client'

interface Props {
  onLogin: () => void
}

export default function LoginPanel({ onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(email, password)
      setToken(res.access_token)
      onLogin()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg.includes('401') ? '邮箱或密码不正确' : '登录失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--cyber-bg, #020810)',
      fontFamily: 'var(--font-label, Barlow Condensed, sans-serif)',
    }}>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16, width: 320 }}>
        <div style={{ textAlign: 'center', marginBottom: 12 }}>
          <div style={{ fontFamily: 'var(--font-hud)', fontSize: 28, fontWeight: 900, color: 'var(--accent, #00d8ff)', letterSpacing: '0.2em', textShadow: '0 0 30px var(--accent, #00d8ff)' }}>DRP</div>
          <div style={{ fontFamily: 'var(--font-label)', fontSize: 12, color: 'rgba(150,190,220,0.6)', letterSpacing: '0.15em', marginTop: 4 }}>监管大屏 · 穿透式资金监管平台</div>
        </div>

        <input
          type="email"
          placeholder="邮箱"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          style={{ padding: '10px 14px', background: 'rgba(0,216,255,0.05)', border: '1px solid rgba(0,216,255,0.2)', borderRadius: 4, color: '#c8dff0', fontSize: 14, outline: 'none', fontFamily: 'inherit' }}
        />

        <input
          type="password"
          placeholder="密码"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          style={{ padding: '10px 14px', background: 'rgba(0,216,255,0.05)', border: '1px solid rgba(0,216,255,0.2)', borderRadius: 4, color: '#c8dff0', fontSize: 14, outline: 'none', fontFamily: 'inherit' }}
        />

        {error && (
          <div style={{ color: '#ff2020', fontSize: 12, textAlign: 'center', fontFamily: 'var(--font-mono)' }}>{error}</div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{ padding: '10px', background: loading ? 'rgba(0,216,255,0.3)' : 'rgba(0,216,255,0.15)', border: '1px solid rgba(0,216,255,0.4)', borderRadius: 4, color: '#00d8ff', fontSize: 14, cursor: loading ? 'not-allowed' : 'pointer', fontFamily: 'inherit', letterSpacing: '0.1em' }}
        >
          {loading ? '登录中...' : '进入大屏'}
        </button>
      </form>
    </div>
  )
}
```

Run: `grep "LoginPanel" frontend/src/dashboard/LoginPanel.tsx`
Expected: `export default function LoginPanel`

---

## Task 5: 创建 StatusBar.tsx 极简顶栏

**Files:**
- Create: `frontend/src/dashboard/StatusBar.tsx`

**Steps:**

- [ ] **Step 1: 创建 StatusBar.tsx**

```typescript
import { useState } from 'react'
import { getToken, clearToken } from '../api/client'

interface Props {
  lastUpdate: Date | null
  onRefresh: () => void
  autoRefreshInterval: number  // 0 = 关闭
  onAutoRefreshChange: (interval: number) => void
  onLogout: () => void
}

const REFRESH_OPTIONS = [
  { label: '15s', value: 15000 },
  { label: '30s', value: 30000 },
  { label: '60s', value: 60000 },
  { label: '关闭', value: 0 },
]

export default function StatusBar({ lastUpdate, onRefresh, autoRefreshInterval, onAutoRefreshChange, onLogout }: Props) {
  const [showAutoMenu, setShowAutoMenu] = useState(false)

  const currentLabel = REFRESH_OPTIONS.find(o => o.value === autoRefreshInterval)?.label ?? '30s'

  return (
    <div style={{
      height: 40, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 16px',
      background: 'rgba(2,8,16,0.97)',
      borderBottom: '1px solid rgba(0,216,255,0.18)',
      fontFamily: 'var(--font-label, Barlow Condensed, sans-serif)',
      flexShrink: 0,
    }}>
      {/* 左侧：标题 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ fontFamily: 'var(--font-hud)', fontSize: 14, fontWeight: 700, color: '#00d8ff', letterSpacing: '0.15em', textShadow: '0 0 12px #00d8ff' }}>DRP 监管看板</span>
      </div>

      {/* 右侧：状态 + 控制 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, fontSize: 11 }}>
        {/* 最后更新时间 */}
        <span style={{ color: 'rgba(150,190,220,0.5)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
          {lastUpdate ? `更新: ${lastUpdate.toLocaleTimeString('zh-CN', { hour12: false })}` : '等待数据...'}
        </span>

        {/* 自动刷新选择 */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowAutoMenu(!showAutoMenu)}
            style={{ background: 'none', border: '1px solid rgba(0,216,255,0.3)', borderRadius: 3, color: '#00d8ff', padding: '3px 8px', cursor: 'pointer', fontSize: 10, fontFamily: 'inherit', letterSpacing: '0.08em' }}
          >
            🔄 自动刷新({currentLabel})
          </button>
          {showAutoMenu && (
            <div style={{
              position: 'absolute', top: '100%', right: 0, marginTop: 4,
              background: 'rgba(2,8,16,0.98)', border: '1px solid rgba(0,216,255,0.3)',
              borderRadius: 4, zIndex: 100, minWidth: 100,
            }}>
              {REFRESH_OPTIONS.map(opt => (
                <div
                  key={opt.value}
                  onClick={() => { onAutoRefreshChange(opt.value); setShowAutoMenu(false) }}
                  style={{
                    padding: '6px 12px', cursor: 'pointer', fontSize: 11,
                    color: autoRefreshInterval === opt.value ? '#00d8ff' : 'rgba(150,190,220,0.7)',
                    background: autoRefreshInterval === opt.value ? 'rgba(0,216,255,0.1)' : 'transparent',
                    fontFamily: 'inherit',
                  }}
                >
                  {opt.label}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 手动刷新按钮 */}
        <button
          onClick={onRefresh}
          style={{ background: 'none', border: '1px solid rgba(0,216,255,0.3)', borderRadius: 3, color: '#00d8ff', padding: '3px 8px', cursor: 'pointer', fontSize: 10, fontFamily: 'inherit', letterSpacing: '0.08em' }}
        >
          🔄 刷新
        </button>

        {/* 登出 */}
        <button
          onClick={onLogout}
          style={{ background: 'none', border: '1px solid rgba(255,100,100,0.3)', borderRadius: 3, color: 'rgba(255,100,100,0.7)', padding: '3px 8px', cursor: 'pointer', fontSize: 10, fontFamily: 'inherit', letterSpacing: '0.08em' }}
        >
          🚪 退出
        </button>
      </div>
    </div>
  )
}
```

Run: `grep "StatusBar" frontend/src/dashboard/StatusBar.tsx`
Expected: `export default function StatusBar`

---

## Task 6: 创建 DashboardApp.tsx 大屏 App 壳

**Files:**
- Create: `frontend/src/DashboardApp.tsx`

**Steps:**

- [ ] **Step 1: 创建 DashboardApp.tsx**

```typescript
/**
 * 监管大屏 App 壳
 * - 未登录：显示 LoginPanel
 * - 已登录：显示 StatusBar + Dashboard（全屏图表）
 * - 自动刷新 + 手动刷新 + 离线降级横幅
 */
import { useState, useEffect, useCallback, useRef } from 'react'
import { getToken, clearToken } from './api/client'
import LoginPanel from './dashboard/LoginPanel'
import StatusBar from './dashboard/StatusBar'
import Dashboard from './dashboard/Dashboard'

export default function DashboardApp() {
  const [authed, setAuthed] = useState(() => !!getToken())
  const [autoRefreshInterval, setAutoRefreshInterval] = useState(30000) // 默认 30s
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [offlineError, setOfflineError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)   // 改变时触发 Dashboard 刷新
  const [loading, setLoading] = useState(false)
  const autoTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const retryTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 执行一次刷新
  const doRefresh = useCallback(async () => {
    setLoading(true)
    setOfflineError(null)
    try {
      // 验证 token 仍然有效（简单 ping）
      const res = await fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/auth/users`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      if (!res.ok) throw new Error('Unauthorized')
      setLastUpdate(new Date())
      setRefreshKey(k => k + 1)
    } catch {
      setOfflineError(`数据连接异常，展示数据截至 ${lastUpdate ? lastUpdate.toLocaleTimeString('zh-CN', { hour12: false }) : '—'}`)
      // 每 30s 重试
      if (!retryTimerRef.current) {
        retryTimerRef.current = setInterval(doRefresh, 30000)
      }
    } finally {
      setLoading(false)
    }
  }, [lastUpdate])

  // 自动刷新定时器
  useEffect(() => {
    if (autoTimerRef.current) clearInterval(autoTimerRef.current)
    if (autoRefreshInterval > 0) {
      autoTimerRef.current = setInterval(doRefresh, autoRefreshInterval)
    }
    return () => { if (autoTimerRef.current) clearInterval(autoTimerRef.current) }
  }, [autoRefreshInterval, doRefresh])

  // 清理重试定时器
  useEffect(() => {
    return () => { if (retryTimerRef.current) clearInterval(retryTimerRef.current) }
  }, [])

  function handleLogin() {
    setAuthed(true)
    doRefresh()
  }

  function handleLogout() {
    clearToken()
    setAuthed(false)
    setLastUpdate(null)
    setOfflineError(null)
  }

  if (!authed) {
    return <LoginPanel onLogin={handleLogin} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* 离线横幅 */}
      {offlineError && (
        <div style={{
          padding: '6px 16px', background: 'rgba(255,170,0,0.15)', borderBottom: '1px solid rgba(255,170,0,0.4)',
          color: '#ffaa00', fontSize: 11, fontFamily: 'var(--font-mono)', textAlign: 'center', flexShrink: 0,
        }}>
          ⚠ {offlineError}
        </div>
      )}

      {/* 刷新中顶栏提示 */}
      {loading && (
        <div style={{
          padding: '3px 16px', background: 'rgba(0,216,255,0.08)', borderBottom: '1px solid rgba(0,216,255,0.15)',
          color: '#00d8ff', fontSize: 10, fontFamily: 'var(--font-mono)', textAlign: 'center', flexShrink: 0,
        }}>
          🔄 数据刷新中...
        </div>
      )}

      {/* 状态栏 */}
      <StatusBar
        lastUpdate={lastUpdate}
        onRefresh={doRefresh}
        autoRefreshInterval={autoRefreshInterval}
        onAutoRefreshChange={setAutoRefreshInterval}
        onLogout={handleLogout}
      />

      {/* 主图表区 */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Dashboard key={refreshKey} />
      </div>
    </div>
  )
}
```

Run: `grep "DashboardApp" frontend/src/DashboardApp.tsx`
Expected: `export default function DashboardApp`

---

## Task 7: 更新 package.json 添加 dev:dashboard

**Files:**
- Modify: `frontend/package.json`

**Steps:**

- [ ] **Step 1: 添加 dev:dashboard script**

```json
"dev:dashboard": "vite --port 5174",
```

Run: `grep "dev:dashboard" frontend/package.json`
Expected: `"dev:dashboard": "vite --port 5174",`

---

## Task 8: 更新 index.html 添加 app 属性（区分 multi-page 入口）

**Files:**
- Modify: `frontend/index.html:1-5`

**Steps:**

- [ ] **Step 1: 添加 data-app 属性**

在 `<html>` 标签添加 `data-app="admin"` 属性，便于后续扩展或 CSS 作用域隔离。

```html
<html lang="zh" data-app="admin">
```

Run: `grep 'data-app="admin"' frontend/index.html`
Expected: `<html lang="zh" data-app="admin">`

---

## Task 9: 更新 restart.sh 支持同时启动两个前端

**Files:**
- Modify: `scripts/restart.sh`

**Steps:**

- [ ] **Step 1: 读取当前 restart.sh 内容**

确认 frontend 启动部分的逻辑（已在前面读取）。

- [ ] **Step 2: 修改 frontend 启动函数，使用 nohup 分离后台进程**

将 `start_frontend` 中的 `nohup ... &` 改为分别启动 admin 和 dashboard 两个进程，PID 分别写入 `.frontend.pid` 和 `.dashboard.pid`：

```bash
start_frontend() {
    echo "[$(date '+%H:%M:%S')] 启动前端 (Vite)..."
    cd "$FRONTEND_DIR"
    # 管理后台 5173
    nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE"
    # 监管大屏 5174
    nohup npm run dev:dashboard > "$FRONTEND_LOG/.dashboard.log" 2>&1 &
    echo $! > "$FRONTEND_PID_FILE.dashboard"
    cd "$PROJECT_ROOT"
    sleep 2
    echo "[$(date '+%H:%M:%S')] 前端已启动"
    echo "  管理后台: http://localhost:5173/"
    echo "  监管大屏: http://localhost:5174/"
}
```

- [ ] **Step 3: 修改 stop_frontend 清理两个 PID 文件**

```bash
stop_frontend() {
    if [ -f "$FRONTEND_PID_FILE" ]; then
        kill $(cat "$FRONTEND_PID_FILE") 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE"
    fi
    if [ -f "$FRONTEND_PID_FILE.dashboard" ]; then
        kill $(cat "$FRONTEND_PID_FILE.dashboard") 2>/dev/null || true
        rm -f "$FRONTEND_PID_FILE.dashboard"
    fi
    pkill -f "vite.*frontend" 2>/dev/null || true
}
```

Run: `grep "dev:dashboard" scripts/restart.sh`
Expected: `npm run dev:dashboard`

---

## Task 10: 验证构建

**Steps:**

- [ ] **Step 1: 验证 Vite multi-page 构建**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Expected: 输出包含 `dist/index.html` 和 `dist/dashboard.html`

- [ ] **Step 2: 启动两个前端**

```bash
./scripts/restart.sh
```

Expected:
- 管理后台: http://localhost:5173/
- 监管大屏: http://localhost:5174/

- [ ] **Step 3: 大屏登录页访问测试**

```bash
curl -s http://localhost:5174/ | grep -o '<title>.*</title>'
```

Expected: `<title>DRP 监管大屏</title>`

- [ ] **Step 4: 大屏登录测试**

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@drp.local","password":"DrpAdmin123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/users | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'用户数: {len(d)}')"
```

Expected: `用户数: 1`
