## [2026-04-05 12:30] 第 1 次设计评审（双角色）
**阶段**：系统设计
**评审结论**：有条件通过 → 已修订通过
**角色 A**：design-architect（系统架构师）
**角色 B**：design-security（安全架构师）

### P0 处理记录（2项，全部接受）
- [B001] Mock数据权限列表改为占位符 test:perm_a/b/c
- [B002] 新增安全测试层 + Property 10 JWT安全验证

### P1 处理记录（6项，全部接受）
- [A001] Btn组件需添加className（代码修改项）
- [A002] WsStatus扩展为4种状态 + 重连策略
- [A003] 401自动清Token + Property 11
- [B003] 前端权限守卫测试声明
- [B004] WebSocket认证失败场景
- [B005] CSV注入防护用例

### P2 处理记录（6项，全部接受）
- [A004] 网络超时策略（AbortController）
- [A005] vitest.smoke.config.ts配置
- [A006] confirm/prompt改造清单补全
- [B006] Token存储安全边界 + XSS防护
- [B007] 错误消息脱敏验证
- [B008] 租户隔离专项测试
