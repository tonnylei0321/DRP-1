## [2026-04-05 22:00] 第 1 次设计评审（双角色）
**阶段**：系统设计
**评审结论**：有条件通过 → 已修订通过
**角色 A**：design-architect（系统架构师）— 正向验证
**角色 B**：design-security（安全架构师）— 反向挑战

### P0 处理记录（1项，接受）
- [001] DDL 内容直接发送外部 LLM API 数据泄露风险 → 新增"LLM 调用安全策略"章节：DDL 脱敏规则 + 审计日志 + 私有化 LLM 配置

### P1 处理记录（5项，全部接受）
- [002] /indicators 全局查询路由设计不完整 → 新增 GET /indicators 路由（无路径参数），保留现有 GET /indicators/{entity_id}
- [003] export-yaml 类型转换未明确 → 新增 generate_mapping_yaml_from_specs() 方法
- [004] batch-approve 缺少操作审计和数量上限 → 增加 max_count 参数 + 审计日志
- [005] DDL 注入风险 → 后端 5MB 限制 + 表名白名单 + SPARQL 值转义
- [006] SPARQL 注入风险 → 补充嵌套子查询测试 + 明确防护策略

### P2 处理记录（7项，全部接受）
- [007] Celery 任务名不一致 → 统一为 calculate_indicators_for_tenant_task
- [008] batch-approve 响应缺少 skipped_count → 增加字段
- [009] MappingSpec 缺少 data_type 列 → 新增 data_type: String(100) 列
- [010] reject_reason 无输入校验 → 最大 500 字符 + HTML 标签过滤
- [011] Alembic 迁移策略未明确 → 明确"先迁移后部署"策略
- [012] ETL 重试数据重复 → 传递原始 job_id + 写入前清除旧三元组
- [013] reject 端点缺少请求体 schema → 新增 RejectMappingRequest

### P3 处理记录（4项，全部接受）
- [014] DDL 生成器缺少完整列定义 → 补充说明"实现阶段根据 SPARQL 反推"
- [015] Hypothesis 未在 dev 依赖中 → 明确需添加到 pyproject.toml
- [016] 测试数据实体 ID 与生产冲突 → 统一加 test_ 前缀
- [017] Redis Pub/Sub 未按租户隔离 → 使用 risk_events:{tenant_id} 频道名

### P4 处理记录（1项，延后）
- [018] LLM 接口无速率限制 → 延后
