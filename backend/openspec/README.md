# OpenSpec 配置

本目录包含 DRP 项目的 OpenAPI 规范配置和验证工具。

## 目录结构

- `config/` - OpenSpec 配置文件
- `schemas/` - 共享的 OpenAPI 组件定义
- `scripts/` - 验证和生成脚本
- `tests/` - OpenAPI 规范测试

## 使用指南

### 1. 生成 OpenAPI 规范

```bash
# 生成 OpenAPI 规范文件
python -m openspec.scripts.generate_openapi

# 生成并验证规范
python -m openspec.scripts.validate_openapi
```

### 2. 验证 API 实现

```bash
# 运行 OpenAPI 规范测试
pytest openspec/tests/ -v

# 使用 schemathesis 进行属性测试
schemathesis run --checks all http://localhost:8000/openapi.json
```

### 3. 开发规范

1. **API 设计优先**: 先定义 OpenAPI 规范，再实现代码
2. **版本控制**: 每次 API 变更都要更新规范版本
3. **向后兼容**: 保持 API 向后兼容性
4. **文档完整**: 所有端点必须有完整的文档和示例

## 规范要求

### 必须包含的字段

1. **info**: API 基本信息
2. **servers**: API 服务器地址
3. **paths**: 所有 API 端点定义
4. **components**: 共享的 schemas、parameters、responses
5. **security**: 安全方案定义
6. **tags**: API 分组标签

### 响应规范

1. 所有成功响应必须包含 `200` 或 `201` 状态码
2. 错误响应必须包含 `4xx` 或 `5xx` 状态码
3. 每个端点必须定义至少一个错误响应
4. 响应体必须使用定义好的 schema

### 请求规范

1. 路径参数必须定义在路径中
2. 查询参数必须有默认值或可选标记
3. 请求体必须使用定义好的 schema
4. 必须定义请求的 content-type