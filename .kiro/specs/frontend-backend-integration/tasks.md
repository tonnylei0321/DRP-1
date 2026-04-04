# 实现计划：前后端集成 — 穿透式资金监管平台

## 概述

将前端原型硬编码数据替换为后端 FastAPI 真实数据。实现顺序：后端 API 新增 → 前端模块（auth/api_client/data_adapter）→ prototype_app.js 改造 → 测试（属性测试 + 单元测试 + 冒烟测试 + 集成测试）。

## 任务

- [x] 1. 后端：新增 Pydantic Schema 与组织架构 API
  - [x] 1.1 创建后端响应 Schema（OrgNodeResponse、IndicatorResponse、RelationResponse）
    - 在 `backend/src/drp/` 下合适位置新增 Pydantic v2 模型
    - `OrgNodeResponse`：包含 id、name、level、type、city、cash、debt、asset、guarantee、compliance、risk、has_children、children（递归）
    - `IndicatorResponse`：包含 id、name、domain、unit、value、threshold、direction
    - `RelationResponse`：包含 source、target、type
    - 所有缺失字段提供合理默认值
    - _需求: 13.1, 13.2, 13.3_

  - [x] 1.2 实现 `GET /org/tree` API 端点
    - 在 `backend/src/drp/` 下新增 `org/router.py`（或扩展已有路由）
    - 支持 `max_depth`（默认2，范围1-6）和 `root_id`（可选）查询参数
    - `root_id` 参数校验：仅允许字母数字下划线和连字符，防止 SPARQL 注入
    - 通过 SPARQL_Proxy 查询 GraphDB，按 `fibo:isSubsidiaryOf` 递归构建树
    - 使用 `get_current_user` 依赖进行 JWT 认证
    - SPARQL 查询超时 30 秒，结果集上限 1000 条
    - SPARQL 失败时返回 HTTP 500 + `{"detail": "数据查询失败，请稍后重试"}`
    - _需求: 13.1, 13.4, 13.5_

  - [x] 1.3 实现 `GET /org/{entity_id}/relations` API 端点
    - 在 `org/router.py` 中新增关系查询端点
    - `entity_id` 参数校验：仅允许字母数字下划线和连字符
    - 返回指定实体与同级实体之间的关系列表
    - 关系 type 取值：hasSubsidiary、fundFlow、guarantee、borrowing、fxExposure
    - 使用 `get_current_user` 依赖 + SPARQL_Proxy 租户隔离
    - _需求: 13.3, 13.4, 13.5_

  - [ ]* 1.4 后端组织架构 API 单元测试
    - 测试 `/org/tree` 正常查询、空结果、max_depth 边界、SPARQL 失败
    - 测试 `/org/{entity_id}/relations` 正常查询、实体不存在、SPARQL 失败
    - 使用 mock SPARQL_Proxy 隔离外部依赖
    - _需求: 13.1, 13.3, 13.5_

  - [ ]* 1.5 属性测试：组织架构树深度约束（Property 9）
    - **Property 9: 组织架构树深度约束**
    - 使用 hypothesis 生成随机 max_depth (1-6) + mock SPARQL 数据
    - 验证返回树中所有叶节点 level 不超过根节点 level + max_depth
    - **验证需求: 13.1**

- [x] 2. 后端：新增指标 API 端点
  - [x] 2.1 实现 `GET /indicators/{entity_id}` API 端点
    - 在 `backend/src/drp/indicators/` 下扩展或新增路由
    - `entity_id` 参数校验：仅允许字母数字下划线和连字符
    - 通过 SPARQL 查询实体关联的 RegulatoryIndicator
    - 返回7大领域下所有指标：id、name、domain（使用前端领域 ID）、unit、value、threshold、direction
    - 不返回 status 字段（由前端计算）
    - 后端路由层完成域名映射（后端域 → 前端领域 ID：fund/debt/guarantee/invest/derivative/finbiz/overseas）
    - 使用 `get_current_user` 依赖 + SPARQL_Proxy 租户隔离
    - _需求: 13.2, 13.4, 13.5_

  - [ ]* 2.2 后端指标 API 单元测试
    - 测试正常查询、实体不存在（404）、SPARQL 失败（500）
    - 验证域名映射正确性
    - _需求: 13.2, 13.5_

- [x] 3. 后端：注册新路由到 main.py
  - 将 org router 和 indicators 新端点注册到 `backend/src/drp/main.py`
  - 确保 CORS 配置允许前端域名访问
  - _需求: 13.1, 13.2, 13.3, 13.4_

- [ ]* 3.1 属性测试：后端 API 认证保护（Property 10）
  - **Property 10: 后端 API 认证保护**
  - 使用 hypothesis 对三个新端点（/org/tree、/indicators/{id}、/org/{id}/relations）发送无 Authorization 头请求
  - 验证均返回 HTTP 401
  - **验证需求: 13.4**

- [x] 4. 检查点 — 后端 API 就绪
  - 确保所有后端测试通过，ask the user if questions arise.

- [x] 5. 前端：实现 auth.js 认证模块
  - [x] 5.1 创建 `auth.js` 模块
    - 实现 `Auth` 对象：checkAuth()、login()、logout()、getToken()、getTenantId()、isTokenExpired()
    - TOKEN_KEY = 'drp_access_token'，TENANT_KEY = 'drp_tenant_id'
    - login() 调用 `POST /auth/login`，成功后存储 access_token 到 localStorage
    - 从 JWT payload（base64 解码）解析 tenant_id 和 exp
    - isTokenExpired() 比较 exp 与当前时间戳
    - logout() 清除 localStorage 并重定向到登录页
    - checkAuth() 检查 token 存在且未过期，否则显示登录页
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ]* 5.2 属性测试：JWT Payload 解析正确性（Property 3）
    - **Property 3: JWT Payload 解析正确性**
    - 使用 fast-check 生成随机 JWT payload（含 tenant_id + exp）
    - 验证 getTenantId() 返回值与 payload 中 tenant_id 一致
    - 验证 isTokenExpired() 在 exp < 当前时间时返回 true，反之 false
    - **验证需求: 2.5, 2.7, 9.1**

  - [ ]* 5.3 auth.js 单元测试
    - 测试登录成功/失败、token 过期检测、logout 清除、401 时的行为
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 6. 前端：实现 api_client.js 客户端模块
  - [x] 6.1 创建 `api_client.js` 模块
    - 实现 `ApiClient` 对象：request()、get()、post()、download()
    - BASE_URL 默认 `http://localhost:8000`，TIMEOUT = 15000
    - 使用原生 fetch API + AbortController 实现超时
    - 自动从 Auth.getToken() 获取 token 注入 `Authorization: Bearer <token>` 头
    - HTTP 401 → 调用 Auth.logout() 重定向
    - HTTP 4xx/5xx → 返回 `{status, detail, url}` 结构化错误对象
    - 网络超时/不可达 → 返回 `{status: "network_error", detail, url}`
    - console.error 输出详细错误日志
    - _需求: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 10.5_

  - [ ]* 6.2 属性测试：Bearer Token 注入一致性（Property 1）
    - **Property 1: Bearer Token 注入一致性**
    - 使用 fast-check 生成随机 token 字符串 + 随机 URL path
    - 验证 request() 发出的请求头包含正确的 Authorization: Bearer <token>
    - **验证需求: 1.2, 9.2**

  - [ ]* 6.3 属性测试：结构化错误对象完整性（Property 2）
    - **Property 2: 结构化错误对象完整性**
    - 使用 fast-check 生成随机 4xx/5xx 状态码 + 随机错误消息
    - 验证返回的错误对象包含 status（等于 HTTP 状态码）、detail（非空字符串）、url 三个字段
    - **验证需求: 1.4**

  - [ ]* 6.4 api_client.js 单元测试
    - 测试 401 重定向、网络超时、正常 GET/POST 请求、download 方法
    - _需求: 1.3, 1.4, 1.5_

- [x] 7. 前端：实现 data_adapter.js 数据适配层
  - [x] 7.1 创建 `data_adapter.js` 模块
    - 实现 `DataAdapter` 对象：adaptOrgTree()、adaptIndicators()、adaptRelations()、adaptDrillPath()、computeStatus()
    - adaptOrgTree()：递归转换后端组织架构数据，补充缺失字段默认值（risk→'lo'、compliance→0、children→[]）
    - adaptIndicators()：按7大领域分组，计算每个指标的 status（红/黄/绿），计算领域 score 和 alertCount
    - computeStatus()：实现阈值逻辑（direction=up/down/mid 三种情况）
    - adaptRelations()：映射关系 type 到 REL_TYPES 键名，确保 source/target 为非空字符串
    - adaptDrillPath()：从 node_iri 提取最后一段（: 或 / 分隔符后）作为前端节点 ID
    - _需求: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 7.2 属性测试：组织架构数据适配完整性（Property 4）
    - **Property 4: 组织架构数据适配完整性**
    - 使用 fast-check 生成随机后端组织架构 JSON（含缺失字段变体）
    - 验证输出每个节点包含全部 13 个字段，缺失字段使用默认值
    - **验证需求: 3.2, 11.2, 11.5**

  - [ ]* 7.3 属性测试：指标状态计算正确性（Property 5）
    - **Property 5: 指标状态计算正确性**
    - 使用 fast-check 生成随机 value + threshold + direction 组合
    - 验证 computeStatus() 返回值符合红黄绿阈值规则
    - **验证需求: 4.2, 11.3**

  - [ ]* 7.4 属性测试：关系类型映射有效性（Property 6）
    - **Property 6: 关系类型映射有效性**
    - 使用 fast-check 生成随机关系数据列表
    - 验证输出每条边的 type 为五种合法值之一，source/target 为非空字符串
    - **验证需求: 6.2, 11.4**

  - [ ]* 7.5 属性测试：IRI 节点 ID 提取正确性（Property 7）
    - **Property 7: IRI 节点 ID 提取正确性**
    - 使用 fast-check 生成随机 IRI 字符串（含 : 和 / 分隔符）
    - 验证提取的节点 ID 等于最后一个分隔符之后的子串
    - **验证需求: 7.2**

  - [ ]* 7.6 data_adapter.js 单元测试
    - 测试各种边界数据转换：空数组、缺失字段、非法 type 值、空 IRI
    - _需求: 11.2, 11.3, 11.4, 11.5_

- [x] 8. 检查点 — 前端模块就绪
  - 确保所有前端模块测试通过，ask the user if questions arise.

- [x] 9. 前端：prototype_app.js 集成改造
  - [x] 9.1 集成 auth.js — 登录流程
    - 在 HTML 中引入 auth.js、api_client.js、data_adapter.js（`<script>` 标签）
    - window.onload 中先调用 Auth.checkAuth()，通过后再执行 renderAll()
    - 新增登录页 UI（Login_Page）：邮箱 + 密码输入框 + 登录按钮
    - 登录失败显示"邮箱或密码错误"提示（需求 2.4）
    - 新增"退出登录"按钮，调用 Auth.logout()
    - 状态栏显示当前租户名称（通过 `GET /tenants/{tenant_id}` 获取）
    - _需求: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 9.1, 9.3_

  - [x] 9.2 集成组织架构数据加载
    - 新增 `loadOrgTree()` 异步函数，调用 `GET /org/tree?max_depth=2`
    - 通过 DataAdapter.adaptOrgTree() 转换数据
    - 替换硬编码 `ORG` 变量，触发 renderAll() 重新渲染
    - 加载中显示骨架屏/加载动画（需求 3.4）
    - 加载失败显示错误提示 + 重试按钮（需求 3.5）
    - _需求: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 9.3 集成指标数据加载（含缓存）
    - 新增 `loadIndicators(entity_id)` 异步函数，调用 `GET /indicators/{entity_id}`
    - 实现 5 分钟内存缓存（indicatorCache，以 entity_id 为键）
    - 通过 DataAdapter.adaptIndicators() 转换数据
    - 更新右侧 Domain_Panel 指标列表、评分、告警计数
    - 更新中央 Entity_Graph 节点七瓣花颜色和告警徽章
    - 单个实体加载失败不影响其他实体（需求 4.5）
    - _需求: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ]* 9.4 属性测试：指标缓存有效期（Property 8）
    - **Property 8: 指标缓存有效期**
    - 使用 fast-check 生成随机 entity_id + 时间偏移
    - 验证 5 分钟内缓存命中，超过 5 分钟缓存未命中
    - **验证需求: 4.6**

  - [x] 9.5 集成穿透式钻取
    - 改造 `drillInto()` 为异步函数
    - 双击实体时调用后端获取子实体列表（`GET /org/tree?root_id={id}&max_depth=1`）
    - 并行请求关系数据（`GET /org/{id}/relations`），使用 Promise.allSettled
    - 更新 drillPath、currentNode，触发 renderAll()
    - 面包屑回退：已加载数据使用内存缓存，不重新请求
    - 加载中显示中央画布加载指示器（需求 5.5）
    - 失败时保持当前视图 + 通知提示（需求 5.6）
    - _需求: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 9.6 集成实体关系图谱数据
    - 新增 `loadRelations(entity_id)` 异步函数
    - 通过 DataAdapter.adaptRelations() 转换数据
    - 替换 buildGraphData() 中硬编码的关系生成逻辑
    - 保留现有力导向布局算法和 Canvas 渲染逻辑
    - 关系加载失败时回退到 parent-child 控股关系推导（需求 6.5）
    - _需求: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 9.7 集成穿透路径查询与高亮
    - 点击异常指标时调用 `GET /drill/path/{indicator_id}`
    - 通过 DataAdapter.adaptDrillPath() 转换路径数据
    - 按步骤顺序动画高亮路径节点和边
    - 空结果时显示通知"该指标暂无穿透路径数据"
    - _需求: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.8 集成 KPI 栏实时数据
    - 基于后端返回的实体数据计算 KPI 栏 6 个指标
    - 穿透钻取切换层级时重新计算 KPI
    - 保留现有 renderKPI() 函数，仅替换数据来源
    - _需求: 8.1, 8.2, 8.3_

  - [x] 9.9 集成溯源报告下载
    - 改造"风险报告"按钮：未选中指标时置灰不可点击
    - 选中指标后点击调用 `GET /drill/report/{indicator_id}`
    - 通过 ApiClient.download() 获取 Blob，触发浏览器下载
    - 支持 PDF 和 JSON 两种格式（根据 Content-Type 判断）
    - 下载中按钮禁用 + 显示"生成中..."
    - 失败时恢复按钮 + 通知提示
    - _需求: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 9.10 集成加载状态与错误处理
    - API 请求进行中：状态栏"本体引擎"旁显示加载动画
    - 所有请求完成无错误：恢复"● 已连接"（绿色）
    - 后端不可达：变更为"● 已断开"（红色）
    - 错误通知使用 `#notif` 通知条，3 秒自动消失
    - console.error 输出详细错误日志
    - _需求: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 9.11 集成多租户支持
    - 登录成功后从 JWT 提取 tenant_id 存储到全局状态
    - 状态栏显示租户名称（调用 `GET /tenants/{tenant_id}`）
    - HTTP 403 时显示"租户信息无效，请重新登录"并重定向登录页
    - _需求: 9.1, 9.2, 9.3, 9.4_

- [x] 10. 检查点 — 前端集成完成
  - 确保所有前端集成改造完成，ask the user if questions arise.

- [ ] 11. 冒烟测试
  - [ ] 11.1 编写冒烟测试脚本
    - **S1**: 后端服务启动 — `GET /docs` 返回 200
    - **S2**: 登录接口可用 — `POST /auth/login` 返回 200 或 401
    - **S3**: 组织架构 API 可用 — `GET /org/tree`（带 token）返回 200
    - **S4**: 指标 API 可用 — `GET /indicators/{id}`（带 token）返回 200 或 404
    - **S5**: 关系 API 可用 — `GET /org/{id}/relations`（带 token）返回 200
    - **S6**: 前端页面加载 — HTML 文件可访问，JS 无报错
    - **S7**: 登录页面渲染 — 无 token 时显示登录表单
    - 每条用例包含前置条件、操作步骤、预期结果
    - _需求: 1.1, 2.1, 3.1, 4.1, 6.1, 13.1, 13.2, 13.3_

- [ ] 12. 集成测试
  - [ ]* 12.1 编写端到端集成测试
    - 场景1：登录 → 加载组织架构 → 选中实体 → 查看指标（完整用户流程）
    - 场景2：穿透钻取 → 面包屑回退（多层级导航）
    - 场景3：指标异常 → 穿透路径 → 报告下载（风险追溯流程）
    - 场景4：多租户隔离 — 不同 tenant_id 返回不同数据
    - _需求: 2.1, 3.1, 4.1, 5.1, 7.1, 9.2, 12.1_

- [ ] 13. 最终检查点 — 全部测试通过
  - 确保所有测试通过（冒烟测试 + 单元测试 + 属性测试 + 集成测试），ask the user if questions arise.

## 说明

- 标记 `*` 的子任务为可选，可跳过以加速 MVP 交付
- 每个任务引用了具体的需求编号，确保需求全覆盖
- 冒烟测试在集成测试之前完成（符合用户规范要求）
- 属性测试验证设计文档中定义的 10 个正确性属性
- 检查点确保增量验证，避免问题累积
