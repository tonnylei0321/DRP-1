## [2026-04-05 11:00] 第 1 次需求评审（双角色）
**阶段**：需求分析
**评审结论**：有条件通过 → 已修订通过
**角色 A**：requirements-ba（业务分析师）
**角色 B**：requirements-ux（用户体验研究员）

### P1 处理记录（7项，全部接受）
- [A002/B011] CSS变量验证改为CSS类名验证
- [A003] @smoke标记改为 *.smoke.test.ts 文件命名约定
- [B001] 映射拒绝改为Modal交互，补充取消行为
- [B002] 删除确认改为自定义Modal，补充取消行为
- [B003/A004] 新增GroupsPage占位页面AC
- [B004] CSV导出范围明确为当前页数据
- [A001] Content-Type范围限定为POST/PUT

### P2 处理记录（7项，全部接受）
- [A005] 新增Dashboard主组件集成测试AC
- [A007/B015] mock端点列表细化为12个完整端点
- [A008] 新增ETL/租户/质量3个E2E场景
- [B006] 新增网络超时+WebSocket断线重连AC
- [B007] 新增401自动清Token+Token过期旅程恢复AC
- [B008] 新增SSO按钮URL跳转验证AC
- [B005] 新增监管看板冒烟测试AC
