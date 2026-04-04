# Change: 监管大屏 UI/UE 全面重构 — 国资穿透式监管视角

## Why
当前大屏 UI 基于通用的 Palantir 风格设计，未体现"国资委一眼看清全局风险"的核心诉求。需要重构为以风险全貌为核心、分级处置为导向的监管指挥中心界面。

## What Changes

### 布局重构
- 左列：风险灯塔（纵向4柱，CRITICAL/WARN/INFO/OK 数量）
- 右上：7域热力矩阵（BA/CC/ST/BL/DF/DR/SA，每格合规率%）
- 中央：Tactical Map + CRITICAL 节点红色脉冲闪烁
- 底部左侧：风险处置队列（分级处置状态）
- 底部中央：6条红线雷达盘

### CTIO 本体融合
- 7大业务域（BA/CC/ST/BL/DF/DR/SA）热力矩阵，对应 CTIO 指标体系
- 四大红线（IND-BA-002/CC-001/CC-002/ST-001）雷达盘
- 风险处置队列联动 CTIO RiskEvent（CRITICAL/WARN/INFO 三级）

### 风险处置流程
- **CRITICAL** → 需立即处置（红色，无条件处置）
- **WARN** → 7天内整改（橙色，限期处置）
- **INFO** → 关注（青色，持续监控）
- 每条处置记录关联 CTIO RiskEvent，显示：节点名称 + 指标ID + 当前值 + 阈值 + 处置状态

### 数据刷新
- 实时风险事件流（WebSocket，CTIO RiskEvent 推送）
- 地图红色节点实时闪烁，触发条件：ctio:riskLevel = CRITICAL

## Impact
- Affected specs: `monitoring-dashboard`（UI/UE 全面重构，新增 CTIO 指标体系展示）
- Affected code: `dashboard/src/` 全部组件重构
- Break: 是，UI 全面改版
