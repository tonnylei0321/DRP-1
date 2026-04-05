# 需求文档：端到端测试数据流水线

## 简介

本功能为央企穿透式资金监管平台（DRP）构建一条完整的端到端测试数据流水线，覆盖从 DDL 生成、测试数据灌入、DDL 上传与映射生成、映射评审、ETL 执行与监控，到监管大屏指标展示与钻取的全链路。目标是让开发和测试团队能够在无真实源系统接入的情况下，验证平台 106 个监管指标（7 大业务域）的完整数据通路。

## 术语表

- **DDL_Generator**：DDL 与测试数据生成器，负责输出覆盖 7 大业务域的建表语句和 INSERT 数据
- **Test_Data**：测试数据集，包含正常值、预警值、红线值三种数据分布
- **Admin_Portal**：管理后台前端（frontend/），提供 DDL 上传、映射审核、ETL 监控等页面
- **DDL_Parser**：DDL 解析器（`backend/src/drp/mapping/ddl_parser.py`），支持 MySQL/PostgreSQL/Oracle 语法
- **LLM_Mapper**：LLM 映射服务（`backend/src/drp/mapping/llm_service.py`），调用大模型生成字段到 CTIO 本体的映射建议
- **Mapping_Spec**：映射规范记录，包含源字段、目标属性、置信度、审批状态
- **ETL_Engine**：ETL 同步引擎（`backend/src/drp/etl/engine.py`），支持全量/增量同步
- **Indicator_Calculator**：指标计算器（`backend/src/drp/indicators/calculator.py`），基于 SPARQL 查询计算 106 个指标值
- **Dashboard**：监管大屏前端（dashboard/），展示指标统计、热力矩阵、钻取面板
- **GraphDB**：Ontotext GraphDB 10.7，本体与三元组存储
- **CTIO**：Central Treasury Intelligence Ontology，央企资金监管本体
- **Named_Graph**：GraphDB 中按租户隔离的命名图（`urn:tenant:{id}`）
- **Business_Domain**：7 大业务域——银行账户(001-031)、资金集中(032-041)、结算(042-068)、票据(069-078)、债务融资(079-085)、决策风险(086-097)、国资委考核(098-106)

## 需求

### 需求 0：端到端流水线编排 [评审 #001]

**用户故事：** 作为测试工程师，我希望有一条清晰的端到端流水线编排，定义从 DDL 生成到大屏展示的完整步骤衔接，以便一次性完成全链路验证。

#### 验收标准

1. THE DDL_Generator SHALL 以 Python 脚本形式实现（`scripts/generate_test_data.py`），将生成的 DDL 文件输出到 `backend/tests/fixtures/ddl/` 目录，按域命名（如 `01_bank_account.sql`、`02_fund_concentration.sql`），测试数据输出到 `backend/tests/fixtures/data/` 目录 [评审 #007]
2. WHEN DDL 和测试数据生成完成后，THE DDL_Generator SHALL 输出一个合并的 `all_tables.sql` 文件（DDL + INSERT），可直接在 Admin_Portal 的 DDL 上传页粘贴使用
3. WHEN 映射审核全部完成后（所有映射状态为 approved 或 rejected），THE 后端 SHALL 提供 `/mappings/export-yaml` 接口，自动从已审核通过的映射记录中生成 mapping_yaml，用户无需手动构造 [评审 #002]
4. WHEN 用户在 Admin_Portal 的 ETL 监控页点击"触发同步"按钮时，THE Admin_Portal SHALL 自动调用 `/mappings/export-yaml` 获取 mapping_yaml，并预填到 ETL 触发表单中 [评审 #002]
5. WHEN ETL 任务状态变为 success 时，THE 后端 SHALL 自动触发 `Indicator_Calculator.calculate_all_domains()` 计算全部 106 个指标 [评审 #004]
6. WHEN 指标计算完成后，THE Admin_Portal SHALL 在 ETL 监控页显示"指标已更新"提示，并提供"查看大屏"链接跳转到 Dashboard（`http://localhost:5174/`）
7. THE 端到端流水线的完整步骤 SHALL 为：① 运行 `scripts/generate_test_data.py` → ② 在 Admin_Portal DDL 上传页粘贴 DDL → ③ 生成映射建议 → ④ 映射评审（批量确认） → ⑤ 触发 ETL → ⑥ 查看大屏指标

### 需求 1：DDL 文件生成

**用户故事：** 作为测试工程师，我希望自动生成覆盖 7 大业务域的 DDL 文件，以便为端到端测试提供源系统表结构。

#### 验收标准

1. THE DDL_Generator SHALL 生成覆盖 7 大 Business_Domain 的 CREATE TABLE 语句，每个域至少包含一张主表
2. WHEN DDL_Generator 生成银行账户域 DDL 时，THE DDL_Generator SHALL 包含直联账户表、内部存款账户表、受限账户表，字段覆盖指标 001-031 所需的原始数据列
3. WHEN DDL_Generator 生成资金集中域 DDL 时，THE DDL_Generator SHALL 包含资金池表、归集记录表，字段覆盖指标 032-041 所需的原始数据列
4. WHEN DDL_Generator 生成结算域 DDL 时，THE DDL_Generator SHALL 包含结算记录表、支付渠道表，字段覆盖指标 042-068 所需的原始数据列
5. WHEN DDL_Generator 生成票据域 DDL 时，THE DDL_Generator SHALL 包含票据表、背书链表，字段覆盖指标 069-078 所需的原始数据列
6. WHEN DDL_Generator 生成债务融资域 DDL 时，THE DDL_Generator SHALL 包含贷款表、债券表、融资租赁表，字段覆盖指标 079-085 所需的原始数据列
7. WHEN DDL_Generator 生成决策风险域 DDL 时，THE DDL_Generator SHALL 包含授信表、担保表、关联交易表、衍生品表，字段覆盖指标 086-097 所需的原始数据列
8. WHEN DDL_Generator 生成国资委考核域 DDL 时，THE DDL_Generator SHALL 包含财务报表表、考核指标表，字段覆盖指标 098-106 所需的原始数据列
9. THE DDL_Generator SHALL 为每张表添加 COMMENT 注释（表注释和列注释），以便 LLM_Mapper 生成高质量映射建议
10. THE DDL_Generator SHALL 生成兼容 PostgreSQL 语法的 DDL，与项目数据库环境一致

### 需求 2：测试数据生成

**用户故事：** 作为测试工程师，我希望自动生成覆盖正常值、预警值、红线值的测试数据，以便验证指标计算和风险告警的完整性。

#### 验收标准

1. THE DDL_Generator SHALL 为每张表生成 SQL INSERT 语句形式的 Test_Data
2. THE Test_Data SHALL 包含三种数据分布：正常值（指标达标）、预警值（接近阈值）、红线值（超过红线）
3. WHEN 生成银行账户域 Test_Data 时，THE DDL_Generator SHALL 生成至少 50 条直联账户记录、10 条内部存款记录、5 条受限账户记录
4. WHEN 生成结算域 Test_Data 时，THE DDL_Generator SHALL 生成至少 100 条结算记录，覆盖跨行、跨境、内部、网银等结算渠道
5. WHEN 生成票据域 Test_Data 时，THE DDL_Generator SHALL 生成至少 30 条票据记录，包含商业汇票、银行承兑汇票、电子商业汇票
6. THE Test_Data SHALL 包含至少 3 个法人实体（LegalEntity）的数据，以支持组织穿透钻取测试。具体为：至少 1 个集团、2 个大区、3 个子公司，并通过 `ctio:parentOrg` 属性建立层级关系（集团→大区→子公司） [评审 #008]
7. THE Test_Data SHALL 包含至少 2 条触发红线告警的数据记录（如资金集中率低于 85%、直联率低于 95%）
8. THE Test_Data SHALL 包含至少 2 条触发预警的数据记录（如指标值接近但未超过红线阈值）
9. FOR ALL 生成的 Test_Data，THE DDL_Generator SHALL 确保 INSERT 语句与对应 DDL 表结构的列名和数据类型一致（往返一致性）

### 需求 3：DDL 上传与映射生成

**用户故事：** 作为数据管理员，我希望通过管理后台上传 DDL 文件并自动生成 CTIO 本体映射建议，以便快速完成源系统接入配置。

#### 验收标准

1. WHEN 用户在 Admin_Portal 的 DDL 上传页选择 DDL 文件时，THE Admin_Portal SHALL 读取文件内容并显示在编辑区域。THE Admin_Portal SHALL 限制上传文件大小不超过 5MB，仅接受 .sql/.ddl/.txt 扩展名，并在上传前进行客户端校验 [评审 #012]
2. WHEN 用户点击"生成映射建议"按钮时，THE Admin_Portal SHALL 调用后端 `/mappings/generate` 接口，将 DDL 内容发送给 DDL_Parser 和 LLM_Mapper
3. WHEN DDL_Parser 解析 DDL 成功时，THE DDL_Parser SHALL 返回包含表名、列名、数据类型、注释的结构化元数据
4. IF DDL_Parser 解析 DDL 失败（无有效表定义），THEN THE 后端 SHALL 返回 HTTP 422 错误，包含描述性错误信息
5. WHEN LLM_Mapper 生成映射建议完成时，THE Admin_Portal SHALL 在解析结果预览区域展示映射列表，包含源字段、目标 CTIO 属性、置信度百分比
6. THE Admin_Portal SHALL 按置信度高低对映射建议进行颜色标记：≥80% 绿色、60%-79% 黄色、<60% 红色
7. WHEN 映射建议生成成功时，THE 后端 SHALL 将映射记录持久化到数据库，状态为 pending（待审核）或 auto_approved（自动批准，置信度≥90%）

### 需求 4：映射评审

**用户故事：** 作为数据管理员，我希望在管理后台查看映射建议列表并执行确认或拒绝操作，以便确保映射质量。

#### 验收标准

1. WHEN 用户进入 Admin_Portal 的映射审核页时，THE Admin_Portal SHALL 从后端 `/mappings` 接口加载映射列表
2. THE Admin_Portal SHALL 将映射列表分为"待审核"和"已审核"两个区域展示
3. THE Admin_Portal SHALL 为每条待审核映射显示：源字段（表名.列名）、目标 CTIO 属性、数据类型、置信度进度条
4. WHEN 用户点击"确认"按钮时，THE Admin_Portal SHALL 调用 `/mappings/{id}/approve` 接口，将映射状态更新为 approved
5. WHEN 用户点击"拒绝"按钮时，THE Admin_Portal SHALL 弹出拒绝原因输入框，用户确认后调用 `/mappings/{id}/reject` 接口，请求体包含 `reason` 字段。THE 后端 SHALL 将拒绝原因持久化到 Mapping_Spec 记录中 [评审 #003]
6. WHEN 映射状态更新成功时，THE Admin_Portal SHALL 刷新映射列表，将该条映射移至"已审核"区域
7. IF 后端返回 404 错误（映射不存在），THEN THE Admin_Portal SHALL 显示错误提示并刷新列表
8. THE Admin_Portal SHALL 提供"全部确认"按钮，一键将所有待审核映射状态更新为 approved [评审 #005]
9. THE Admin_Portal SHALL 提供"按阈值批量确认"功能，一键确认所有置信度 ≥ 指定阈值（默认 80%）的待审核映射 [评审 #005]

### 需求 5：ETL 执行与监控

**用户故事：** 作为数据管理员，我希望触发 ETL 任务将测试数据写入 GraphDB，并实时监控任务执行状态，以便确认数据已正确入图。

#### 验收标准

1. WHEN 用户在 Admin_Portal 的 ETL 监控页点击"触发同步"按钮时，THE Admin_Portal SHALL 显示触发表单（租户选择、表名选择），并自动从 `/mappings/export-yaml` 获取 mapping_yaml 预填 [评审 #002]
2. WHEN 后端接收到 ETL 触发请求时，THE 后端 SHALL 创建 ETL 任务记录（状态为 pending），并通过 Celery 异步执行同步任务
3. WHEN ETL_Engine 执行同步时，THE ETL_Engine SHALL 读取源数据、应用映射规则、生成 SPARQL INSERT 语句，写入租户 Named_Graph
4. WHEN ETL 任务执行成功时，THE ETL_Engine SHALL 更新任务状态为 success，记录写入的三元组数量和完成时间
5. IF ETL 任务执行失败，THEN THE ETL_Engine SHALL 更新任务状态为 failed，记录错误信息
6. WHEN 用户进入 Admin_Portal 的 ETL 监控页时，THE Admin_Portal SHALL 展示最近 100 条 ETL 任务记录，包含任务 ID、类型、状态、写入三元组数、耗时、错误信息
7. THE Admin_Portal SHALL 为 ETL 任务状态使用颜色标记：success 绿色、running 黄色、failed 红色、pending 灰色
8. IF Celery Worker 不可用，THEN THE 后端 SHALL 将任务标记为 failed，错误信息为"Celery 不可用，无法异步执行"
9. WHEN ETL 任务状态为 failed 时，THE Admin_Portal SHALL 显示"重试"按钮，点击后以相同参数重新触发 ETL 任务 [评审 #006]
10. WHEN ETL 任务状态为 failed 时，THE Admin_Portal SHALL 显示"查看详细日志"链接，展开显示完整错误堆栈信息 [评审 #006]

### 需求 6：指标计算与大屏展示

**用户故事：** 作为监管人员，我希望在监管大屏看到基于测试数据计算的 106 个指标统计值，并支持按组织层级穿透钻取，以便验证端到端数据通路的正确性。

#### 验收标准

1. WHEN ETL 任务状态变为 success 时，THE 后端 SHALL 自动触发 Indicator_Calculator 基于 GraphDB 中的三元组数据，通过 SPARQL 查询计算 106 个指标的当前值 [评审 #004]
2. THE Indicator_Calculator SHALL 按 7 大 Business_Domain 分批执行指标计算：银行账户(001-031)、资金集中(032-041)、结算(042-068)、票据(069-078)、债务融资(079-085)、决策风险(086-097)、国资委考核(098-106)
3. WHEN 指标计算完成时，THE Indicator_Calculator SHALL 将结果写入 GraphDB（更新 RegulatoryIndicator 实例的 currentValue）并缓存到 Redis（TTL=3600 秒）
4. WHEN 指标值不达标时，THE Indicator_Calculator SHALL 通过 Redis Pub/Sub 频道 `risk_events` 发布风险事件
5. WHEN 用户打开 Dashboard 时，THE Dashboard SHALL 调用 `/indicators` 接口获取全部 106 个指标的当前值、目标值、预警阈值、红线阈值
6. THE Dashboard SHALL 在热力矩阵（DomainHeatmap）中按 7 大域展示域级合规率，颜色编码为：合规率 ≥98% 青绿色(#00ffb3)、95%-97.9% 青色(#22d3ee)、90%-94.9% 橙色(#ffaa00)、<90% 红色(#ff2020) [评审 #011]
7. WHEN 用户点击热力矩阵中的某个域时，THE Dashboard SHALL 展开指标钻取面板（IndicatorDrilldown），显示该域下所有指标的当前值、目标值、红线、状态
8. THE Dashboard SHALL 在实体树（EntityTree）中展示组织层级结构（集团→大区→子公司），数据来源于后端 `/org/tree` API 端点（已有实现），支持按风险等级过滤 [评审 #008]
9. WHEN 用户在实体树中选择某个法人实体时，THE Dashboard SHALL 调用 `/indicators?entity_id={id}` 接口获取该实体关联的指标数据，实现组织穿透钻取 [评审 #009]
10. WHEN 某个域的所有指标 currentValue 均为 0 或 NULL 时，THE Dashboard SHALL 在该域的钻取面板中显示诊断提示"该域暂无有效数据，请检查 ETL 任务状态和映射配置" [评审 #010]

### 需求 7：DDL 解析器往返一致性

**用户故事：** 作为开发者，我希望确保 DDL 解析器能正确解析生成的 DDL 文件，以便保证数据流水线的可靠性。

#### 验收标准

1. FOR ALL DDL_Generator 生成的 DDL 文件，THE DDL_Parser SHALL 成功解析并返回与生成时一致的表名列表
2. FOR ALL DDL_Generator 生成的表，THE DDL_Parser SHALL 正确提取每张表的所有列名、数据类型和注释
3. FOR ALL DDL_Parser 解析结果中的列，THE 列的 data_type 字段 SHALL 与 DDL 中定义的类型字符串匹配（忽略大小写和空格差异）
4. FOR ALL DDL_Parser 解析结果中带注释的列，THE 列的 comment 字段 SHALL 与 DDL 中 COMMENT 子句的内容一致
