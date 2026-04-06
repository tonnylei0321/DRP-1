# 实施计划：端到端测试数据流水线

## 概述

按照设计文档的实施顺序，将端到端测试数据流水线拆分为 6 个阶段：DDL 生成器脚本 → 后端 API 修改 → 前端管理后台修改 → 监管大屏修改 → 属性测试与单元测试 → 端到端冒烟验证。每个阶段的任务增量构建，确保无孤立代码。

## 任务

- [x] 1. DDL 生成器脚本（`scripts/generate_test_data.py`）
  - [x] 1.1 创建 `scripts/generate_test_data.py` 脚本骨架与数据模型定义
    - 定义 `TableDef`、`ColumnDef`、`Entity`、`Distribution` 数据类
    - 定义 `ENTITY_HIERARCHY` 法人实体层级（ID 统一加 `test_` 前缀）
    - 定义 `DOMAIN_TABLES` 注册表：7 大域的表结构定义（表名、列名、数据类型、COMMENT 注释）
    - 列定义需根据 `backend/src/drp/indicators/registry.py` 中 106 条指标的 SPARQL 查询反推，确保每个指标所需的原始数据列都有对应表字段
    - 7 大域至少包含：银行账户域（direct_linked_account、internal_deposit_account、restricted_account）、资金集中域（cash_pool、collection_record）、结算域（settlement_record、payment_channel）、票据域（bill、endorsement_chain）、债务融资域（loan、bond、finance_lease）、决策风险域（credit_line、guarantee、related_transaction、derivative）、国资委考核域（financial_report、assessment_indicator）
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 2.6_

  - [x] 1.2 实现 `TestDataFactory` 测试数据工厂
    - 实现 `generate(table, count, distribution)` 方法，按正常(70%)/预警(20%)/红线(10%) 分布生成数据
    - 银行账户域：至少 50 条直联账户、10 条内部存款、5 条受限账户
    - 结算域：至少 100 条结算记录，覆盖跨行/跨境/内部/网银渠道
    - 票据域：至少 30 条票据，含商业汇票/银行承兑汇票/电子商业汇票
    - 包含至少 2 条红线告警数据（如资金集中率 < 85%、直联率 < 95%）
    - 包含至少 2 条预警数据（接近但未超过红线阈值）
    - 所有 `entity_id` 引用 `ENTITY_HIERARCHY` 中的 `test_` 前缀实体
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 1.3 实现 DDL 与 INSERT 文件输出
    - 生成 `backend/tests/fixtures/ddl/01_bank_account.sql` ~ `07_sasoe_assessment.sql`（按域分文件，含 CREATE TABLE + COMMENT）
    - 生成 `backend/tests/fixtures/data/01_bank_account_data.sql` ~ `07_sasoe_assessment_data.sql`（INSERT 语句）
    - 生成合并文件 `backend/tests/fixtures/ddl/all_tables.sql`（DDL + INSERT）
    - 每张表必须有表级 COMMENT 和列级 COMMENT（非空）
    - INSERT 列名集合与 CREATE TABLE 列名集合完全一致
    - _需求: 0.1, 0.2, 1.9, 1.10, 2.1, 2.9_

- [x] 2. 检查点 — DDL 生成器验证
  - 运行 `python scripts/generate_test_data.py`，确认 `backend/tests/fixtures/ddl/` 和 `backend/tests/fixtures/data/` 下生成预期文件
  - 确保所有测试通过，如有问题请询问用户

- [x] 3. 后端 API 修改
  - [x] 3.1 MappingSpec 模型变更与 Alembic 迁移
    - 在 `backend/src/drp/mapping/models.py` 的 `MappingSpec` 类新增 `reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)` 和 `data_type: Mapped[str | None] = mapped_column(String(100), nullable=True)`
    - 创建 Alembic 迁移脚本：`ALTER TABLE mapping_spec ADD COLUMN reject_reason TEXT NULL; ADD COLUMN data_type VARCHAR(100) NULL;`
    - _需求: 4.5, 3.3_

  - [x] 3.2 新增 `RejectMappingRequest` schema 并修改 reject 端点
    - 在 `backend/src/drp/mapping/schemas.py` 新增 `RejectMappingRequest(BaseModel)` 含 `reason: str | None = Field(None, max_length=500)`
    - 修改 `backend/src/drp/mapping/router.py` 的 `reject_mapping` 端点：接收 `RejectMappingRequest` 请求体，将 `reason` 持久化到 `reject_reason` 字段，过滤 HTML 标签防止存储型 XSS
    - _需求: 4.5_

  - [x] 3.3 新增 `/mappings/export-yaml` 端点
    - 在 `backend/src/drp/mapping/router.py` 新增 `GET /mappings/export-yaml`，权限 `mapping:read`
    - 查询当前租户所有 `status=approved` 的 MappingSpec
    - 在 `backend/src/drp/mapping/yaml_generator.py` 新增 `generate_mapping_yaml_from_specs(specs: list[MappingSpec]) -> str` 方法（直接从 ORM 对象序列化，含 data_type 字段）
    - 无已审核映射时返回 HTTP 404
    - _需求: 0.3_

  - [x] 3.4 新增 `/mappings/batch-approve` 端点
    - 在 `backend/src/drp/mapping/router.py` 新增 `POST /mappings/batch-approve`，权限 `mapping:approve`
    - 请求体含 `mode`（all/threshold）、`threshold`（默认 80.0）、`max_count`（默认 500）
    - `mode=all`：更新所有 pending 映射为 approved（受 max_count 限制）
    - `mode=threshold`：更新 pending 且 confidence >= threshold 的映射为 approved
    - 响应含 `approved_count`、`skipped_count`、`total_pending`
    - 写入审计日志：操作人、时间、模式、影响条数
    - _需求: 4.8, 4.9_

  - [x] 3.5 新增 `GET /indicators` 路由（无路径参数）
    - 在 `backend/src/drp/indicators/router.py` 新增 `GET /indicators`（无路径参数），支持可选 `entity_id` 查询参数
    - `entity_id` 为空时返回全局指标聚合值；非空时返回该实体关联指标
    - 保留现有 `GET /indicators/{entity_id}` 路由，保持向后兼容
    - _需求: 6.5, 6.9_

  - [x] 3.6 ETL 成功后自动触发指标计算
    - 修改 `backend/src/drp/etl/_task_runner.py`：在 `run_full_sync` 和 `run_incremental_sync` 成功后调用 `calculate_indicators_for_tenant_task.delay(tenant_id)`
    - _需求: 0.5, 6.1_

  - [x] 3.7 DDL 注入防护与 LLM 审计日志
    - 后端 `/mappings/generate` 端点增加 DDL 内容大小限制（最大 5MB）
    - DDL 解析后的表名/列名白名单校验：仅允许 `[a-zA-Z0-9_]` 字符
    - 在 LLM 调用处记录审计日志：调用时间、操作人、租户 ID、表数量、字段数量、映射建议数量、耗时、状态
    - _需求: 3.1（安全部分）_

- [x] 4. 检查点 — 后端 API 验证
  - 运行 `cd backend && uv run pytest tests/ -x`，确保现有测试不被破坏
  - 确保所有测试通过，如有问题请询问用户

- [x] 5. 前端管理后台修改
  - [x] 5.1 DDL 上传页文件校验
    - 修改 `frontend/src/pages/MappingPages.tsx` 的 `DdlUploadPage` 组件
    - 文件上传增加客户端校验：大小 ≤ 5MB、扩展名 `.sql/.ddl/.txt`
    - 校验失败时显示 ErrorBox 提示（"文件大小不能超过 5MB" / "仅支持 .sql/.ddl/.txt 文件"）
    - _需求: 3.1_

  - [x] 5.2 映射审核页批量操作
    - 修改 `frontend/src/pages/MappingPages.tsx` 的 `MappingsPage` 组件
    - 新增"全部确认"按钮，调用 `mappingApi.batchApprove('all')`
    - 新增"按阈值批量确认"按钮（默认 80%），调用 `mappingApi.batchApprove('threshold', 80)`
    - 拒绝弹窗的 `reason` 字段已传递到后端（确认现有实现正确）
    - _需求: 4.8, 4.9_

  - [x] 5.3 API 客户端扩展
    - 在 `frontend/src/api/client.ts` 的 `mappingApi` 对象新增：
      - `exportYaml: () => request<{ mapping_yaml: string }>('GET', '/mappings/export-yaml')`
      - `batchApprove: (mode, threshold?) => request<{ approved_count: number; skipped_count: number; total_pending: number }>('POST', '/mappings/batch-approve', { mode, threshold })`
    - _需求: 0.3, 4.8_

  - [x] 5.4 ETL 监控页增强
    - 修改 `frontend/src/pages/AdminPages.tsx` 的 `EtlPage` 组件
    - 新增"触发同步"按钮：点击后调用 `mappingApi.exportYaml()` 获取 mapping_yaml → 显示触发表单（租户选择、表名输入、mapping_yaml 预填只读）→ 提交调用 `etlApi.trigger()`
    - ETL 成功后显示"指标已更新"提示 + "查看大屏"链接（`http://localhost:5174/`）
    - 失败任务显示"重试"按钮和"查看详细日志"展开区域
    - _需求: 0.4, 0.6, 5.1, 5.9, 5.10_

- [x] 6. 检查点 — 前端管理后台验证
  - 运行 `cd frontend && npm test`，确保现有测试不被破坏
  - 确保所有测试通过，如有问题请询问用户

- [x] 7. 监管大屏修改
  - [x] 7.1 大屏诊断提示
    - 修改 `dashboard/src/components/IndicatorDrilldown.tsx`
    - 当某域所有指标 `currentValue` 均为 0 或 null 时，显示诊断提示："该域暂无有效数据，请检查 ETL 任务状态和映射配置"
    - _需求: 6.10_

  - [x] 7.2 大屏实体穿透钻取
    - 在 `dashboard/src/api/indicatorsApi.ts` 新增 `fetchIndicatorsByEntity(entityId: string)` 方法，调用 `GET /indicators?entity_id={entityId}`
    - 修改 `dashboard/src/components/EntityTree.tsx` 或其父组件：选中实体节点后调用 `fetchIndicatorsByEntity`，联动热力矩阵和钻取面板刷新
    - _需求: 6.9_

  - [x] 7.3 安装 dashboard 测试依赖
    - 在 `dashboard/package.json` 添加 devDependencies：`vitest`、`@testing-library/react`、`@testing-library/jest-dom`、`jsdom`、`fast-check`
    - 添加 test 脚本：`"test": "vitest --run"`
    - 创建 `dashboard/vitest.config.ts` 配置文件
    - _需求: 测试基础设施_

- [x] 8. 检查点 — 大屏修改验证
  - 确保 `cd dashboard && npm run build` 编译通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 9. 后端属性测试与单元测试
  - [x] 9.1 添加 hypothesis 到后端 dev 依赖
    - 在 `backend/pyproject.toml` 的 `[dependency-groups] dev` 中添加 `"hypothesis>=6.100.0"`
    - 运行 `cd backend && uv sync --group dev` 安装
    - _需求: 测试基础设施_

  - [ ]* 9.2 Property 1: DDL 解析往返一致性测试
    - 创建 `backend/tests/test_ddl_roundtrip.py`
    - **Property 1: DDL 解析往返一致性** — 对 DDL_Generator 生成的 DDL 文件，经 DDL_Parser 解析后返回一致的表名列表；每列的列名、数据类型（忽略大小写和空格）和注释与 DDL 定义一致
    - 使用 hypothesis 生成随机表结构组合，最少 100 次迭代
    - 标签：`# Feature: e2e-test-data-pipeline, Property 1: DDL 解析往返一致性`
    - **验证: 需求 1.10, 3.3, 7.1, 7.2, 7.3, 7.4**

  - [ ]* 9.3 Property 2: INSERT 与 DDL 列一致性测试
    - 在 `backend/tests/test_ddl_roundtrip.py` 中追加
    - **Property 2: 生成器 INSERT 与 DDL 列一致性** — INSERT 语句中的列名集合与 CREATE TABLE 列名集合完全一致，INSERT 值数量等于列数
    - 标签：`# Feature: e2e-test-data-pipeline, Property 2: 生成器 INSERT 与 DDL 列一致性`
    - **验证: 需求 2.9**

  - [ ]* 9.4 Property 3: 表 COMMENT 完整性测试
    - 在 `backend/tests/test_ddl_roundtrip.py` 中追加
    - **Property 3: 生成表 COMMENT 完整性** — 每张表包含表级 COMMENT；每列包含非空列级 COMMENT
    - 标签：`# Feature: e2e-test-data-pipeline, Property 3: 生成表 COMMENT 完整性`
    - **验证: 需求 1.9**

  - [ ]* 9.5 Property 4: export-yaml 仅包含已审核通过映射测试
    - 创建 `backend/tests/test_mapping_export.py`
    - **Property 4: export-yaml 仅包含已审核通过映射** — 混合状态映射集合中，export-yaml 仅包含 approved 条目，字段与数据库记录一致
    - 使用 hypothesis 生成随机映射状态组合
    - 标签：`# Feature: e2e-test-data-pipeline, Property 4: export-yaml 仅包含已审核通过映射`
    - **验证: 需求 0.3**

  - [ ]* 9.6 Property 5: 拒绝原因持久化往返测试
    - 创建 `backend/tests/test_mapping_reject.py`
    - **Property 5: 拒绝原因持久化往返** — 调用 reject 接口后查询映射记录，reject_reason 与提交原因一致，status 为 rejected
    - 使用 hypothesis 生成随机拒绝原因字符串
    - 标签：`# Feature: e2e-test-data-pipeline, Property 5: 拒绝原因持久化往返`
    - **验证: 需求 4.5**

  - [ ]* 9.7 Property 6: 批量确认按阈值正确过滤测试
    - 创建 `backend/tests/test_mapping_batch.py`
    - **Property 6: 批量确认按阈值正确过滤** — confidence >= T 且 pending 的映射变为 approved；confidence < T 的保持不变；非 pending 不受影响
    - 使用 hypothesis 生成随机置信度集合和阈值
    - 标签：`# Feature: e2e-test-data-pipeline, Property 6: 批量确认按阈值正确过滤`
    - **验证: 需求 4.8, 4.9**

  - [ ]* 9.8 Property 7: 指标达标判断正确性测试
    - 创建 `backend/tests/test_indicator_compliance.py`
    - **Property 7: 指标达标判断正确性** — 比率类指标 value >= threshold 达标；计数类指标 value <= threshold 达标；value 为 None 不达标
    - 使用 hypothesis 生成随机指标定义和值
    - 标签：`# Feature: e2e-test-data-pipeline, Property 7: 指标达标判断正确性`
    - **验证: 需求 6.4**

- [ ] 10. 前端属性测试
  - [ ]* 10.1 Property 8: 合规率颜色编码正确性测试
    - 创建 `dashboard/src/components/__tests__/DomainHeatmap.test.ts`
    - **Property 8: 合规率颜色编码正确性** — rate ≥ 98 → 青绿色、95-98 → 青色、90-95 → 橙色、< 90 → 红色
    - 使用 fast-check 生成随机合规率值（0-100），最少 100 次迭代
    - 标签：`// Feature: e2e-test-data-pipeline, Property 8: 合规率颜色编码正确性`
    - **验证: 需求 6.6**

  - [ ]* 10.2 Property 9: 域诊断提示显示逻辑测试
    - 创建 `dashboard/src/components/__tests__/IndicatorDrilldown.test.ts`
    - **Property 9: 域诊断提示显示逻辑** — 当且仅当域内所有指标 currentValue 均为 0 或 null 时显示诊断提示
    - 使用 fast-check 生成随机指标数据集合
    - 标签：`// Feature: e2e-test-data-pipeline, Property 9: 域诊断提示显示逻辑`
    - **验证: 需求 6.10**

- [x] 11. 检查点 — 全部测试验证
  - 运行 `cd backend && uv run pytest tests/ -x` 确保后端测试全部通过
  - 运行 `cd frontend && npm test` 确保前端测试全部通过
  - 运行 `cd dashboard && npm test` 确保大屏测试全部通过
  - 确保所有测试通过，如有问题请询问用户

- [x] 12. 冒烟测试
  - [x] 12.1 编写后端冒烟测试
    - 创建 `backend/tests/test_e2e_smoke.py`，标记 `@pytest.mark.integration`
    - 用例 1：运行 `scripts/generate_test_data.py` → 验证 `backend/tests/fixtures/ddl/` 下生成 7 个域文件 + `all_tables.sql`
    - 用例 2：读取 `all_tables.sql` → 调用 DDL_Parser → 验证解析出的表数量 ≥ 14（7 域 × 2 表）
    - 用例 3：调用 `/mappings/batch-approve` → 验证返回 approved_count + skipped_count = total_pending
    - 用例 4：调用 `/mappings/export-yaml` → 验证返回的 YAML 可被 `yaml.safe_load` 解析且包含 `mappings` 键
    - _需求: 0.7（全链路步骤验证）_

  - [ ]* 12.2 编写前端冒烟测试
    - 创建 `frontend/src/pages/__tests__/DdlUpload.test.tsx`：测试 5MB 限制和扩展名校验
    - 创建 `frontend/src/pages/__tests__/MappingBatch.test.tsx`：测试"全部确认"和"按阈值确认"按钮渲染和点击
    - _需求: 3.1, 4.8, 4.9_

- [x] 13. 最终检查点 — 端到端验证
  - 确保所有测试通过
  - 验证全链路步骤可执行：① 生成 DDL → ② 上传 → ③ 映射 → ④ ETL → ⑤ 大屏
  - 确保所有测试通过，如有问题请询问用户

## 冒烟测试用例

| 用例 | 前置条件 | 操作步骤 | 预期结果 |
|------|----------|----------|----------|
| 生成测试数据 | Python 3.11+ 已安装 | 运行 `python scripts/generate_test_data.py` | `backend/tests/fixtures/ddl/` 下生成 7 个域文件 + `all_tables.sql`；`backend/tests/fixtures/data/` 下生成 7 个数据文件 |
| DDL 上传生成映射 | 后端服务运行中 | 粘贴 `all_tables.sql` 内容到 DDL 上传页 → 点击"生成映射建议" | 映射列表显示，包含置信度颜色标记（绿/黄/红） |
| 文件校验拦截 | 管理后台已打开 | 上传一个 6MB 的 .sql 文件 | 显示"文件大小不能超过 5MB"错误提示，不发送请求 |
| 批量确认映射 | 有待审核映射 | 点击"全部确认" | 所有映射变为 approved，列表刷新到"已审核"区域 |
| 拒绝映射含原因 | 有待审核映射 | 点击"拒绝" → 输入原因 → 确认 | 映射变为 rejected，数据库 reject_reason 字段有值 |
| 导出映射 YAML | 有已审核映射 | 调用 `GET /mappings/export-yaml` | 返回 YAML 字符串，仅包含 approved 状态的映射 |
| 触发 ETL | 映射已审核、Celery 运行中 | 点击"触发同步" → 表单自动预填 mapping_yaml → 提交 | ETL 任务创建，状态 pending → running → success |
| ETL 后指标自动计算 | ETL 任务成功完成 | 等待 Celery 任务链完成 | 指标计算任务被触发，Redis 缓存更新 |
| 查看大屏指标 | ETL 已成功、指标已计算 | 打开 `http://localhost:5174/` | 热力矩阵显示 7 域合规率，点击可钻取查看指标详情 |
| 域诊断提示 | 某域无有效数据 | 点击该域查看钻取面板 | 显示"该域暂无有效数据，请检查 ETL 任务状态和映射配置" |
| 实体穿透钻取 | 指标数据已计算 | 在实体树选择某子公司节点 | 热力矩阵和钻取面板刷新为该实体的指标数据 |

## 备注

- 标记 `*` 的任务为可选测试任务，可跳过以加速 MVP
- 每个任务引用了具体需求编号，确保需求全覆盖
- 检查点确保增量验证，及时发现问题
- 属性测试验证设计文档中定义的 9 个正确性属性
- 后端依赖管理使用 `uv`（非 pip），hypothesis 需添加到 dev 依赖组
- dashboard 需要新增 vitest + fast-check 测试基础设施
