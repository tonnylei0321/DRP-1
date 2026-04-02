# Hook 机制

<cite>
**本文档引用的文件**
- [settings.json](file://settings.json)
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts)
- [hooks/skill-activation-prompt.sh](file://hooks/skill-activation-prompt.sh)
- [hooks/post-tool-use-tracker.sh](file://hooks/post-tool-use-tracker.sh)
- [hooks/package.json](file://hooks/package.json)
- [skills/skill-rules.json](file://skills/skill-rules.json)
- [skills/skill-developer/HOOK_MECHANISMS.md](file://skills/skill-developer/HOOK_MECHANISMES.md)
- [skills/skill-developer/TRIGGER_TYPES.md](file://skills/skill-developer/TRIGGER_TYPES.md)
- [skills/skill-developer/TROUBLESHOOTING.md](file://skills/skill-developer/TROUBLESHOOTING.md)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构概览](#架构概览)
5. [详细组件分析](#详细组件分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考虑](#性能考虑)
8. [调试指南](#调试指南)
9. [结论](#结论)

## 简介

Hook 机制是 Claude Code 中实现智能技能自动激活的核心系统。该系统采用两阶段架构设计，通过 UserPromptSubmit Hook（主动建议）和 Post-Tool-Use Hook（工具使用后跟踪）实现完整的技能触发和执行流程。

该机制的核心价值在于：
- **智能化技能推荐**：基于用户提示词内容自动识别相关技能
- **强制性执行控制**：确保关键技能在特定操作前得到执行
- **无侵入式集成**：通过钩子机制无缝嵌入现有工作流程
- **可扩展的触发器系统**：支持关键词、意图模式、文件路径等多种触发方式

## 项目结构

Hook 机制的实现分布在多个关键目录中：

```mermaid
graph TB
subgraph "配置层"
Settings[settings.json]
Rules[skill-rules.json]
end
subgraph "Hook 层"
Bash[Shell 脚本]
TS[TypeScript 钩子]
end
subgraph "技能层"
Skills[技能定义]
Triggers[触发器配置]
end
Settings --> Bash
Bash --> TS
Rules --> TS
TS --> Skills
Skills --> Triggers
```

**图表来源**
- [settings.json](file://settings.json#L13-L35)
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L1-L133)
- [skills/skill-rules.json](file://skills/skill-rules.json#L1-L250)

**章节来源**
- [settings.json](file://settings.json#L1-L37)
- [hooks/package.json](file://hooks/package.json#L1-L17)

## 核心组件

### 两阶段 Hook 架构

Hook 机制采用双阶段设计，确保技能触发的准确性和有效性：

```mermaid
sequenceDiagram
participant User as 用户
participant Claude as Claude Code
participant Hook1 as UserPromptSubmit Hook
participant Hook2 as Post-Tool-Use Hook
participant Skills as 技能系统
User->>Claude : 提交提示词
Claude->>Hook1 : 触发 UserPromptSubmit
Hook1->>Hook1 : 分析提示词内容
Hook1->>Claude : 输出技能建议
Claude->>Skills : 执行技能
Skills->>Claude : 返回技能结果
User->>Claude : 发起工具调用
Claude->>Hook2 : 触发 Post-Tool-Use
Hook2->>Hook2 : 检查执行条件
Hook2->>Claude : 允许或阻止执行
```

**图表来源**
- [skills/skill-developer/HOOK_MECHANISMS.md](file://skills/skill-developer/HOOK_MECHANISMS.md#L15-L120)

### 触发器类型系统

系统支持四种主要触发器类型，每种都有其特定的应用场景：

| 触发器类型 | 匹配方式 | 应用场景 | 性能特征 |
|------------|----------|----------|----------|
| 关键词触发器 | 字符串包含匹配 | 明确主题识别 | O(n) 时间复杂度 |
| 意图模式触发器 | 正则表达式匹配 | 隐含意图检测 | O(m) 正则匹配开销 |
| 文件路径触发器 | Glob 模式匹配 | 基于位置的激活 | O(p) 模式编译开销 |
| 内容模式触发器 | 文件内容正则匹配 | 技术栈识别 | O(f) 文件读取开销 |

**章节来源**
- [skills/skill-developer/TRIGGER_TYPES.md](file://skills/skill-developer/TRIGGER_TYPES.md#L15-L306)

## 架构概览

### 整体系统架构

```mermaid
graph TB
subgraph "用户交互层"
UserPrompt[用户提示词]
ToolCall[工具调用]
end
subgraph "Hook 管理层"
HookManager[Hook 管理器]
EventDispatcher[事件分发器]
end
subgraph "执行引擎"
UserPromptHook[UserPromptSubmit Hook]
PostToolHook[Post-Tool-Use Hook]
SkillEngine[技能引擎]
end
subgraph "配置存储"
ConfigStore[配置存储]
SkillRules[技能规则]
SessionState[会话状态]
end
UserPrompt --> HookManager
ToolCall --> HookManager
HookManager --> EventDispatcher
EventDispatcher --> UserPromptHook
EventDispatcher --> PostToolHook
UserPromptHook --> SkillEngine
PostToolHook --> SkillEngine
SkillEngine --> ConfigStore
ConfigStore --> SessionState
```

**图表来源**
- [settings.json](file://settings.json#L13-L35)
- [skills/skill-developer/HOOK_MECHANISMS.md](file://skills/skill-developer/HOOK_MECHANISMS.md#L1-L307)

### 数据流架构

```mermaid
flowchart TD
Start([Hook 启动]) --> ReadInput[读取标准输入]
ReadInput --> ParseJSON[解析 JSON 输入]
ParseJSON --> LoadConfig[加载配置文件]
LoadConfig --> ApplyTriggers[应用触发器规则]
ApplyTriggers --> KeywordMatch{关键词匹配?}
KeywordMatch --> |是| AddToResults[添加到结果集]
KeywordMatch --> |否| IntentMatch{意图模式匹配?}
IntentMatch --> |是| AddToResults
IntentMatch --> |否| FilePathMatch{文件路径匹配?}
FilePathMatch --> |是| CheckContent{检查内容模式?}
FilePathMatch --> |否| NoMatch[无匹配]
CheckContent --> ContentMatch{内容匹配?}
ContentMatch --> |是| AddToResults
ContentMatch --> |否| NoMatch
AddToResults --> GenerateOutput[生成输出]
NoMatch --> GenerateOutput
GenerateOutput --> ExitCode{确定退出码}
ExitCode --> |UserPromptSubmit| Stdout[标准输出]
ExitCode --> |PreToolUse Allow| Stdout
ExitCode --> |PreToolUse Block| Stderr[标准错误]
Stdout --> InjectContext[注入上下文]
Stderr --> ShowMessage[显示消息]
InjectContext --> End([Hook 结束])
ShowMessage --> End
```

**图表来源**
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L36-L127)
- [skills/skill-developer/HOOK_MECHANISMS.md](file://skills/skill-developer/HOOK_MECHANISMS.md#L170-L189)

## 详细组件分析

### UserPromptSubmit Hook 组件

UserPromptSubmit Hook 是两阶段 Hook 架构中的第一阶段，负责在用户提交提示词时提供技能建议。

#### 核心功能实现

```mermaid
classDiagram
class HookInput {
+string session_id
+string transcript_path
+string cwd
+string permission_mode
+string hook_event_name
+string prompt
}
class SkillRule {
+string type
+string enforcement
+string priority
+PromptTriggers promptTriggers
}
class PromptTriggers {
+string[] keywords
+string[] intentPatterns
}
class MatchedSkill {
+string name
+string matchType
+SkillRule config
}
class SkillActivationHook {
+main() Promise~void~
+matchKeywords(prompt, keywords) boolean
+matchIntentPatterns(prompt, patterns) boolean
+generateOutput(matchedSkills) string
+processExitCode() void
}
HookInput --> SkillActivationHook : "输入"
SkillRule --> MatchedSkill : "配置"
PromptTriggers --> SkillRule : "包含"
MatchedSkill --> SkillActivationHook : "结果"
```

**图表来源**
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L5-L34)

#### 执行流程详解

```mermaid
sequenceDiagram
participant User as 用户
participant Bash as Bash 包装器
participant TS as TypeScript Hook
participant FS as 文件系统
participant Output as 输出系统
User->>Bash : 提交提示词
Bash->>TS : 传递标准输入
TS->>FS : 读取 skill-rules.json
FS-->>TS : 返回配置数据
TS->>TS : 解析 JSON 输入
TS->>TS : 匹配关键词触发器
TS->>TS : 匹配意图模式触发器
TS->>TS : 组合匹配结果
TS->>Output : 输出格式化消息
Output-->>User : 显示技能建议
Note over TS : 退出码始终为 0
```

**图表来源**
- [hooks/skill-activation-prompt.sh](file://hooks/skill-activation-prompt.sh#L1-L6)
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L36-L127)

#### 关键实现特性

1. **多级匹配策略**：同时支持关键词和意图模式匹配，提高识别准确性
2. **优先级分组**：按 critical → high → medium → low 顺序组织技能建议
3. **非阻塞设计**：始终返回退出码 0，确保不影响用户交互
4. **格式化输出**：提供统一的消息格式，便于 Claude 处理

**章节来源**
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L1-L133)
- [hooks/skill-activation-prompt.sh](file://hooks/skill-activation-prompt.sh#L1-L6)

### Post-Tool-Use Hook 组件

Post-Tool-Use Hook 是第二阶段 Hook，负责在工具使用后进行跟踪和验证。

#### 核心功能实现

```mermaid
classDiagram
class ToolInfo {
+string tool_name
+string session_id
+ToolInput tool_input
}
class ToolInput {
+string file_path
+string old_string
+string new_string
}
class RepoDetector {
+detect_repo(file_path) string
+get_build_command(repo) string
+get_tsc_command(repo) string
}
class PostToolHook {
+main() Promise~void~
+extractToolInfo() ToolInfo
+detectRepo(file_path) string
+logEditedFile(file_path, repo) void
+storeCommands(repo, buildCmd, tscCmd) void
+exitCleanly(code) void
}
ToolInfo --> PostToolHook : "输入"
ToolInput --> ToolInfo : "包含"
RepoDetector --> PostToolHook : "使用"
```

**图表来源**
- [hooks/post-tool-use-tracker.sh](file://hooks/post-tool-use-tracker.sh#L12-L141)

#### 执行流程详解

```mermaid
flowchart TD
Start([工具调用完成]) --> ReadToolInfo[读取工具信息]
ReadToolInfo --> ValidateTool{验证工具类型}
ValidateTool --> |编辑工具| Continue[继续处理]
ValidateTool --> |其他工具| Skip[跳过处理]
Continue --> DetectRepo[检测仓库类型]
DetectRepo --> RepoKnown{仓库类型已知?}
RepoKnown --> |未知| Skip
RepoKnown --> |已知| LogFile[记录编辑文件]
LogFile --> UpdateRepos[更新受影响仓库列表]
UpdateRepos --> GetCommands[获取构建命令]
GetCommands --> StoreCommands[存储命令信息]
StoreCommands --> Cleanup[清理临时文件]
Cleanup --> Exit[正常退出]
Skip --> Exit
Exit --> End([Hook 结束])
```

**图表来源**
- [hooks/post-tool-use-tracker.sh](file://hooks/post-tool-use-tracker.sh#L8-L178)

#### 关键实现特性

1. **智能仓库检测**：根据文件路径自动识别前端、后端、数据库等仓库类型
2. **构建命令管理**：自动检测并存储各仓库的构建和类型检查命令
3. **缓存机制**：使用会话 ID 创建独立的缓存目录，避免冲突
4. **多包管理**：支持 monorepo 结构，正确识别各个包的边界

**章节来源**
- [hooks/post-tool-use-tracker.sh](file://hooks/post-tool-use-tracker.sh#L1-L178)

### 触发器系统组件

触发器系统是 Hook 机制的核心，提供了灵活的技能激活策略。

#### 触发器配置结构

```mermaid
erDiagram
SKILL_RULES {
string version
string description
json skills
json notes
}
SKILL {
string type
string enforcement
string priority
string description
json promptTriggers
json fileTriggers
}
PROMPT_TRIGGERS {
string[] keywords
string[] intentPatterns
}
FILE_TRIGGERS {
string[] pathPatterns
string[] pathExclusions
string[] contentPatterns
}
SKILL_RULES ||--o{ SKILL : "包含"
SKILL ||--|| PROMPT_TRIGGERS : "包含"
SKILL ||--|| FILE_TRIGGERS : "包含"
```

**图表来源**
- [skills/skill-rules.json](file://skills/skill-rules.json#L1-L250)

#### 触发器匹配算法

```mermaid
flowchart TD
Input[输入内容] --> CheckKeywords{检查关键词}
CheckKeywords --> |匹配| AddResult[添加到结果]
CheckKeywords --> |不匹配| CheckIntent{检查意图模式}
CheckIntent --> |匹配| AddResult
CheckIntent --> |不匹配| CheckFilePath{检查文件路径}
CheckFilePath --> |匹配| CheckContent{检查文件内容}
CheckFilePath --> |不匹配| NoMatch[无匹配]
CheckContent --> |匹配| AddResult
CheckContent --> |不匹配| NoMatch
AddResult --> PriorityGroup[按优先级分组]
NoMatch --> PriorityGroup
PriorityGroup --> Output[生成输出]
Output --> End([结束])
```

**图表来源**
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L57-L78)

**章节来源**
- [skills/skill-rules.json](file://skills/skill-rules.json#L1-L250)
- [skills/skill-developer/TRIGGER_TYPES.md](file://skills/skill-developer/TRIGGER_TYPES.md#L1-L306)

## 依赖关系分析

### 外部依赖关系

```mermaid
graph TB
subgraph "外部工具"
NodeJS[Node.js 运行时]
Bash[Bash Shell]
JQ[jq JSON处理器]
TSC[TypeScript Compiler]
TSX[TSX 运行时]
end
subgraph "内部模块"
HookTS[Hook TypeScript 模块]
HookSh[Hook Shell 脚本]
Config[配置模块]
Utils[工具函数]
end
subgraph "系统接口"
FS[文件系统]
STDIO[标准输入输出]
ENV[环境变量]
end
NodeJS --> HookTS
Bash --> HookSh
JQ --> HookSh
TSC --> HookTS
TSX --> HookTS
HookTS --> Config
HookSh --> Config
HookTS --> Utils
HookSh --> Utils
HookTS --> FS
HookSh --> FS
HookTS --> STDIO
HookSh --> STDIO
HookTS --> ENV
HookSh --> ENV
```

**图表来源**
- [hooks/package.json](file://hooks/package.json#L11-L15)
- [hooks/skill-activation-prompt.sh](file://hooks/skill-activation-prompt.sh#L1-L6)

### 内部模块依赖

```mermaid
graph LR
subgraph "Hook 层"
UserPromptHook[UserPromptSubmit Hook]
PostToolHook[Post-Tool-Use Hook]
end
subgraph "配置层"
SkillRules[技能规则]
Settings[设置配置]
end
subgraph "工具层"
FileUtil[文件工具]
JSONUtil[JSON 工具]
RegexUtil[正则工具]
end
UserPromptHook --> SkillRules
PostToolHook --> SkillRules
UserPromptHook --> Settings
PostToolHook --> Settings
UserPromptHook --> FileUtil
PostToolHook --> FileUtil
UserPromptHook --> JSONUtil
PostToolHook --> JSONUtil
UserPromptHook --> RegexUtil
PostToolHook --> RegexUtil
```

**图表来源**
- [settings.json](file://settings.json#L13-L35)
- [skills/skill-rules.json](file://skills/skill-rules.json#L1-L250)

**章节来源**
- [hooks/package.json](file://hooks/package.json#L1-L17)

## 性能考虑

### 性能基准指标

系统针对不同 Hook 类型设定了明确的性能目标：

| Hook 类型 | 性能目标 | 主要瓶颈 | 优化策略 |
|-----------|----------|----------|----------|
| UserPromptSubmit | < 100ms | JSON 解析、正则匹配 | 缓存编译后的正则表达式 |
| PreToolUse | < 200ms | 文件系统访问、正则匹配 | 懒加载、模式预编译 |
| Post-Tool-Use | < 50ms | I/O 操作 | 批量写入、异步处理 |

### 性能优化策略

#### 编译时优化

1. **正则表达式缓存**：将常用的正则表达式编译结果缓存到内存中
2. **文件路径预编译**：对 Glob 模式进行预编译，减少运行时开销
3. **配置文件缓存**：缓存 skill-rules.json 到内存，避免重复读取

#### 运行时优化

1. **短路求值**：在匹配失败时尽早退出，避免不必要的计算
2. **增量更新**：只在配置文件变化时重新加载
3. **并发处理**：对独立的匹配任务进行并行处理

#### 内存管理

```mermaid
flowchart TD
Start([Hook 启动]) --> LoadConfig[加载配置]
LoadConfig --> CheckCache{检查缓存}
CheckCache --> |有缓存| UseCache[使用缓存配置]
CheckCache --> |无缓存| ParseConfig[解析配置]
ParseConfig --> CacheConfig[缓存配置]
UseCache --> ProcessInput[处理输入]
CacheConfig --> ProcessInput
ProcessInput --> OptimizeRegex[优化正则表达式]
OptimizeRegex --> ProcessTriggers[处理触发器]
ProcessTriggers --> GenerateOutput[生成输出]
GenerateOutput --> End([Hook 结束])
```

**图表来源**
- [skills/skill-developer/HOOK_MECHANISMS.md](file://skills/skill-developer/HOOK_MECHANISMS.md#L260-L301)

**章节来源**
- [skills/skill-developer/HOOK_MECHANISMS.md](file://skills/skill-developer/HOOK_MECHANISMS.md#L260-L301)

## 调试指南

### 常见问题诊断

#### UserPromptSubmit Hook 问题

| 问题症状 | 可能原因 | 诊断步骤 | 解决方案 |
|----------|----------|----------|----------|
| 无技能建议 | 关键词不匹配 | 检查 skill-rules.json 中的 keywords | 添加更多关键词变体 |
| 意图模式不工作 | 正则表达式过于严格 | 使用 regex101.com 测试模式 | 放宽模式范围 |
| JSON 解析错误 | 配置文件语法错误 | 使用 jq 验证 JSON 格式 | 修正 JSON 语法 |
| 性能问题 | 触发器过多 | 分析匹配模式复杂度 | 精简触发器配置 |

#### Post-Tool-Use Hook 问题

| 问题症状 | 可能原因 | 诊断步骤 | 解决方案 |
|----------|----------|----------|----------|
| 仓库识别错误 | 文件路径不匹配 | 检查 detect_repo 函数逻辑 | 调整仓库检测规则 |
| 构建命令缺失 | 缺少构建配置 | 检查 package.json 和 tsconfig.json | 添加缺失的配置文件 |
| 缓存目录权限问题 | 文件系统权限不足 | 检查 .claude 目录权限 | 修复目录权限设置 |
| 性能延迟 | I/O 操作过多 | 分析日志中的时间戳 | 实施异步写入 |

### 调试命令集合

#### UserPromptSubmit 调试

```bash
# 基础测试命令
echo '{"session_id":"test","prompt":"your test prompt"}' | \
  npx tsx .claude/hooks/skill-activation-prompt.ts

# 验证配置文件
cat .claude/skills/skill-rules.json | jq .

# 检查 Hook 注册状态
cat .claude/settings.json | jq '.hooks.UserPromptSubmit'

# 性能测试
time echo '{"prompt":"test"}' | npx tsx .claude/hooks/skill-activation-prompt.ts
```

#### Post-Tool-Use 调试

```bash
# 基础测试命令
cat <<'EOF' | npx tsx .claude/hooks/post-tool-use-tracker.sh
{
  "session_id": "test",
  "tool_name": "Edit",
  "tool_input": {"file_path": "/path/to/test/file.ts"}
}
EOF

# 检查缓存目录
ls -la .claude/tsc-cache/

# 查看编辑文件日志
cat .claude/tsc-cache/default/edited-files.log

# 性能测试
time cat <<'EOF' | npx tsx .claude/hooks/post-tool-use-tracker.sh
{"tool_name":"Edit","tool_input":{"file_path":"test.ts"}}
EOF
```

### 错误处理机制

```mermaid
flowchart TD
Start([Hook 执行]) --> TryBlock[Try 块执行]
TryBlock --> Success{执行成功?}
Success --> |是| NormalExit[正常退出]
Success --> |否| CatchError[Catch 错误]
CatchError --> LogError[记录错误日志]
LogError --> CheckExitCode{检查退出码}
CheckExitCode --> |UserPromptSubmit| Exit0[退出码 0]
CheckExitCode --> |PreToolUse| Exit1[退出码 1]
CheckExitCode --> |其他| Exit2[退出码 2]
Exit0 --> End([结束])
Exit1 --> End
Exit2 --> End
```

**图表来源**
- [hooks/skill-activation-prompt.ts](file://hooks/skill-activation-prompt.ts#L123-L132)

**章节来源**
- [skills/skill-developer/TROUBLESHOOTING.md](file://skills/skill-developer/TROUBLESHOOTING.md#L1-L515)

## 结论

Hook 机制通过精心设计的两阶段架构，实现了智能、高效且可扩展的技能自动激活系统。该系统的关键优势包括：

1. **智能化触发**：通过多种触发器类型实现精确的技能识别
2. **无侵入式设计**：保持与现有工作流程的完全兼容性
3. **可扩展性**：支持动态配置和未来功能增强
4. **性能优化**：针对不同 Hook 类型设定明确的性能目标

随着系统的持续演进，可以预期在以下方面获得进一步改进：
- 动态规则热重载
- 更智能的技能依赖管理
- 条件化执行控制
- 完善的使用统计分析

这套 Hook 机制为 Claude Code 的技能系统奠定了坚实的技术基础，为未来的 AI 协作开发提供了强大的支撑。