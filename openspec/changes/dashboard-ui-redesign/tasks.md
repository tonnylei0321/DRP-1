## Implementation

### 视觉基础
- [x] 1.1 更新 `dashboard/src/index.css` — CSS 变量、CRT 扫描线、辉光、呼吸灯、数值跳动动画、面板/树/跑马灯样式
- [x] 1.2 `dashboard/index.html` 已引入 Google Fonts（Orbitron, Share Tech Mono, Barlow Condensed）

### 布局框架
- [x] 2.1 创建 `dashboard/src/components/TopBar.tsx` — 顶部栏（Logo + 关键指标 + WS状态 + 登出）
- [x] 2.2 创建 `dashboard/src/components/EntityTree.tsx` — 左侧实体树，支持风险过滤，与地图联动
- [x] 2.3 创建 `dashboard/src/components/TacticalMap.tsx` — D3 Natural Earth 地图，点位渲染，HUD 点击
- [x] 2.4 创建 `dashboard/src/components/WarRoomInspector.tsx` — 右侧详情审查器
- [x] 2.5 创建 `dashboard/src/components/RiskTicker.tsx` — 底部外汇跑马灯，30s 滚动
- [x] 2.6 创建 `dashboard/src/components/HUDPanel.tsx` — HUD 弹窗，SVG 动态连线
- [x] 2.7 创建 `dashboard/src/components/FilterBar.tsx` — 风险过滤栏

### 动态效果
- [x] 3.1 数值跳动动画 — TopBar 指标每 2s 随机波动
- [x] 3.2 风险呼吸灯 — 高风险节点红色脉冲动画
- [x] 3.3 扫描线效果 — CRT scanline-beam + radial vignette
- [x] 3.4 HUD 出现动画 — hud-appear 0.2s ease-out
- [x] 3.5 连线虚线流动 — dash-flow animation

### 数据与状态
- [x] 4.1 `dashboard/src/data/indicators.ts` — 106 个 FIBO 标注指标 + 示例实体树（7 个区域/法人节点）
- [x] 4.2 地图点位生成器 — extractDots() 从实体树提取经纬度
- [x] 4.3 地图/树/HUD 三方联动 — 选中树节点 → 地图高亮 + HUD；点击地图 → 树高亮 + HUD

### 集成与冒烟测试
- [x] 5.1 `dashboard/src/App.tsx` 整合所有组件为三栏布局（TopBar + 三栏 + RiskTicker）
- [x] 5.2 登录页保留赛博格配色风格
- [x] 5.3 TypeScript 检查通过，冒烟测试通过（5174 正常加载）

## Spec Deltas
- [x] 6.1 monitoring-dashboard spec 已更新（UI/UE 规范已在 spec.md 中定义）
