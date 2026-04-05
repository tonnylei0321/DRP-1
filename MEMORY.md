# 项目记忆（Project Memory）

- [2026-04-04] 决策: 前端原型使用原生HTML+JS+Canvas（非Vue3），当前为原型集成阶段，后续产品化迁移到Vue3+TypeScript
- [2026-04-04] 决策: API响应格式使用裸数据（不包装{code,message,data}），与现有drill API保持一致，后续统一
- [2026-04-04] 决策: 指标状态（红/黄/绿）由前端计算，后端只返回value/threshold/direction，不返回status字段
- [2026-04-04] 决策: 组织架构API GET /org/tree 支持max_depth参数分层加载（默认2级），避免一次性加载全部层级
- [2026-04-04] 决策: JWT token存储在localStorage，前端JWT解析仅用于UI展示不验证签名，后续考虑HttpOnly Cookie
- [2026-04-04] 接口: 后端域名映射：银行账户/资金集中→fund, 债务融资→debt, 决策风险→guarantee, 票据→derivative, 结算(前半)→finbiz, 结算(后半>=056)→invest, 国资委考核→overseas
- [2026-04-04] 接口: 新增3个后端API: GET /org/tree, GET /indicators/{entity_id}, GET /org/{entity_id}/relations，entity_id参数校验正则^[a-zA-Z0-9_-]+$防SPARQL注入
- [2026-04-04] 修复: 6个Kiro hooks的schema不合规——fileSaved应为fileEdited, agentTurnEnd应为agentStop, userPromptSubmit应为promptSubmit, shellCommand应为runCommand, filePattern应为patterns数组
- [2026-04-04] 踩坑: SSH推送GitHub需要先将公钥添加到GitHub Settings→SSH keys，且需要ssh-add加载密钥到agent
- [2026-04-04] 偏好: 用户要求hooks放在~/.kiro/hooks/（用户级，所有项目生效），修改时先复制到项目级.kiro/hooks/修改再同步回去
- [2026-04-04] 偏好: 用户要求进度快照自动更新（progress-on-task-save + progress-on-session-end两个hooks）
- [2026-04-05] 踩坑: Kiro hooks 项目级(.kiro/hooks/)和用户级(~/.kiro/hooks/)同时存在相同hook会导致每个hook触发两次，应只保留一边。建议用户级保留全部，项目级清空
- [2026-04-05] 踩坑: promptSubmit类型的hook（如progress-on-session-end、project-bootstrap）每条用户消息都会触发，不是死循环但会造成响应变慢的感觉
