## MODIFIED Requirements

### Requirement: 管理后台入口
系统 SHALL 提供管理后台作为独立前端项目（端口 5180），监管大屏已拆分为独立项目（端口 5181）。

#### Scenario: 访问管理后台
- **WHEN** 用户访问 http://localhost:5180
- **THEN** 展示管理后台登录页或已登录后的管理界面
- **AND** 管理后台包含侧边栏导航（用户、角色、租户、映射、ETL、审计等）
