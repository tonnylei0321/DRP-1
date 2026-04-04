## MODIFIED Requirements

### Requirement: 监管大屏部署方式
系统 SHALL 提供独立的监管大屏前端应用，部署在独立端口（5174），与管理后台（5173）完全分离。

#### Scenario: 独立大屏访问
- **WHEN** 用户访问 http://localhost:5174
- **THEN** 展示独立的监管大屏（全屏图表，无侧边栏）
- **AND** 大屏需要登录认证，使用与 admin 相同的 `/auth/login` API
- **AND** JWT token 存储在 localStorage

### Requirement: 大屏自动刷新
系统 SHALL 提供大屏数据自动刷新机制。

#### Scenario: 自动刷新数据
- **WHEN** 大屏已登录且无用户交互
- **THEN** 每 30 秒自动刷新一次数据（可配置：15s/30s/60s/关闭）
- **AND** 刷新时右上角显示 loading 状态

#### Scenario: 手动刷新
- **WHEN** 用户点击手动刷新按钮
- **THEN** 立即触发一次数据请求
- **AND** 请求完成后停止 loading 状态
