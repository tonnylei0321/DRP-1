## ADDED Requirements

### Requirement: Palantir 风格深色监管看板
系统 SHALL 提供深色主题的监管看板，采用青色/绿色/琥珀/红色四色风险语义，配合战术节点、HUD 浮窗和扫描线等视觉元素，营造专业情报指挥中心氛围。

#### Scenario: 看板初始加载
- **WHEN** 用户访问监管看板
- **THEN** 展示集团组织层级骨架图，节点按风险状态着色
- **AND** 顶部 Topbar 展示全局关键指标（集中率、直联率、结算率、违规数）
- **AND** 底部 Ticker 滚动展示实时风险事件流

#### Scenario: 风险节点视觉区分
- **WHEN** 某节点存在红线违规
- **THEN** 该节点呈红色脉冲动画
- **AND** 顶部违规计数器递增，告警横幅滚动播报

---

### Requirement: 混合布局 — 层级骨架 + 力导向展开
系统 SHALL 采用 D3 hierarchy 渲染集团组织层级骨架，点击节点时以 D3 forceSimulation 展开其下属账户网络子图。

#### Scenario: 展开子公司账户网络
- **WHEN** 用户点击某二级法人节点
- **THEN** 该节点周围以力导向布局展开其所有关联账户
- **AND** 账户节点与法人节点之间绘制归集关系边
- **AND** 其他未选中节点透明度降低，突出焦点

#### Scenario: 收起子图
- **WHEN** 用户点击空白区域或再次点击法人节点
- **THEN** 力导向子图收起，恢复层级骨架视图

---

### Requirement: HUD 浮窗交互
系统 SHALL 在用户点击任意节点时弹出 HUD 风格浮窗，展示节点详情并提供操作入口。

#### Scenario: 点击账户节点弹出 HUD
- **WHEN** 用户点击账户节点
- **THEN** HUD 浮窗从节点位置动画弹出
- **AND** 展示账户 ID、余额、直联状态、冻结标志等核心属性
- **AND** 提供"穿透溯源"、"查看历史"等操作按钮

---

### Requirement: 实时风险事件流
系统 SHALL 通过 WebSocket 推送实时风险事件，底部 Ticker 和右侧事件面板同步更新。

#### Scenario: 实时接收风险事件
- **WHEN** SHACL 生成新的 RiskEvent
- **THEN** 后端通过 Redis Pub/Sub 捕获事件
- **AND** 通过 WebSocket 推送到所有在线看板用户
- **AND** 底部 Ticker 新增该事件条目，相关节点视觉状态更新

---

### Requirement: 多语言支持
系统 SHALL 支持中文和英文界面切换，所有业务标签、提示文字和状态描述均提供双语版本。

#### Scenario: 切换界面���言
- **WHEN** 用户点击语言切换按钮
- **THEN** 界面所有文字即时切换，无需刷新页面
- **AND** 语言偏好持久化到用户配置
