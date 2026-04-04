## Implementation

- [x] 1.1 创建 dashboard/ 目录结构（src/, index.html, vite.config.ts, package.json, tsconfig.json）
- [x] 1.2 创建 dashboard/src/main.tsx 入口脚本
- [x] 1.3 创建 dashboard/src/App.tsx 大屏 App 组件（LoginPanel + DashboardView）
- [x] 1.4 创建 dashboard/src/pages/LoginPanel.tsx 登录页（预填 admin@drp.local / DrpAdmin123!）
- [x] 1.5 复制大屏组件到 dashboard/src/dashboard/（D3Graphs、GeoMap、Dashboard、DashComponents、i18n、useRiskEvents）
- [x] 1.6 复制 dashboard/src/api/ API client（指向同一后端）
- [x] 1.7 复制 dashboard/src/index.css 全局样式
- [x] 1.8 配置 dashboard/package.json scripts（dev 端口 5181，build）
- [x] 1.9 dashboard/src/App.tsx 包含极简顶栏（自动刷新、手动刷新、登出、离线横幅）
- [x] 1.10 冒烟测试：启动两个前端，curl 验证 5180 和 5181 JS 模块加载正确

## Spec Deltas

- [x] 2.1 更新 monitoring-dashboard spec：大屏部署方式从"管理后台子路由"改为"独立项目 + 5181 端口"
- [x] 2.2 更新 admin-portal spec：说明大屏已拆分出去
