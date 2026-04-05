# 需求文档：前后端集成 — 穿透式资金监管平台

## 简介

将央企穿透式资金监管平台前端原型（`央企数字资产监管平台_prototype.html` + `prototype_app.js`）中的硬编码模拟数据替换为后端 FastAPI 服务提供的真实数据。前端通过 API 客户端层与后端通信，实现 JWT 认证、组织架构加载、7大领域106指标实时查询、实体关系图谱渲染、穿透式钻取以及多租户隔离。

## 术语表

- **Frontend**：前端原型应用，由 `央企数字资产监管平台_prototype.html` 和 `prototype_app.js` 组成
- **Backend**：FastAPI 后端服务，入口为 `backend/src/drp/main.py`
- **API_Client**：前端中负责与后端 REST API 通信的 JavaScript 模块
- **Auth_Module**：前端中负责 JWT 令牌管理（登录、存储、注入）的模块
- **Drill_API**：后端穿透溯源 API（`/drill` 前缀），提供三级穿透查询
- **Indicator_Registry**：后端 106 条监管指标 SPARQL 计算语句注册表
- **GraphDB**：RDF 图数据库，存储 FIBO+CTIO 本体数据，通过 SPARQL 查询
- **SPARQL_Proxy**：后端 SPARQL 代理层，自动注入租户 Named Graph 上下文
- **Tenant**：租户，对应一个央企集团，数据通过 GraphDB Named Graph 隔离
- **Organization_Tree**：组织架构树，表示集团→二级子集团→三级子公司→四级公司→五级SPV的层级结构
- **Domain_Panel**：右侧监管作战室中的7大领域面板（资金管理、债务管理、担保管理、投资管理、金融衍生品、金融业务、境外资金）
- **Entity_Graph**：中央画布区域的力导向实体关系图谱
- **Login_Page**：用户登录页面，用于输入凭证获取 JWT 令牌

## 需求

### 需求 1：API 客户端基础层

**用户故事：** 作为前端开发者，我希望有一个统一的 API 客户端模块，以便所有后端请求都经过统一的认证、错误处理和基础 URL 管理。

#### 验收标准

1. THE API_Client SHALL 提供一个可配置的 `BASE_URL` 属性，指向后端服务地址（默认值为 `http://localhost:8000`）
2. WHEN 发送任何 API 请求时，THE API_Client SHALL 在 HTTP 请求头中附加 `Authorization: Bearer <token>` 字段（token 从 Auth_Module 获取）
3. WHEN 后端返回 HTTP 401 状态码时，THE API_Client SHALL 清除本地存储的令牌并将用户重定向到 Login_Page
4. WHEN 后端返回 HTTP 4xx 或 5xx 状态码时，THE API_Client SHALL 返回包含 `status`、`detail`、`url` 字段的结构化错误对象
5. WHEN 网络请求超时（超过 15 秒）或网络不可达时，THE API_Client SHALL 返回包含 `status: "network_error"` 的错误对象
6. THE API_Client SHALL 使用浏览器原生 `fetch` API，不引入额外的 HTTP 库依赖

### 需求 2：JWT 认证集成

**用户故事：** 作为平台用户，我希望通过登录页面输入凭证获取访问令牌，以便安全地访问监管数据。

#### 验收标准

1. WHEN 用户打开 Frontend 且本地无有效 JWT 令牌时，THE Auth_Module SHALL 显示 Login_Page 并阻止访问主界面
2. WHEN 用户在 Login_Page 提交邮箱和密码时，THE Auth_Module SHALL 向 `POST /auth/login` 发送 `LoginRequest`（包含 `email` 和 `password` 字段）
3. WHEN 后端返回 `TokenResponse`（包含 `access_token`、`token_type`、`expires_in`）时，THE Auth_Module SHALL 将 `access_token` 存储到 `localStorage` 并跳转到主界面
4. WHEN 登录请求返回 HTTP 401 时，THE Auth_Module SHALL 在 Login_Page 显示"邮箱或密码错误"的提示信息
5. WHEN 存储的 JWT 令牌已过期时，THE Auth_Module SHALL 清除本地令牌并将用户重定向到 Login_Page 重新登录
6. WHEN 用户点击"退出登录"按钮时，THE Auth_Module SHALL 清除 `localStorage` 中的令牌并重定向到 Login_Page
7. THE Auth_Module SHALL 从 JWT payload 中解析 `tenant_id` 字段并存储，供后续 API 请求使用

### 需求 3：组织架构树数据加载

**用户故事：** 作为监管人员，我希望左侧组织架构树展示从 GraphDB 获取的真实企业层级数据，以便了解集团的实际组织结构。

#### 验收标准

1. WHEN Frontend 主界面加载完成时，THE API_Client SHALL 向后端 `GET /org/tree` 请求当前租户的组织架构数据（此 API 需后端新增，见需求 13）
2. WHEN 后端返回组织架构数据时，THE Frontend SHALL 通过 DataAdapter（见需求 11）将数据转换为与现有 `ORG` 对象相同的树形结构（包含 `id`、`name`、`level`、`type`、`city`、`cash`、`debt`、`asset`、`guarantee`、`compliance`、`risk`、`has_children`、`children` 字段）
3. WHEN 组织架构数据加载成功时，THE Frontend SHALL 使用后端数据替换硬编码的 `ORG` 变量，并触发完整的界面重新渲染（包括左侧树、中央图谱、右侧面板、KPI 栏）
4. WHILE 组织架构数据正在加载时，THE Frontend SHALL 在左侧面板显示加载状态指示器（骨架屏或加载动画）
5. IF 组织架构数据加载失败，THEN THE Frontend SHALL 在左侧面板显示错误提示并提供"重试"按钮

### 需求 4：监管指标数据加载

**用户故事：** 作为监管人员，我希望7大领域的106个指标展示从后端计算的真实数值，以便基于真实数据做出监管决策。

#### 验收标准

1. WHEN 用户选中一个实体节点时，THE API_Client SHALL 向后端 `GET /indicators/{entity_id}` 请求该实体在7大领域下所有指标的计算值（此 API 需后端新增，见需求 13）
2. WHEN 后端返回指标数据时，THE Frontend SHALL 通过 DataAdapter（见需求 11）将每个指标的 `value`、`threshold`、`direction` 映射到现有的 `generateIndicators` 函数返回格式，指标状态（danger/warn/normal）由前端按现有红黄绿阈值逻辑计算（红：低于阈值；黄：阈值±10%；绿：高于阈值10%以上），后端不返回 `status` 字段
3. WHEN 指标数据加载成功时，THE Frontend SHALL 更新右侧 Domain_Panel 中对应领域的指标列表、评分、告警计数
4. WHEN 指标数据加载成功时，THE Frontend SHALL 更新中央 Entity_Graph 中节点的七瓣花（domain petals）颜色和告警徽章
5. IF 某个实体的指标数据请求失败，THEN THE Frontend SHALL 在该实体的 Domain_Panel 中显示"数据加载失败"提示，同时保留其他已加载实体的数据
6. THE Frontend SHALL 对已加载的指标数据进行本地缓存（以实体 ID 为键），缓存有效期为 5 分钟，过期后下次选中该实体时重新请求后端数据

### 需求 5：穿透式钻取集成

**用户故事：** 作为监管人员，我希望双击实体节点时通过后端 Drill API 获取下级数据，实现真实的穿透式钻取（集团→二级→三级→四级→五级SPV）。

#### 验收标准

1. WHEN 用户双击 Entity_Graph 中一个有子节点的实体时（根据后端返回的 `has_children` 标志判定），THE Frontend SHALL 调用后端 API 获取该实体的下级子实体列表
2. WHEN 后端返回子实体列表时，THE Frontend SHALL 更新 `drillPath` 数组、`currentNode` 变量，并触发 `renderAll()` 重新渲染整个界面
3. WHEN 用户点击面包屑导航中的某一层级时，THE Frontend SHALL 回退到该层级；如果目标层级的组织架构数据已在本次会话内存中（之前加载过），则直接使用内存数据，不重新请求后端
4. WHEN 用户点击右侧面板的"钻入下级"按钮时，THE Frontend SHALL 执行与双击相同的穿透钻取逻辑
5. WHILE 穿透钻取数据正在加载时，THE Frontend SHALL 在中央画布区域显示加载指示器
6. IF 穿透钻取请求失败，THEN THE Frontend SHALL 显示通知提示"穿透查询失败，请重试"并保持当前视图不变

### 需求 6：实体关系图谱数据加载

**用户故事：** 作为监管人员，我希望中央画布的实体关系图谱展示从 GraphDB 获取的真实关系数据（控股、担保、资金流、借贷、外汇敞口），以便识别风险传导路径。

#### 验收标准

1. WHEN Frontend 完成穿透钻取或初始加载时，THE API_Client SHALL 向后端 `GET /org/{entity_id}/relations` 请求当前层级实体之间的关系数据（此 API 需后端新增，见需求 13）
2. WHEN 后端返回关系数据时，THE Frontend SHALL 通过 DataAdapter（见需求 11）将关系映射到现有的 `REL_TYPES` 类型（`hasSubsidiary`、`fundFlow`、`guarantee`、`borrowing`、`fxExposure`）
3. WHEN 关系数据加载成功时，THE Frontend SHALL 使用后端数据替换 `buildGraphData` 函数中硬编码的关系生成逻辑
4. THE Frontend SHALL 保留现有的力导向布局算法（`simStep`）和画布渲染逻辑（`drawGraph`），仅替换数据源
5. IF 关系数据加载失败，THEN THE Frontend SHALL 回退到仅显示控股关系（从组织架构树的 parent-child 关系推导）

### 需求 7：穿透路径查询

**用户故事：** 作为监管人员，我希望查看从指标到根因账户的完整穿透路径，以便追溯风险根源。

#### 验收标准

1. WHEN 用户在 Domain_Panel 中点击某个异常指标（status 为 danger 或 warn）时，THE Frontend SHALL 调用 `GET /drill/path/{indicator_id}` 获取完整穿透路径
2. WHEN 后端返回穿透路径数据（包含 `step`、`node_iri`、`node_type`、`node_label`）时，THE Frontend SHALL 通过 DataAdapter 从 `node_iri` 中提取最后一段作为前端节点 ID，在中央画布区域高亮显示路径涉及的节点和边
3. WHEN 穿透路径包含多个步骤时，THE Frontend SHALL 按步骤顺序（step 升序）以动画方式逐步高亮路径节点
4. IF 穿透路径查询返回空结果，THEN THE Frontend SHALL 显示通知"该指标暂无穿透路径数据"

### 需求 8：KPI 栏实时数据

**用户故事：** 作为监管人员，我希望顶部 KPI 栏展示从后端获取的实时汇总数据，以便快速掌握整体风险态势。

#### 验收标准

1. WHEN Frontend 完成组织架构数据加载时，THE Frontend SHALL 基于后端返回的实体数据计算 KPI 栏的6个指标（现金总额、资产规模、负债率、担保余额、指标异常数、合规评分）
2. WHEN 用户执行穿透钻取切换到新层级时，THE Frontend SHALL 重新计算并更新 KPI 栏数据，反映当前层级的汇总值
3. THE Frontend SHALL 保留现有的 KPI 栏渲染逻辑（`renderKPI` 函数），仅替换数据来源为后端返回的实体属性

### 需求 9：多租户支持

**用户故事：** 作为平台管理员，我希望不同央企集团的数据完全隔离，以便每个租户只能看到自己的监管数据。

#### 验收标准

1. WHEN 用户登录成功时，THE Auth_Module SHALL 从 JWT payload 中提取 `tenant_id` 并存储到全局状态
2. WHEN API_Client 发送任何业务请求时，THE Frontend SHALL 确保 JWT 令牌包含有效的 `tenant_id`，后端通过 SPARQL_Proxy 自动完成租户数据隔离（此能力后端已实现）
3. THE Frontend SHALL 在状态栏显示当前租户名称，通过 `GET /tenants/{tenant_id}` 获取租户详情
4. IF Frontend 收到 HTTP 403 响应（tenant_id 为空或无效），THEN THE Frontend SHALL 显示"租户信息无效，请重新登录"提示并重定向到 Login_Page

### 需求 10：加载状态与错误处理

**用户故事：** 作为平台用户，我希望在数据加载过程中看到清晰的状态反馈，在出错时看到有意义的错误提示，以便了解系统当前状态。

#### 验收标准

1. WHILE 任何 API 请求正在进行时，THE Frontend SHALL 在状态栏的"本体引擎"指示器旁显示加载动画
2. WHEN 所有 API 请求完成且无错误时，THE Frontend SHALL 将状态栏的"本体引擎"指示器恢复为"● 已连接"（绿色）
3. WHEN 后端服务不可达时，THE Frontend SHALL 将状态栏的"本体引擎"指示器变更为"● 已断开"（红色）
4. WHEN API 请求发生错误时，THE Frontend SHALL 使用现有的 `#notif` 通知条显示错误摘要，通知条在 3 秒后自动消失
5. THE Frontend SHALL 在控制台输出详细的错误日志（包含请求 URL、HTTP 状态码、错误详情），便于开发调试

### 需求 11：数据格式适配层

**用户故事：** 作为前端开发者，我希望有一个数据适配层将后端 API 返回的数据格式转换为前端现有渲染函数期望的格式，以便最小化对现有渲染代码的修改。

#### 验收标准

1. THE Frontend SHALL 提供一个 `DataAdapter` 模块，负责将后端 API 响应转换为前端数据结构
2. WHEN DataAdapter 接收到后端组织架构数据时，THE DataAdapter SHALL 将其转换为与现有 `ORG` 对象结构一致的嵌套树（包含 `id`、`name`、`level`、`type`、`city`、`cash`、`debt`、`asset`、`guarantee`、`compliance`、`risk`、`has_children`、`children` 字段）
3. WHEN DataAdapter 接收到后端指标数据时，THE DataAdapter SHALL 将其转换为与 `generateIndicators` 函数返回值一致的格式（按领域分组，每个指标包含 `id`、`name`、`unit`、`value`、`threshold`、`direction` 字段），并根据 `value`、`threshold`、`direction` 按红黄绿阈值逻辑计算 `status` 字段填入（红：低于阈值；黄：阈值±10%；绿：高于阈值10%以上）
4. WHEN DataAdapter 接收到后端关系数据时，THE DataAdapter SHALL 将其转换为 `graphEdges` 数组期望的格式（包含 `source`、`target`、`type` 字段，type 值为 `REL_TYPES` 中定义的键名）
5. IF 后端返回的数据缺少某个必需字段，THEN THE DataAdapter SHALL 使用合理的默认值填充（如 `risk` 默认为 `'lo'`，`compliance` 默认为 `0`，`children` 默认为空数组）

### 需求 12：溯源报告下载

**用户故事：** 作为监管人员，我希望点击"风险报告"按钮时下载后端生成的穿透溯源报告，以便留存审计证据。

#### 验收标准

1. WHEN 用户在右侧面板的 Domain_Panel 中选中一个具体指标后点击"风险报告"按钮时，THE Frontend SHALL 调用 `GET /drill/report/{indicator_id}` 下载溯源报告；IF 用户未选中任何指标，THEN "风险报告"按钮 SHALL 置灰不可点击
2. WHEN 后端返回 PDF 格式的报告时，THE Frontend SHALL 触发浏览器文件下载，文件名格式为 `drill_report_{indicator_id}.pdf`
3. WHEN 后端返回 JSON 格式的报告（reportlab 未安装的回退情况）时，THE Frontend SHALL 触发浏览器文件下载，文件名格式为 `drill_report_{indicator_id}.json`
4. WHILE 报告正在生成和下载时，THE Frontend SHALL 将"风险报告"按钮置为禁用状态并显示"生成中..."文字
5. IF 报告下载失败，THEN THE Frontend SHALL 恢复按钮状态并通过 `#notif` 通知条显示错误信息

### 需求 13：后端 API 扩展

**用户故事：** 作为前端应用，我需要后端提供组织架构查询、实体指标查询和实体关系查询三个新 API，以便前端能够获取穿透式监管所需的完整数据。

#### 验收标准

1. THE Backend SHALL 提供 `GET /org/tree` API，支持可选查询参数 `max_depth`（默认值为 2），返回当前租户的组织架构树（从集团根节点到指定深度），每个节点包含 `id`、`name`、`level`、`type`、`city`、`cash`、`debt`、`asset`、`guarantee`、`compliance`、`risk`、`has_children`、`children` 字段，数据通过 SPARQL 从 GraphDB 查询并按 `fibo:isSubsidiaryOf` 关系递归构建
2. THE Backend SHALL 提供 `GET /indicators/{entity_id}` API，返回指定实体在7大监管领域下所有指标的计算值，每个指标包含 `id`、`name`、`domain`、`unit`、`value`、`threshold`、`direction` 字段，指标值通过 SPARQL 从 GraphDB 中对应实体的属性计算得出
3. THE Backend SHALL 提供 `GET /org/{entity_id}/relations` API，返回指定实体与其同级实体之间的关系列表，每条关系包含 `source`、`target`、`type`（取值为 `hasSubsidiary`、`fundFlow`、`guarantee`、`borrowing`、`fxExposure` 之一）字段，数据通过 SPARQL 查询 GraphDB 中的 RDF 关系三元组
4. ALL 三个新 API SHALL 通过 JWT 认证保护（使用 `get_current_user` 依赖），并通过 SPARQL_Proxy 自动注入租户上下文
5. ALL 三个新 API SHALL 在 SPARQL 查询失败时返回 HTTP 500 并附带结构化错误信息（包含 `detail` 字段）
