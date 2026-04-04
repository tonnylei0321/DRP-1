# DRP OpenSpec 开发指南

## 概述

OpenSpec 是 DRP 项目的 API 规范框架，基于 OpenAPI 3.1.0 标准。它确保所有 API 端点都有完整的文档、一致的响应格式和严格的验证。

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -e ".[dev]"
```

### 2. 生成 OpenAPI 规范

```bash
# 使用 Makefile
make generate

# 或直接运行脚本
python -m openspec.scripts.generate_openapi
```

### 3. 验证规范

```bash
make validate
```

### 4. 运行测试

```bash
make test
```

### 5. 完整流程

```bash
make openspec  # 生成 + 验证 + 测试
```

## 开发规范

### API 设计原则

1. **设计优先**: 先定义 OpenAPI 规范，再实现代码
2. **一致性**: 所有 API 遵循相同的模式和约定
3. **版本控制**: API 版本在 URL 或 header 中明确标识
4. **向后兼容**: 避免破坏性变更，使用扩展字段

### 端点规范

#### 路径命名
- 使用小写字母和连字符: `/api/v1/user-profiles`
- 资源使用复数形式: `/tenants`, `/users`
- 嵌套资源: `/tenants/{tenant_id}/projects`

#### HTTP 方法
- `GET`: 获取资源
- `POST`: 创建资源
- `PUT`: 更新整个资源
- `PATCH`: 部分更新资源
- `DELETE`: 删除资源

#### 状态码
- `200`: 成功获取
- `201`: 创建成功
- `204`: 删除成功（无内容）
- `400`: 请求错误
- `401`: 未认证
- `403`: 无权限
- `404`: 资源不存在
- `422`: 验证错误
- `500`: 服务器错误

### 请求/响应规范

#### 请求头
```yaml
Content-Type: application/json
Authorization: Bearer {token}
X-Request-ID: {uuid}
```

#### 响应格式
```json
{
  "data": {},  // 成功时返回数据
  "error": {   // 错误时返回错误信息
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  },
  "meta": {    // 分页等信息
    "page": 1,
    "total": 100
  }
}
```

#### 分页
```json
{
  "data": [],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  },
  "links": {
    "self": "/api/v1/resources?page=1",
    "next": "/api/v1/resources?page=2",
    "prev": null,
    "first": "/api/v1/resources?page=1",
    "last": "/api/v1/resources?page=5"
  }
}
```

### 错误处理

#### 错误响应格式
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "请求的资源不存在",
    "details": {
      "resource_id": "123",
      "resource_type": "tenant"
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_123456"
  }
}
```

#### 标准错误码
- `VALIDATION_ERROR`: 请求数据验证失败
- `RESOURCE_NOT_FOUND`: 资源不存在
- `PERMISSION_DENIED`: 权限不足
- `AUTHENTICATION_FAILED`: 认证失败
- `INTERNAL_ERROR`: 服务器内部错误

## FastAPI 集成指南

### 1. 路由定义

```python
from fastapi import APIRouter, Depends, HTTPException
from drp.openspec.decorators import validate_request, validate_response

router = APIRouter(prefix="/api/v1", tags=["用户管理"])

@router.post("/users", status_code=201)
@validate_request(UserCreate)
@validate_response(UserResponse)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    """创建新用户"""
    try:
        return await service.create_user(user_data)
    except UserExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

### 2. Pydantic 模型

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    """创建用户请求"""
    email: EmailStr = Field(..., description="用户邮箱")
    name: str = Field(..., min_length=1, max_length=100, description="用户姓名")
    password: str = Field(..., min_length=8, description="密码")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "张三",
                "password": "securepassword123"
            }
        }

class UserResponse(BaseModel):
    """用户响应"""
    id: str = Field(..., description="用户ID")
    email: EmailStr = Field(..., description="用户邮箱")
    name: str = Field(..., description="用户姓名")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
```

### 3. 依赖注入

```python
from fastapi import Depends
from drp.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_user_service(
    session: AsyncSession = Depends(get_session)
) -> UserService:
    return UserService(session=session)
```

## 测试指南

### 单元测试

```python
import pytest
from fastapi.testclient import TestClient

def test_create_user(client: TestClient):
    """测试创建用户"""
    user_data = {
        "email": "test@example.com",
        "name": "测试用户",
        "password": "password123"
    }
    
    response = client.post("/api/v1/users", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert data["email"] == user_data["email"]
    assert data["name"] == user_data["name"]
```

### 集成测试

```python
@pytest.mark.integration
def test_user_workflow(client: TestClient):
    """测试用户完整工作流"""
    # 1. 创建用户
    user_data = {...}
    create_response = client.post("/api/v1/users", json=user_data)
    assert create_response.status_code == 201
    
    user_id = create_response.json()["id"]
    
    # 2. 获取用户
    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200
    
    # 3. 更新用户
    update_data = {"name": "新名字"}
    update_response = client.patch(f"/api/v1/users/{user_id}", json=update_data)
    assert update_response.status_code == 200
    
    # 4. 删除用户
    delete_response = client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204
```

### OpenAPI 规范测试

```python
def test_openapi_spec(client: TestClient):
    """测试 OpenAPI 规范"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    spec = response.json()
    assert "openapi" in spec
    assert "paths" in spec
    assert "/api/v1/users" in spec["paths"]
```

## CI/CD 集成

### 预提交钩子

在 `.git/hooks/pre-commit` 中添加:

```bash
#!/bin/bash
cd backend
python -m openspec.scripts.validate_openapi
if [ $? -ne 0 ]; then
    echo "❌ OpenAPI 规范验证失败"
    exit 1
fi
```

### GitHub Actions

已配置自动验证工作流，在每次推送时:
1. 生成 OpenAPI 规范
2. 验证规范完整性
3. 运行规范测试
4. 运行属性测试

## 工具和命令

### 常用命令

```bash
# 生成规范
make generate

# 验证规范
make validate

# 运行测试
make test

# 完整流程
make openspec

# 清理生成文件
make clean

# CI/CD 测试
make ci-test
```

### 脚本说明

- `openspec/scripts/generate_openapi.py`: 生成 OpenAPI 规范
- `openspec/scripts/validate_openapi.py`: 验证规范完整性
- `openspec/tests/test_openapi.py`: OpenAPI 规范测试

## 故障排除

### 常见问题

1. **规范验证失败**
   - 检查路径参数是否在路径中定义
   - 检查响应状态码是否完整
   - 检查 schema 引用是否正确

2. **测试失败**
   - 确保所有依赖已安装
   - 检查测试数据是否符合 schema
   - 查看详细的错误信息

3. **生成文件缺失**
   - 运行 `make generate` 重新生成
   - 检查文件权限
   - 查看脚本输出日志

### 调试技巧

```bash
# 详细输出
python -m openspec.scripts.generate_openapi --verbose

# 只验证不生成
python -m openspec.scripts.validate_openapi --strict

# 运行特定测试
pytest openspec/tests/test_openapi.py::test_openapi_spec_exists -v
```

## 扩展和定制

### 添加自定义验证

在 `openspec/scripts/validate_openapi.py` 中添加新的验证函数:

```python
def validate_custom_rules(spec: dict) -> list[str]:
    """自定义验证规则"""
    errors = []
    # 添加验证逻辑
    return errors
```

### 扩展基础配置

修改 `openspec/config/openapi-base.json` 添加:
- 新的服务器配置
- 安全方案
- 共享组件
- 标签定义

### 集成其他工具

1. **Redoc**: 生成漂亮的 API 文档
2. **Swagger UI**: 交互式 API 文档
3. **Postman**: API 测试和文档
4. **Insomnia**: API 设计和测试