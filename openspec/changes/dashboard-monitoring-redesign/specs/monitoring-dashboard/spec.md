## MODIFIED Requirements

### Requirement: 布局 — 五区指挥中心
系统 SHALL 采用五区布局：左侧风险灯塔 + 右上7域热力矩阵 + 中央战术地图 + 底部左侧处置队列 + 底部中央红线雷达盘。

#### Layout Spec
- **左侧风险灯塔**（固定宽度280px）：纵向4柱（CRITICAL/WARN/INFO/OK），柱高=数量，一眼判断全局态势
- **右上热力矩阵**（固定宽度320px）：6×2网格，每格=对应域合规率%
- **中央战术地图**：D3 Natural Earth 投影 + CRITICAL节点红色脉冲
- **底部左侧处置队列**：风险事件分级列表（CRITICAL立即处置/WARN 7天整改/INFO关注）
- **底部中央红线雷达盘**：6轴（直联率/全口径集中/可归集集中/结算直联/背书链深度/6311还款）

### Requirement: 风险灯塔
系统 SHALL 展示全局 CRITICAL/WARN/INFO/OK 四级事件数量。

#### Scenario: 点击风险灯塔
- **WHEN** 用户点击某级风险灯柱
- **THEN** 地图高亮该级所有节点，处置队列筛选到该级别

### Requirement: 7域热力矩阵
系统 SHALL 展示 CTIO 7大业务域合规率热力矩阵。

#### Heatmap Spec
| 域 | 代码 | 指标数 | 说明 |
|----|------|--------|------|
| 银行账户监管 | BA | 15 | 直联率、U-Key配置率 |
| 资金集中监管 | CC | 15 | 全口径集中率(红线95%)、可归集集中率(红线85%) |
| 结算监管 | ST | 15 | 结算直联率(红线95%) |
| 票据监管 | BL | 15 | 背书链深度(>20层WARN, >50层CRITICAL) |
| 债务融资监管 | DF | 15 | 6311还款完成率、担保合规率 |
| 决策风险 | DR | 16 | 资金决策合规率、关联交易合规率 |
| 国资委考核 | SA | 15 | 报表提交及时率、资金管理评级 |

#### Color Spec
- 绿色：合规率 ≥ 98%
- 青色：合规率 ≥ 95%
- 橙色：合规率 ≥ 90%
- 红色：合规率 < 90%

#### Scenario: 钻取域
- **WHEN** 用户点击热力矩阵某格
- **THEN** 展开该域下所有指标列表（编号、名称、当前值、目标值、阈值）

### Requirement: 红线雷达盘
系统 SHALL 展示4条红线指标的雷达图。

#### Radar Spec（6轴）
| 轴 | 指标 | 红线阈值 |
|----|------|---------|
| 轴1 | 账户直联率 IND-BA-002 | ≥ 95% |
| 轴2 | 全口径资金集中率 IND-CC-001 | ≥ 95% |
| 轴3 | 可归集资金集中率 IND-CC-002 | ≥ 85% |
| 轴4 | 结算直联率 IND-ST-001 | ≥ 95% |
| 轴5 | 票据背书链深度 IND-BL-001 | ≤ 20层 |
| 轴6 | 6311还款完成率 IND-DF-001 | ≥ 100% |

### Requirement: 风险处置队列
系统 SHALL 展示分级处置队列。

#### Disposition Spec
- **CRITICAL**（红色）：需立即处置，无条件执行
- **WARN**（橙色）：7天内整改，限期处置
- **INFO**（青色）：持续关注，监控跟踪

#### Queue Item Spec
```
[级别标签] [企业名称] [指标名称] [当前值] vs [红线值] [处置状态] [倒计时]
```

### Requirement: CTIO RiskEvent 联动
系统 SHALL 通过 WebSocket 接收 CTIO RiskEvent 实时推送，更新灯塔/热力图/地图/处置队列。

#### Scenario: CRITICAL 事件推送
- **WHEN** 后端 SHACL 生成 CRITICAL RiskEvent
- **THEN** WebSocket 推送到大屏
- **AND** 灯塔 CRITICAL 柱 +1
- **AND** 地图对应节点开始红色脉冲
- **AND** 处置队首新增记录

### Requirement: CTIO 指标数据
系统 SHALL 从后端 API 加载 CTIO 指标当前值（ctio:currentValue）。

#### Indicator API Spec
- `GET /indicators` — 返回所有 106 项指标（含 currentValue, targetValue, warnThreshold）
- `GET /risk-events` — 返回当前 RiskEvent 列表（按严重等级和时间排序）
- WebSocket `/ws/risk-events` — 实时推送新增 RiskEvent
