# Change: DRP 监管大屏 UI/UE 全新设计

## Why
当前大屏 UI 沿用了管理后台的通用深色主题，缺乏"作战指挥中心"的专业氛围和金融监管的严肃感。用户要求全新设计，参考赛博格专业主义风格。

## What Changes
- 配色方案：深蓝黑背景 + 电光青/荧光绿/警示橙红 + 紫金点缀
- 字体：Orbitron（Logo/数值）+ Share Tech Mono（技术参数）+ Barlow Condensed（标签）
- 布局：三栏（左侧实体树 + 中间地图 + 右侧审查器）
- 地图：D3 Natural Earth 投影 + HUD 弹窗带连线
- 动态效果：CRT 扫描线、数值跳动、呼吸灯、外汇跑马灯
- 质感：辉光 (Glow)、阴极射线管伪元素

## Impact
- Affected specs: `monitoring-dashboard`（UI/UE 全面更新）
- Affected code: `dashboard/src/` 下所有组件和样式
- Break: 是，UI 全面重构
