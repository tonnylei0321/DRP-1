# 设计方案：DRP 前端拆分为管理后台与监管大屏

## 1. 背景与目标

DRP 前端目前是单一 Vite + React 应用，通过侧边栏混合了管理后台功能和监管大屏功能。为支持管理后台和大屏的**独立部署、独立访问**，将其拆分为两个独立入口的应用。

## 2. 架构方案

### 2.1 目录结构

```
frontend/
├── index.html              # 管理后台入口（5173）
├── vite.config.ts          # 管理后台 Vite 配置
├── dashboard/             # 监管大屏（独立部署目录）
│   ├── index.html         # 大屏 HTML 入口
│   ├── main.tsx           # 大屏入口脚本
│   ├── vite.config.ts     # 大屏专用 Vite 配置
│   └── DashboardApp.tsx   # 大屏 App 壳
└── src/
    ├── App.tsx            # 管理后台 App
    ├── DashboardApp.tsx  # 大屏 App（shared）
    ├── main.tsx           # 管理后台入口脚本
    ├── pages/            # 管理后台页面
    ├── dashboard/         # 大屏组件（LoginPanel、StatusBar）
    ├── components/        # 共享 UI 组件
    ├── api/client.ts      # 共享 API client
    └── hooks/             # 共享 hooks
```
    ├── pages/              # 管理后台页面（保留）
    ├── dashboard/          # 大屏图表（保留）
    ├── components/         # 共享 UI 组件
    ├── api/client.ts       # 共享 API client
    └── hooks/              # 共享 hooks
```

### 2.2 入口配置

- `frontend/index.html` → 管理后台（`npm run dev`，默认 5173）
- `frontend/dashboard/` → 监管大屏（`npm run dev:dashboard`，默认 5174）
  - 独立 `vite.config.ts`，root 指向 `dashboard/` 目录
  - 通过 `--config dashboard/vite.config.ts` 指定配置

### 2.3 npm scripts

```json
{
  "dev": "vite",
  "dev:dashboard": "vite --config dashboard/vite.config.ts --port 5174",
  "build": "tsc -b && vite build",
  "build:dashboard": "vite build --config dashboard/vite.config.ts"
}
```

## 3. DashboardApp.tsx 详细设计

### 3.1 组件结构

```
DashboardApp
├── LoginPanel          # 未登录时显示
└── DashboardView       # 已登录时显示
    ├── StatusBar       # 极简顶栏（40px）
    └── Dashboard       # 全屏图表区域（复用现有组件）
```

### 3.2 登录机制

- 大屏独立登录页（`/dashboard` 路由对应 dashboard.html）
- 使用与 admin 相同的 `/auth/login` API
- 登录成功后 token 存入 `localStorage`（与管理后台共享同一 key）
- 大屏无需单独注册，使用同一套用户体系

### 3.3 刷新机制

**自动刷新：**
- 默认 30 秒自动刷新一次
- 可配置选项：15s / 30s / 60s / 关闭
- 刷新时显示微调动画（loading spinner）

**手动刷新：**
- 右上角刷新按钮
- 点击立即触发一次数据请求
- 请求完成后停止 loading 状态

**离线降级：**
- 网络中断时顶部显示橙色横幅："数据连接异常，展示数据截至 [时间]"
- 保留最后一次成功加载的数据继续展示
- 每 30 秒自动重试

### 3.4 极简顶栏设计

```
[状态条高度 40px，深色背景]
DRP 监管看板  |  最后更新: 12:34:56  |  🔄 自动刷新(30s)  |  手动刷新按钮  |  🌙 主题切换
```

## 4. 共享与隔离策略

| 资源 | 共享 | 隔离 |
|------|------|------|
| API client | ✅ `src/api/client.ts` | — |
| UI 组件 | ✅ `src/components/ui.tsx` | — |
| 全局样式 | ✅ `src/index.css` | — |
| 图表组件 | ✅ `src/dashboard/` | — |
| App 组件 | — | ❌ `App.tsx` vs `DashboardApp.tsx` |
| 入口文件 | — | ❌ `main.tsx` vs `dashboard-main.tsx` |
| HTML 壳 | — | ❌ `index.html` vs `dashboard.html` |

## 5. 后端兼容性

- 两个前端入口共享同一套后端 API
- 大屏登录使用相同的 `/auth/login` 接口
- JWT token 格式完全一致

## 6. 实施步骤

1. 创建 `frontend/dashboard/` 目录
2. 创建 `frontend/dashboard/index.html` 入口
3. 创建 `frontend/dashboard/main.tsx` 入口脚本
4. 创建 `frontend/dashboard/vite.config.ts` 大屏专用 Vite 配置
5. 创建 `frontend/src/DashboardApp.tsx` 大屏 App 组件
6. 创建 `frontend/src/dashboard/LoginPanel.tsx` 大屏登录页
7. 创建 `frontend/src/dashboard/StatusBar.tsx` 极简顶栏
8. 添加 `dev:dashboard` 和 `build:dashboard` npm script
9. 更新 `restart.sh` 支持同时启动两个前端
10. 修复既有 TypeScript 错误（D3 类型、`rect` 未使用、threshold 空值）
