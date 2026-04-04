# DRP OpenSpec Makefile

.PHONY: help openspec generate validate test docs clean

# 默认目标
help:
	@echo "DRP OpenSpec 管理工具"
	@echo ""
	@echo "可用命令:"
	@echo "  make openspec       - 生成并验证 OpenAPI 规范"
	@echo "  make generate       - 生成 OpenAPI 规范"
	@echo "  make validate       - 验证 OpenAPI 规范"
	@echo "  make test           - 运行 OpenAPI 测试"
	@echo "  make docs           - 生成 API 文档"
	@echo "  make clean          - 清理生成的文件"
	@echo ""

# 完整 OpenSpec 流程
openspec: generate validate test
	@echo "✅ OpenSpec 流程完成"

# 生成 OpenAPI 规范
generate:
	@echo "🚀 生成 OpenAPI 规范..."
	cd backend && python -m openspec.scripts.generate_openapi
	@echo "✅ OpenAPI 规范生成完成"

# 验证 OpenAPI 规范
validate:
	@echo "🔍 验证 OpenAPI 规范..."
	cd backend && python -m openspec.scripts.validate_openapi
	@echo "✅ OpenAPI 规范验证完成"

# 运行 OpenAPI 测试
test:
	@echo "🧪 运行 OpenAPI 测试..."
	cd backend && python -m pytest openspec/tests/ -v
	@echo "✅ OpenAPI 测试完成"

# 生成 API 文档
docs:
	@echo "📚 生成 API 文档..."
	@echo "文档可通过以下方式访问:"
	@echo "  - Swagger UI: http://localhost:8000/api/docs"
	@echo "  - OpenAPI 规范: backend/openspec/openapi.json"
	@echo "  - OpenAPI 规范: backend/openspec/openapi.yaml"
	@echo "✅ 文档信息已显示"

# 清理生成的文件
clean:
	@echo "🧹 清理生成的文件..."
	rm -f backend/openspec/openapi.json
	rm -f backend/openspec/openapi.yaml
	@echo "✅ 清理完成"

# CI/CD 集成命令
ci-test:
	@echo "🏗️  运行 CI/CD 测试..."
	make validate
	make test
	@echo "✅ CI/CD 测试完成"

ci-generate:
	@echo "🏗️  CI/CD 生成规范..."
	make generate
	@echo "✅ CI/CD 规范生成完成"

# 开发命令
dev:
	@echo "👨‍💻 开发模式..."
	@echo "启动开发服务器:"
	@echo "  cd backend && uvicorn drp.main:app --reload --port 8000"
	@echo ""
	@echo "生成规范: make generate"
	@echo "验证规范: make validate"
	@echo "运行测试: make test"