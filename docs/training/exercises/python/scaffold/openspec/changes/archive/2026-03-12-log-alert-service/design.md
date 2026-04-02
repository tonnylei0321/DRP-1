# Design: 日志清洗告警服务

## 技术栈
- FastAPI + Pydantic v2
- Python 标准库：threading.Lock、collections.defaultdict、uuid、datetime

## 架构概览

```
HTTP 请求
  └── routers/logs.py          路由层，Depends 注入服务
        ├── LogService          日志存储与统计
        └── AlertService        告警判断与派发
```

## 关键设计决策

### 1. 原子性策略
先执行告警副作用，再原子提交统计。webhook 失败降级（alerts_failed 计数），不阻断日志摄取。

理由：日志摄取优先级高于告警下游可靠性，避免因告警服务不稳定导致日志丢失。

### 2. 窗口聚合
基于日志 timestamp（非系统时间）判断窗口，key 为 (service, level)。

理由：避免时钟漂移影响；同一服务同一级别独立计算，不同服务互不干扰。

### 3. 并发安全
LogService 统计写入和 AlertService 窗口状态均使用 threading.Lock 保护。
LogService 移除无界 _logs 列表，改用 _total 计数器，避免内存无限增长。

### 4. 模型类型
level 使用 Literal["ERROR", "WARN", "INFO"] + field_validator(mode="before") 大小写标准化。
OpenAPI schema 自动生成枚举约束，客户端代码生成可直接使用。

### 5. 服务单例
路由模块级单例 + Depends 注入，便于测试通过 override 替换实现。
测试隔离通过 autouse fixture 调用 reset() 实现，不依赖重建实例。

## 配置项

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| WEBHOOK_URL | https://example.com/webhook | 告警目标地址 |
| ALERT_WINDOW_MINUTES | 5 | 窗口抑制时长（分钟） |
| ALLOWED_ORIGINS | http://localhost:3000 | CORS 允许域名，逗号分隔 |
| ENVIRONMENT | dev | 环境标识，写入 webhook payload |
| HOST | 0.0.0.0 | 服务监听地址 |
| PORT | 8000 | 服务监听端口 |
