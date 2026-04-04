## MODIFIED Requirements

### Requirement: UI 视觉设计 — 赛博格专业主义
系统 SHALL 采用赛博格专业主义视觉风格，营造"深夜作战指挥中心"氛围。

#### Visual Spec: 配色方案
- **背景**：深蓝黑色 `#020810`
- **主色**：电光青 `#00d8ff`（代表系统正常）
- **增长色**：荧光绿 `#00ffb3`
- **警示色**：警示橙 `#ffaa00`、危机红 `#ff2020`
- **点缀色**：紫色 `#a855f7`（SPV）、金色 `#ffd060`（Hub）

#### Visual Spec: 字体矩阵
- `Orbitron`：Logo 和核心数值，科幻感
- `Share Tech Mono`：等宽字体，技术参数和坐标
- `Barlow Condensed`：窄体字，高密度标签

#### Visual Spec: 质感与光效
- **辉光 (Glow)**：`drop-shadow` 和 `box-shadow` 为节点和 Logo 添加霓虹灯呼吸感
- **CRT 扫描线**：通过 `::after` 伪元素实现微弱扫描线效果

### Requirement: 布局 — 三栏 Matrix Layout
系统 SHALL 采用三栏布局：左侧实体树 + 中间战术地图 + 右侧作战室审查器。

#### Scenario: 三栏布局响应式
- **WHEN** 大屏加载
- **THEN** 左侧固定宽度实体树 + 中间自适应核心地图 + 右侧固定宽度审查器
- **AND** 底部跑马灯显示外汇行情

### Requirement: 战术地图 — D3 Natural Earth 投影
系统 SHALL 使用 D3.js Natural Earth 投影渲染地图，支持点位、辉光国家轮廓和 HUD 弹窗。

#### Scenario: 地图点位点击
- **WHEN** 用户点击地图上的点位
- **THEN** HUD 弹窗从节点位置动画弹出，带有一条动态连线指向地理位置
- **AND** 展示点位对应的机构详情

#### Scenario: 地图范围切换
- **WHEN** 用户仅有国内机构
- **THEN** 渲染中国地图
- **WHEN** 用户包含境外机构
- **THEN** 渲染世界地图

### Requirement: 动态效果
系统 SHALL 提供实时感动态效果。

#### Scenario: 数值跳动
- **WHEN** HUD 或 TopBar 显示数值时
- **THEN** 数值通过 JS 定时器进行微小的随机跳动，模拟实时交易数据流

#### Scenario: 风险节点呼吸灯
- **WHEN** 某节点风险等级为高
- **THEN** 该节点呈现红色脉冲/呼吸灯动画

#### Scenario: 地图扫描线
- **WHEN** 地图区域渲染时
- **THEN** 持续循环的扫描线动画增强"实时监控"心理暗示

### Requirement: 监控指标体系
系统 SHALL 提供 106 个监控指标，支持 FIBO 金融本体标注。

#### Data Spec: 指标数组结构
```typescript
interface Indicator {
  name: string;           // 指标名称
  fiboName: string;       // FIBO 实体名称
  value: number;          // 指标数值
  risk: 'none' | 'low' | 'medium' | 'high'; // 风险等级
}
```

#### Scenario: 实体树过滤
- **WHEN** 用户按风险等级筛选
- **THEN** 树视图和地图点位同步过滤，只显示匹配节点
