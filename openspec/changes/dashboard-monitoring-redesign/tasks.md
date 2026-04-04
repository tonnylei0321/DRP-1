## Implementation

### 布局框架
- [ ] 1.1 创建 `RiskBeacon.tsx`（风险灯塔组件）— 纵向4柱，CRITICAL/WARN/INFO/OK 数量，点击联动地图
- [ ] 1.2 创建 `DomainHeatmap.tsx`（7域热力矩阵）— 6×2 网格（BA/CC/ST/BL/DF/DR/SA），颜色=合规率，点击钻取指标列表
- [ ] 1.3 创建 `RiskRadar.tsx`（红线雷达盘）— 6轴：直联率/全口径集中/可归集集中/结算直联/背书链深度/6311还款，当前值vs红线值
- [ ] 1.4 创建 `RiskDispositionQueue.tsx`（处置队列）— CRITICAL/WARN/INFO 分级列表，关联 CTIO RiskEvent
- [ ] 1.5 重构 `App.tsx` 布局 — 左右中三区 + 底部两区的新布局结构

### CTIO 数据融合
- [ ] 2.1 更新 `indicators.ts` — 接入 CTIO 7域指标体系（BA/CC/ST/BL/DF/DR/SA），使用真实指标编号（IND-XX-XXX）
- [ ] 2.2 创建 `indicatorsApi.ts` — 调用后端 API 获取 CTIO 指标当前值（ctio:currentValue）
- [ ] 2.3 创建 `riskEventApi.ts` — 调用后端 API 获取 CTIO RiskEvent 列表，按 CRITICAL/WARN/INFO 分级

### 地图增强
- [ ] 3.1 地图 CRITICAL 节点红色脉冲 — RiskEvent riskLevel=CRITICAL 时节点持续闪烁
- [ ] 3.2 地图节点关联 RiskEvent — 点击节点显示关联的风险事件列表
- [ ] 3.3 支持从风险处置队列点击 → 地图定位到对应企业节点

### 风险处置
- [ ] 4.1 创建 `DispositionCard.tsx` — 处置记录卡片：节点名称 + 指标 + 当前值 vs 阈值 + 处置状态 + 倒计时
- [ ] 4.2 处置状态流转 UI — CRITICAL→立即处置（红色）/ WARN→7天整改（橙色）/ INFO→持续关注（青色）
- [ ] 4.3 钻取到具体指标 — 从热力图点击域 → 展示该域下所有指标列表 + 当前值 + 阈值

### 动态效果增强
- [ ] 5.1 热力矩阵动画 — 单元格颜色随合规率动态变化
- [ ] 5.2 雷达盘绘制动画 — 启动时6条轴从0向当前值延伸动画
- [ ] 5.3 处置队列入场动画 — 新风险事件从右侧滑入

### API 集成
- [ ] 6.1 更新 `api/client.ts` — 添加指标查询接口（GET /indicators）和风险事件接口（GET /risk-events）
- [ ] 6.2 WebSocket 实时推送 — 连接后端 risk-event 推送，实时更新处置队列和地图节点

## Spec Deltas
- [ ] 7.1 更新 monitoring-dashboard spec — 新增完整 CTIO 指标体系展示规范、风险灯塔规范、热力矩阵规范、红线雷达规范、处置队列规范
