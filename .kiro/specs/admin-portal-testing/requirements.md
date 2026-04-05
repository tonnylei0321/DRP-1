# 需求文档：后端管理平台测试体系

## 简介

为 DRP 后端管理平台（`frontend/` 目录）建立完整的自动化测试体系，覆盖单元测试、集成测试、端到端测试和冒烟测试四个层级。项目当前零测试覆盖，需从零搭建测试基础设施并逐步覆盖所有核心模块。

## 术语表

- **Admin_Portal**：DRP 后端管理平台前端应用，基于 React 19 + TypeScript + Vite 构建
- **API_Client**：`frontend/src/api/client.ts` 中封装的 HTTP 通信模块，包含认证、租户、用户、审计、映射、ETL、数据质量等 API 调用
- **UI_Component_Library**：`frontend/src/components/ui.tsx` 中的自定义深色主题组件集合（Btn、Card、Modal、Input、Badge、Spinner、ErrorBox、EmptyState、PageHeader）
- **Test_Runner**：Vitest 测试运行器，用于执行单元测试和集成测试
- **RTL**：React Testing Library，用于组件渲染和交互测试
- **E2E_Runner**：Playwright 浏览器自动化测试框架，用于端到端测试
- **Mock_Server**：使用 MSW（Mock Service Worker）或 Vitest 内置 mock 模拟后端 API 响应
- **Dashboard_Module**：`frontend/src/dashboard/` 目录下的监管看板模块，包含 D3 可视化、WebSocket 实时事件、国际化等
- **Page_Component**：`frontend/src/pages/` 目录下的页面级组件，每个页面包含 API 调用、状态管理和用户交互逻辑
- **Coverage_Reporter**：Vitest 内置的代码覆盖率报告工具，基于 Istanbul 或 V8

## 需求

### 需求 1：测试基础设施搭建

**用户故事：** 作为开发者，我希望项目具备完整的测试基础设施配置，以便能够立即编写和运行各层级测试。

#### 验收标准

1. THE Admin_Portal SHALL 在 `package.json` 中包含 Vitest、React Testing Library（`@testing-library/react`、`@testing-library/jest-dom`、`@testing-library/user-event`）、jsdom 和 MSW 作为开发依赖
2. THE Admin_Portal SHALL 在 `package.json` 中包含 Playwright（`@playwright/test`）作为开发依赖
3. THE Admin_Portal SHALL 包含 `vitest.config.ts` 配置文件，指定 jsdom 作为测试环境、覆盖率收集范围为 `src/` 目录、排除 `node_modules` 和测试文件本身
4. THE Admin_Portal SHALL 包含 `playwright.config.ts` 配置文件，指定基础 URL、浏览器列表和截图策略
5. THE Admin_Portal SHALL 在 `package.json` 的 `scripts` 中包含 `test`（运行单元测试）、`test:coverage`（生成覆盖率报告）、`test:e2e`（运行端到端测试）命令
6. THE Admin_Portal SHALL 包含 `src/test/setup.ts` 全局测试配置文件，初始化 `@testing-library/jest-dom` 扩展匹配器和 MSW 服务器的 `beforeAll`/`afterEach`/`afterAll` 生命周期钩子
7. THE Admin_Portal SHALL 包含 `src/test/mocks/handlers.ts` 文件，为以下 API 端点定义默认 mock 响应处理器：`/auth/login`、`/auth/users/*`、`/auth/roles/*`、`/auth/audit-logs`、`/tenants/*`、`/mappings/generate`、`/mappings`、`/mappings/*/approve`、`/mappings/*/reject`、`/etl/jobs`、`/etl/sync`、`/etl/quality/*`
8. THE Admin_Portal SHALL 包含 `src/test/mocks/server.ts` 文件，使用 MSW 的 `setupServer` 创建 mock 服务器实例

### 需求 2：API 客户端单元测试

**用户故事：** 作为开发者，我希望 API 客户端模块有完整的单元测试，以便确保 HTTP 请求构造、Token 管理和错误处理逻辑正确。

#### 验收标准

1. WHEN `setToken` 被调用时，THE API_Client SHALL 将 token 存储到 `localStorage` 的 `drp_token` 键中，且后续请求的 `Authorization` 头包含 `Bearer <token>`
2. WHEN `clearToken` 被调用时，THE API_Client SHALL 从 `localStorage` 中移除 `drp_token` 键，且后续请求不包含 `Authorization` 头
3. WHEN 后端返回 HTTP 状态码 >= 400 时，THE API_Client SHALL 抛出包含状态码和响应文本的 Error 对象
4. WHEN 后端返回 HTTP 204 No Content 时，THE API_Client SHALL 返回 `undefined` 而非尝试解析 JSON
5. WHEN `authApi.login` 被调用时，THE API_Client SHALL 向 `/auth/login` 发送 POST 请求，请求体包含 `email` 和 `password` 字段
6. WHEN `tenantsApi.create` 被调用时，THE API_Client SHALL 向 `/tenants` 发送 POST 请求，请求体包含 `name` 字段
7. WHEN `auditApi.list` 被调用且传入分页和过滤参数时，THE API_Client SHALL 将 `page`、`per_page`、`event_type` 参数正确拼接为 URL 查询字符串
8. WHEN `mappingApi.reject` 被调用时，THE API_Client SHALL 向 `/mappings/{id}/reject` 发送 PUT 请求，请求体包含 `reason` 字段
9. FOR ALL 包含请求体的 API 方法调用（POST/PUT），THE API_Client SHALL 在请求头中包含 `Content-Type: application/json`
10. WHEN API 请求因网络超时而失败时，THE API_Client SHALL 抛出包含超时信息的 Error 对象，以便调用方区分网络超时与服务端错误
11. WHEN 后端返回 HTTP 401 Unauthorized 时，THE API_Client SHALL 自动调用 `clearToken` 清除本地 Token 并触发跳转到登录页

### 需求 3：UI 组件库单元测试

**用户故事：** 作为开发者，我希望共享 UI 组件库有完整的单元测试，以便确保组件渲染正确且交互行为符合预期。

#### 验收标准

1. WHEN `Btn` 组件以 `variant="primary"` 渲染时，THE UI_Component_Library SHALL 渲染一个包含 `btn-primary` CSS 类名的按钮元素
2. WHEN `Btn` 组件以 `variant="danger"` 渲染时，THE UI_Component_Library SHALL 渲染一个包含 `btn-danger` CSS 类名的按钮元素
3. WHEN `Btn` 组件的 `onClick` 回调被触发时，THE UI_Component_Library SHALL 调用传入的回调函数恰好一次
4. WHEN `Modal` 组件渲染时，THE UI_Component_Library SHALL 显示标题文本和子内容，且点击关闭按钮时调用 `onClose` 回调
5. WHEN `Input` 组件传入 `label` 属性时，THE UI_Component_Library SHALL 渲染一个包含该标签文本的 `<label>` 元素
6. WHEN `Badge` 组件以 `variant="success"` 渲染时，THE UI_Component_Library SHALL 渲染一个包含 `badge-success` CSS 类名的 `<span>` 元素
7. WHEN `ErrorBox` 组件渲染时，THE UI_Component_Library SHALL 显示传入的错误消息文本
8. WHEN `EmptyState` 组件渲染时，THE UI_Component_Library SHALL 显示传入的提示消息文本
9. WHEN `Spinner` 组件渲染时，THE UI_Component_Library SHALL 显示"加载中..."文本
10. WHEN `Card` 组件渲染时，THE UI_Component_Library SHALL 将子元素包裹在包含 `card` CSS 类名的容器中

### 需求 4：页面组件集成测试

**用户故事：** 作为开发者，我希望每个页面组件有集成测试，以便验证页面级别的 API 调用、数据渲染和用户交互流程正确。

#### 验收标准

1. WHEN LoginPage 渲染时，THE Page_Component SHALL 显示邮箱和密码输入框、登录按钮、SAML SSO 按钮和 OIDC 按钮
2. WHEN 用户在 LoginPage 提交有效凭据时，THE Page_Component SHALL 调用 `authApi.login`，成功后调用 `setToken` 并触发 `onLogin` 回调
3. IF LoginPage 登录请求失败，THEN THE Page_Component SHALL 显示包含错误信息的 ErrorBox 组件
4. WHEN UsersPage 渲染时，THE Page_Component SHALL 调用 `usersApi.list` 并在表格中显示用户列表，包含邮箱、用户名、全名、状态和创建时间列
5. WHEN 用户在 UsersPage 点击"新建用户"按钮时，THE Page_Component SHALL 显示包含邮箱、用户名、全名和密码输入框的 Modal 对话框
6. WHEN 用户在 UsersPage 提交新建用户表单时，THE Page_Component SHALL 调用 `usersApi.create` 并在成功后刷新用户列表
7. WHEN 用户在 UsersPage 点击"删除"按钮时，THE Page_Component SHALL 弹出自定义确认 Modal（而非原生 `window.confirm`），用户点击确认后调用 `usersApi.delete` 并刷新用户列表
7a. WHEN 用户在 UsersPage 删除确认 Modal 中点击"取消"时，THE Page_Component SHALL 关闭 Modal 且用户列表保持不变
8. WHEN RolesPage 渲染时，THE Page_Component SHALL 调用 `rolesApi.list` 并显示角色列表，每个角色显示名称、描述和权限数量
9. WHEN 用户在 RolesPage 选择一个角色时，THE Page_Component SHALL 在右侧面板显示该角色的权限树复选框列表
10. WHEN AuditPage 渲染时，THE Page_Component SHALL 调用 `auditApi.list` 并在表格中显示审计日志，包含事件类型、用户ID、资源、IP地址和时间列
11. WHEN 用户在 AuditPage 选择事件类型过滤器时，THE Page_Component SHALL 以新的 `event_type` 参数重新调用 `auditApi.list`
12. WHEN 用户在 AuditPage 点击"导出 CSV"按钮时，THE Page_Component SHALL 生成包含当前过滤条件下当前页数据的所有日志字段的 CSV 文件并触发下载，且 UI 上应标注导出范围为"当前页"
13. WHEN DdlUploadPage 用户上传 SQL 文件或粘贴 DDL 文本并点击"生成映射建议"时，THE Page_Component SHALL 调用 `mappingApi.generate` 并在右侧面板显示映射结果表格
14. WHEN MappingsPage 渲染时，THE Page_Component SHALL 调用 `mappingApi.list` 并将映射按 `pending` 和已审核状态分组显示
15. WHEN 用户在 MappingsPage 点击"确认"按钮时，THE Page_Component SHALL 调用 `mappingApi.approve` 并刷新列表
16. WHEN 用户在 MappingsPage 点击"拒绝"按钮时，THE Page_Component SHALL 弹出原因输入 Modal，用户填写拒绝原因并点击确认后调用 `mappingApi.reject`（请求体包含 `reason` 字段）并刷新列表；用户点击取消时 Modal 关闭且列表保持不变
17. WHEN EtlPage 渲染时，THE Page_Component SHALL 调用 `etlApi.list` 并在表格中显示 ETL 任务列表，包含任务ID、类型、状态、写入三元组数、耗时和错误信息列
18. WHEN TenantsPage 渲染时，THE Page_Component SHALL 调用 `tenantsApi.list` 并在表格中显示租户列表
19. WHEN 用户在 TenantsPage 提交新建租户表单时，THE Page_Component SHALL 调用 `tenantsApi.create` 并在成功后刷新租户列表
20. WHEN QualityPage 渲染时，THE Page_Component SHALL 调用 `tenantsApi.list` 获取租户列表，选择第一个租户后调用 `qualityApi.get` 显示质量评分
21. WHEN GroupsPage 渲染时，THE Page_Component SHALL 显示包含"开发中"提示信息的 EmptyState 组件
22. WHEN 用户在 LoginPage 点击 SAML SSO 按钮时，THE Page_Component SHALL 触发 URL 跳转到 SSO 认证端点

### 需求 5：监管看板模块测试

**用户故事：** 作为开发者，我希望监管看板模块有专项测试，以便验证 D3 可视化渲染、WebSocket 实时事件和国际化切换功能正确。

#### 验收标准

1. WHEN `t` 函数以 `lang='zh'` 和有效 key 调用时，THE Dashboard_Module SHALL 返回对应的中文翻译字符串
2. WHEN `t` 函数以 `lang='en'` 和有效 key 调用时，THE Dashboard_Module SHALL 返回对应的英文翻译字符串
3. WHEN `t` 函数以不存在的 key 调用时，THE Dashboard_Module SHALL 返回 key 本身作为 fallback
4. FOR ALL 在 `STRINGS.zh` 中定义的 key，THE Dashboard_Module SHALL 在 `STRINGS.en` 中也存在对应的 key（中英文翻译键完整性）
5. WHEN `useRiskEvents` hook 接收到有效的 `tenantId` 时，THE Dashboard_Module SHALL 创建 WebSocket 连接到 `{WS_URL}?tenant_id={tenantId}`
6. WHEN WebSocket 连接成功建立时，THE Dashboard_Module SHALL 将 `status` 设置为 `'connected'`
7. WHEN WebSocket 接收到类型为 `risk_event` 的消息时，THE Dashboard_Module SHALL 将事件添加到 `events` 数组头部，并为事件添加 `timestamp` 字段
8. WHEN `events` 数组长度超过 200 时，THE Dashboard_Module SHALL 截断数组保留最新的 200 条事件
9. WHEN WebSocket 连接关闭或发生错误时，THE Dashboard_Module SHALL 将 `status` 设置为 `'disconnected'`
10. WHEN `tenantId` 为 `null` 时，THE Dashboard_Module SHALL 不创建 WebSocket 连接
10a. WHEN WebSocket 连接意外断开时，THE Dashboard_Module SHALL 自动尝试重新连接，并在重连期间将 `status` 设置为 `'reconnecting'`
11. WHEN `HierarchyGraph` 组件渲染时，THE Dashboard_Module SHALL 在 SVG 元素中创建 D3 层级树节点和连线
12. WHEN `ForceGraph` 组件渲染时，THE Dashboard_Module SHALL 在 SVG 元素中创建力导向图节点和连线
13. WHEN `HudPanel` 组件渲染时，THE Dashboard_Module SHALL 显示节点标签、类型、风险等级和属性列表
14. WHEN `RiskTicker` 组件接收到非空 `events` 数组时，THE Dashboard_Module SHALL 显示风险事件滚动播报条
15. WHEN `LayerFilterBar` 组件的按钮被点击时，THE Dashboard_Module SHALL 调用 `onChange` 回调并传入对应的图层过滤值
16. WHEN Dashboard 主组件渲染时，THE Dashboard_Module SHALL 显示 Topbar、层级图（HierarchyGraph）和检查器面板（HudPanel）

### 需求 6：应用级路由与认证集成测试

**用户故事：** 作为开发者，我希望应用级路由和认证流程有集成测试，以便验证登录状态管理、页面切换和退出登录功能正确。

#### 验收标准

1. WHEN 用户未登录（无 token）时，THE Admin_Portal SHALL 渲染 LoginPage 而非主布局
2. WHEN 用户登录成功后，THE Admin_Portal SHALL 渲染包含侧边栏导航和主内容区的主布局
3. WHEN 用户点击侧边栏导航项时，THE Admin_Portal SHALL 切换主内容区显示对应的页面组件
4. WHEN 用户点击"退出登录"按钮时，THE Admin_Portal SHALL 调用 `clearToken` 并返回 LoginPage
5. THE Admin_Portal SHALL 在侧边栏中显示全部 10 个导航项（监管看板、用户管理、用户组、角色权限、审计日志、DDL上传、映射审核、ETL监控、租户管理、数据质量）
6. WHEN 用户 Token 过期导致 API 返回 401 后重新登录成功时，THE Admin_Portal SHALL 恢复用户之前所在的页面路由，而非始终跳转到默认首页

### 需求 7：端到端测试

**用户故事：** 作为开发者，我希望有 Playwright 端到端测试覆盖核心用户流程，以便在真实浏览器环境中验证完整的用户交互路径。

#### 验收标准

1. WHEN E2E 测试启动时，THE E2E_Runner SHALL 使用 mock API 服务器拦截所有后端请求，不依赖真实后端
2. WHEN 用户在登录页输入有效凭据并点击登录时，THE E2E_Runner SHALL 验证页面跳转到主布局且侧边栏可见
3. WHEN 用户在用户管理页点击"新建用户"、填写表单并提交时，THE E2E_Runner SHALL 验证新用户出现在列表中
4. WHEN 用户在审计日志页选择事件类型过滤器时，THE E2E_Runner SHALL 验证表格内容根据过滤条件更新
5. WHEN 用户在 DDL 上传页粘贴 DDL 文本并点击生成时，THE E2E_Runner SHALL 验证映射建议表格出现在右侧面板
6. WHEN 用户在映射审核页点击"确认"或"拒绝"按钮时，THE E2E_Runner SHALL 验证映射状态更新
7. WHEN 用户依次点击所有侧边栏导航项时，THE E2E_Runner SHALL 验证每个页面正确渲染且无控制台错误
8. WHEN EtlPage 在 E2E 环境中加载时，THE E2E_Runner SHALL 验证页面成功渲染且 ETL 任务表格可见
9. WHEN 用户在 E2E 环境中完成租户创建流程（点击新建 → 填写表单 → 提交）时，THE E2E_Runner SHALL 验证新租户出现在租户列表中
10. WHEN 用户在 E2E 环境中的数据质量页面切换租户选择时，THE E2E_Runner SHALL 验证质量评分数据根据所选租户更新

### 需求 8：测试覆盖率与质量门禁

**用户故事：** 作为开发者，我希望有明确的覆盖率目标和质量门禁，以便持续监控测试质量并防止覆盖率退化。

#### 验收标准

1. WHEN `test:coverage` 命令执行完成时，THE Coverage_Reporter SHALL 生成包含行覆盖率、分支覆盖率和函数覆盖率的报告
2. THE Admin_Portal SHALL 在 Vitest 配置中设置覆盖率阈值：行覆盖率 >= 80%、分支覆盖率 >= 70%、函数覆盖率 >= 80%
3. IF 覆盖率低于配置的阈值，THEN THE Test_Runner SHALL 以非零退出码终止，标记测试失败
4. THE Coverage_Reporter SHALL 将 `node_modules`、`test/`、`*.d.ts`、`main.tsx` 排除在覆盖率统计之外
5. THE Admin_Portal SHALL 在 `vitest.config.ts` 中配置覆盖率报告输出格式为 `text`（终端输出）和 `lcov`（CI 集成）

### 需求 9：冒烟测试

**用户故事：** 作为开发者，我希望有一组最小化的冒烟测试，以便在每次部署前快速验证核心功能的可用性。

#### 验收标准

1. THE Admin_Portal SHALL 包含以 `*.smoke.test.ts` 命名的冒烟测试文件，可通过 `test:smoke` 命令单独运行（`test:smoke` 脚本通过 Vitest 的 `include` 配置仅匹配 `*.smoke.test.ts` 文件）
2. WHEN 冒烟测试执行时，THE Test_Runner SHALL 验证登录流程（输入凭据 → 提交 → 进入主布局）在 5 秒内完成
3. WHEN 冒烟测试执行时，THE Test_Runner SHALL 验证用户管理页能成功加载并显示用户列表
4. WHEN 冒烟测试执行时，THE Test_Runner SHALL 验证审计日志页能成功加载并显示日志表格
5. WHEN 冒烟测试执行时，THE Test_Runner SHALL 验证侧边栏导航的所有页面切换均不产生渲染错误
6. THE Admin_Portal SHALL 在 `package.json` 中包含 `test:smoke` 脚本命令，通过 Vitest 的 `include` 配置仅运行 `*.smoke.test.ts` 命名的测试文件
7. WHEN 冒烟测试执行时，THE Test_Runner SHALL 验证监管看板页面能成功加载并渲染 SVG 图谱元素
