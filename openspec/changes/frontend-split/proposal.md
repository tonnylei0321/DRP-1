# Change: 前端拆分为管理端与监管大屏

## Why
DRP 前端目前是单一 Vite + React 应用，通过侧边栏混合了管理后台功能和监管大屏功能。为支持管理后台和大屏的**独立部署、独立访问**，将其拆分为两个独立项目。

## What Changes
- 新增 `dashboard/` 目录作为独立 Vite + React 项目（端口 5174）
- `frontend/` 保持管理端项目（端口 5173）
- 大屏需要独立登录，使用与 admin 相同的 `/auth/login` API
- 大屏复用管理端的大屏组件（D3Graphs、GeoMap、Dashboard）

## Impact
- Affected specs: `monitoring-dashboard`（大屏部署方式变更）、`admin-portal`（大屏入口变更）
- Affected code: 新增 `dashboard/` 整个项目，frontend 无破坏性变更
