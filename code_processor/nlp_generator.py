# -*- coding: utf-8 -*-
"""
NLP Generator - LLM 增强的自然语言生成器

为代码元素生成业务意图描述，而非简单的 AST 翻译。
参考 mcp-graphrag 的 NLPGenerator 设计，增加 LLM 增强能力。
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .base_parser import CodeElement, ElementType

logger = logging.getLogger(__name__)


class NLPGenerator:
    """
    LLM 增强的自然语言生成器

    为代码元素生成业务意图描述，支持两种模式：
    1. 规则推断模式：基于命名模式和业务术语推断
    2. LLM 增强模式：调用 LLM 生成更丰富的描述
    """

    def __init__(self, llm_client: Optional[Any] = None, enable_llm: bool = False):
        """
        初始化 NLP 生成器

        Args:
            llm_client: LLM 客户端实例（可选）
            enable_llm: 是否启用 LLM 增强
        """
        self.llm_client = llm_client
        self.enable_llm = enable_llm and llm_client is not None
        self.business_terms = self._load_business_terms()
        self.framework_terms = self._load_framework_terms()
        self.annotation_meanings = self._load_annotation_meanings()
        self.decorator_meanings = self._load_decorator_meanings()

    def _load_business_terms(self) -> Dict[str, str]:
        """
        加载业务术语映射

        将常见的类名后缀映射到业务描述
        """
        return {
            # 通用模式
            'Service': '服务类，提供业务逻辑处理',
            'Controller': '控制器，处理 HTTP 请求',
            'Repository': '数据访问层，负责数据持久化',
            'Factory': '工厂类，负责对象创建',
            'Builder': '构建器，用于复杂对象的构建',
            'Handler': '处理器，处理特定类型的事件或请求',
            'Manager': '管理器，协调多个组件的工作',
            'Validator': '验证器，负责数据验证',
            'Parser': '解析器，负责数据解析',
            'Generator': '生成器，负责内容生成',
            'Adapter': '适配器，用于接口转换',
            'Wrapper': '包装器，封装底层实现',
            'Proxy': '代理类，提供间接访问',
            'Decorator': '装饰器，动态添加功能',
            'Observer': '观察者，监听状态变化',
            'Strategy': '策略类，封装可替换的算法',
            'Command': '命令类，封装请求为对象',
            'Visitor': '访问者，分离数据结构和操作',
            # Java/Spring 特定
            'Entity': '实体类，表示数据模型',
            'DTO': '数据传输对象，用于层间数据传输',
            'VO': '视图对象，用于展示层数据',
            'DAO': '数据访问对象，封装数据库操作',
            'Mapper': '映射器，负责对象转换',
            'Config': '配置类，管理系统配置',
            'Configuration': '配置类，管理系统配置',
            # Python 特定
            'Mixin': '混入类，提供可复用的功能',
            'Client': '客户端，封装外部服务调用',
            'Provider': '提供者，提供特定资源或服务',
            'Plugin': '插件，提供可扩展的功能',
            'Middleware': '中间件，处理请求/响应管道',
            # 测试相关
            'Test': '测试类，用于单元测试',
            'TestCase': '测试用例，包含测试方法',
            'Mock': '模拟对象，用于测试隔离',
            'Stub': '桩对象，提供预设响应',
            'Fixture': '测试夹具，提供测试数据',
        }

    def _load_framework_terms(self) -> Dict[str, str]:
        """加载框架术语映射"""
        return {
            # Python 框架
            'flask': 'Flask Web 框架',
            'django': 'Django Web 框架',
            'fastapi': 'FastAPI 异步 Web 框架',
            'sqlalchemy': 'SQLAlchemy ORM 框架',
            'pydantic': 'Pydantic 数据验证库',
            'pytest': 'pytest 测试框架',
            'celery': 'Celery 分布式任务队列',
            'redis': 'Redis 缓存',
            'asyncio': 'Python 异步 IO 库',
            # Java 框架
            'springframework': 'Spring 框架',
            'hibernate': 'Hibernate ORM 框架',
            'mybatis': 'MyBatis 持久层框架',
            'junit': 'JUnit 测试框架',
            'jackson': 'Jackson JSON 处理库',
            # JavaScript 框架
            'react': 'React 前端框架',
            'vue': 'Vue.js 前端框架',
            'express': 'Express.js Web 框架',
            'nestjs': 'NestJS 后端框架',
            'typescript': 'TypeScript 类型系统',
        }

    def _load_annotation_meanings(self) -> Dict[str, str]:
        """加载 Java 注解含义"""
        return {
            'Override': '方法重写',
            'Deprecated': '已废弃',
            'Component': 'Spring 组件',
            'Service': 'Spring 服务',
            'Repository': 'Spring 数据访问',
            'Controller': 'Spring 控制器',
            'RestController': 'Spring REST 控制器',
            'Autowired': 'Spring 自动装配',
            'RequestMapping': '请求映射',
            'GetMapping': 'GET 请求映射',
            'PostMapping': 'POST 请求映射',
            'Entity': 'JPA 实体',
            'Table': 'JPA 表映射',
            'Transactional': '事务管理',
            'Test': '测试方法',
        }

    def _load_decorator_meanings(self) -> Dict[str, str]:
        """加载 Python 装饰器含义"""
        return {
            'property': '属性访问器',
            'staticmethod': '静态方法',
            'classmethod': '类方法',
            'abstractmethod': '抽象方法',
            'dataclass': '数据类',
            'pytest.fixture': '测试夹具',
            'pytest.mark': '测试标记',
            'app.route': 'Flask 路由',
            'router.get': 'FastAPI GET 路由',
            'router.post': 'FastAPI POST 路由',
        }

    def generate_class_description(self, element: CodeElement) -> str:
        """
        生成类的业务意图描述

        Args:
            element: 类元素

        Returns:
            业务意图描述
        """
        if self.enable_llm:
            return self._generate_class_description_with_llm(element)
        return self._generate_class_description_by_rules(element)

    def _generate_class_description_by_rules(self, element: CodeElement) -> str:
        """基于规则生成类描述"""
        parts = []

        # 1. 推断类的作用
        purpose = self._infer_class_purpose(element.name)
        if purpose:
            parts.append(f"{element.name} 是一个{purpose}。")

        # 2. 分析继承关系
        extends = element.extra_attributes.get('extends')
        implements = element.extra_attributes.get('implements', [])
        if extends:
            parts.append(f"它继承自 {extends}。")
        if implements:
            parts.append(f"它实现了 {', '.join(implements)} 接口。")

        # 3. 分析注解/装饰器
        if element.annotations:
            annotation_desc = self._describe_annotations(element.annotations)
            if annotation_desc:
                parts.append(f"使用了 {annotation_desc}。")

        # 4. 分析方法
        methods = [c for c in element.children
                   if c.element_type in (ElementType.METHOD, ElementType.FUNCTION)]
        if methods:
            method_summary = self._summarize_methods(methods)
            if method_summary:
                parts.append(method_summary)

        # 5. 使用 docstring
        if element.docstring:
            # 取第一段作为补充
            first_para = element.docstring.split('\n\n')[0].strip()
            if first_para and len(first_para) < 200:
                parts.append(f"文档说明：{first_para}")

        return ' '.join(parts) if parts else f"{element.name} 类。"

    def _generate_class_description_with_llm(self, element: CodeElement) -> str:
        """使用 LLM 生成类描述"""
        # 构建上下文
        context = self._build_element_context(element)

        prompt = f"""请为以下代码类生成一段简洁的业务意图描述（2-3句话）。
描述应该解释这个类的职责、它在系统中的作用，以及它与其他组件的关系。
不要简单列出方法，而是解释这个类为什么存在、它解决什么问题。

{context}

请用中文回答，直接给出描述，不要有前缀。"""

        try:
            response = self.llm_client.generate(prompt)
            return response.strip()
        except Exception as e:
            logger.warning(f"LLM 生成失败，回退到规则模式: {e}")
            return self._generate_class_description_by_rules(element)

    def generate_method_description(self, element: CodeElement) -> str:
        """
        生成方法的业务意图描述

        Args:
            element: 方法元素

        Returns:
            业务意图描述
        """
        if self.enable_llm:
            return self._generate_method_description_with_llm(element)
        return self._generate_method_description_by_rules(element)

    def _generate_method_description_by_rules(self, element: CodeElement) -> str:
        """基于规则生成方法描述"""
        parts = []

        # 1. 推断方法作用
        purpose = self._infer_method_purpose(element.name, element.return_type)
        if purpose:
            parts.append(purpose)

        # 2. 参数说明
        if element.parameters:
            param_desc = self._describe_parameters(element.parameters)
            if param_desc:
                parts.append(param_desc)

        # 3. 返回值说明
        if element.return_type and element.return_type not in ('void', 'None'):
            return_desc = self._describe_return_type(element.return_type, element.name)
            if return_desc:
                parts.append(return_desc)

        # 4. 使用 docstring
        if element.docstring:
            first_line = element.docstring.split('\n')[0].strip()
            if first_line and len(first_line) < 100:
                parts.append(f"文档说明：{first_line}")

        return ' '.join(parts) if parts else f"{element.name} 方法。"

    def _generate_method_description_with_llm(self, element: CodeElement) -> str:
        """使用 LLM 生成方法描述"""
        context = self._build_element_context(element)

        prompt = f"""请为以下代码方法生成一段简洁的业务意图描述（1-2句话）。
描述应该解释这个方法做什么、为什么需要它、它的输入输出是什么。

{context}

请用中文回答，直接给出描述，不要有前缀。"""

        try:
            response = self.llm_client.generate(prompt)
            return response.strip()
        except Exception as e:
            logger.warning(f"LLM 生成失败，回退到规则模式: {e}")
            return self._generate_method_description_by_rules(element)

    def generate_module_description(self, element: CodeElement) -> str:
        """生成模块的业务意图描述"""
        parts = []

        # 模块名推断
        module_name = element.name
        if module_name.startswith('__'):
            parts.append(f"{module_name} 是一个特殊模块。")
        else:
            purpose = self._infer_module_purpose(module_name)
            if purpose:
                parts.append(f"{module_name} 模块{purpose}。")

        # 使用 docstring
        if element.docstring:
            first_para = element.docstring.split('\n\n')[0].strip()
            if first_para:
                parts.append(first_para)

        # 统计子元素
        classes = [c for c in element.children if c.element_type == ElementType.CLASS]
        functions = [c for c in element.children if c.element_type == ElementType.FUNCTION]
        if classes or functions:
            summary = []
            if classes:
                summary.append(f"{len(classes)} 个类")
            if functions:
                summary.append(f"{len(functions)} 个函数")
            parts.append(f"包含 {', '.join(summary)}。")

        return ' '.join(parts) if parts else f"{module_name} 模块。"

    def _infer_class_purpose(self, class_name: str) -> str:
        """推断类的作用"""
        name_lower = class_name.lower()

        # 检查业务术语
        for term, description in self.business_terms.items():
            if term.lower() in name_lower or name_lower.endswith(term.lower()):
                return description

        # 常见命名模式
        patterns = [
            (r'.*service$', '服务类，负责业务逻辑处理'),
            (r'.*controller$', '控制器，处理请求和响应'),
            (r'.*repository$', '数据访问层，负责数据持久化'),
            (r'.*dao$', '数据访问对象，封装数据库操作'),
            (r'.*entity$', '实体类，表示数据模型'),
            (r'.*model$', '模型类，表示数据结构'),
            (r'.*dto$', '数据传输对象'),
            (r'.*vo$', '视图对象'),
            (r'.*config.*$', '配置类'),
            (r'.*util.*$', '工具类'),
            (r'.*helper.*$', '辅助类'),
            (r'.*test.*$', '测试类'),
            (r'^test.*$', '测试类'),
            (r'.*exception$', '异常类'),
            (r'.*error$', '错误类'),
            (r'^abstract.*$', '抽象基类'),
            (r'^base.*$', '基类'),
            (r'^i[A-Z].*$', '接口'),
        ]

        for pattern, desc in patterns:
            if re.match(pattern, name_lower):
                return desc

        return ''

    def _infer_method_purpose(self, method_name: str, return_type: Optional[str]) -> str:
        """推断方法的作用"""
        name_lower = method_name.lower()

        # 常见方法命名模式
        patterns = [
            (r'^get[_]?(.+)$', '获取{}相关数据'),
            (r'^set[_]?(.+)$', '设置{}的值'),
            (r'^is[_]?(.+)$', '检查{}的状态'),
            (r'^has[_]?(.+)$', '检查是否有{}'),
            (r'^can[_]?(.+)$', '检查是否可以{}'),
            (r'^create[_]?(.+)$', '创建{}对象'),
            (r'^add[_]?(.+)$', '添加{}'),
            (r'^update[_]?(.+)$', '更新{}信息'),
            (r'^delete[_]?(.+)$', '删除{}'),
            (r'^remove[_]?(.+)$', '移除{}'),
            (r'^find[_]?(.+)$', '查找{}'),
            (r'^search[_]?(.+)$', '搜索{}'),
            (r'^query[_]?(.+)$', '查询{}'),
            (r'^load[_]?(.+)$', '加载{}'),
            (r'^save[_]?(.+)$', '保存{}'),
            (r'^parse[_]?(.+)$', '解析{}'),
            (r'^build[_]?(.+)$', '构建{}'),
            (r'^init[_]?(.+)$', '初始化{}'),
            (r'^validate[_]?(.+)$', '验证{}'),
            (r'^check[_]?(.+)$', '检查{}'),
            (r'^process[_]?(.+)$', '处理{}'),
            (r'^handle[_]?(.+)$', '处理{}'),
            (r'^convert[_]?(.+)$', '转换{}'),
            (r'^transform[_]?(.+)$', '转换{}'),
            (r'^format[_]?(.+)$', '格式化{}'),
            (r'^calculate[_]?(.+)$', '计算{}'),
            (r'^compute[_]?(.+)$', '计算{}'),
        ]

        for pattern, template in patterns:
            match = re.match(pattern, name_lower)
            if match:
                entity = self._extract_entity_name(match.group(1) if match.groups() else '')
                return template.format(entity) if entity else template.format('数据')

        # 根据返回类型推断
        if return_type:
            rt_lower = return_type.lower()
            if rt_lower in ('bool', 'boolean'):
                return '执行判断操作'
            elif rt_lower in ('void', 'none'):
                return '执行操作'
            elif 'list' in rt_lower or 'array' in rt_lower:
                return '获取列表数据'
            elif 'dict' in rt_lower or 'map' in rt_lower:
                return '获取映射数据'

        return ''

    def _infer_module_purpose(self, module_name: str) -> str:
        """推断模块的作用"""
        name_lower = module_name.lower()

        patterns = [
            ('__init__', '是包的初始化模块'),
            ('__main__', '是程序的入口模块'),
            ('config', '提供配置管理功能'),
            ('utils', '提供通用工具函数'),
            ('helpers', '提供辅助函数'),
            ('models', '定义数据模型'),
            ('views', '定义视图层'),
            ('controllers', '定义控制器'),
            ('services', '定义服务层'),
            ('repositories', '定义数据访问层'),
            ('tests', '包含测试代码'),
            ('cli', '提供命令行接口'),
            ('api', '定义 API 接口'),
        ]

        for pattern, desc in patterns:
            if pattern in name_lower:
                return desc

        return '提供相关功能'

    def _extract_entity_name(self, name_part: str) -> str:
        """从方法名中提取实体名称"""
        if not name_part:
            return ''

        # 将驼峰/下划线命名转换为可读名称
        # CamelCase -> camel case
        result = re.sub(r'([A-Z])', r' \1', name_part).strip().lower()
        # snake_case -> snake case
        result = result.replace('_', ' ')
        return result.strip()

    def _describe_annotations(self, annotations: List[str]) -> str:
        """描述注解/装饰器"""
        descriptions = []
        for annotation in annotations:
            # 清理注解名称
            clean_name = annotation.lstrip('@').split('(')[0]

            # 查找含义
            if clean_name in self.annotation_meanings:
                descriptions.append(f"{clean_name}（{self.annotation_meanings[clean_name]}）")
            elif clean_name in self.decorator_meanings:
                descriptions.append(f"{clean_name}（{self.decorator_meanings[clean_name]}）")
            else:
                descriptions.append(clean_name)

        return '、'.join(descriptions[:3])  # 限制数量

    def _describe_parameters(self, parameters: List[Dict[str, Any]]) -> str:
        """描述参数"""
        if not parameters:
            return ''

        param_names = [p.get('name', '') for p in parameters if p.get('name')]
        if len(param_names) <= 3:
            return f"接收 {', '.join(param_names)} 参数。"
        else:
            return f"接收 {len(param_names)} 个参数。"

    def _describe_return_type(self, return_type: str, method_name: str) -> str:
        """描述返回类型"""
        rt_lower = return_type.lower()

        if 'list' in rt_lower or 'array' in rt_lower:
            return '返回列表数据。'
        elif 'dict' in rt_lower or 'map' in rt_lower:
            return '返回映射数据。'
        elif 'bool' in rt_lower:
            return '返回布尔值。'
        elif 'str' in rt_lower or 'string' in rt_lower:
            return '返回字符串。'
        elif 'int' in rt_lower or 'long' in rt_lower:
            return '返回整数。'
        elif 'float' in rt_lower or 'double' in rt_lower:
            return '返回浮点数。'
        elif 'optional' in rt_lower:
            return '返回可选值。'

        return f'返回 {return_type} 类型数据。'

    def _summarize_methods(self, methods: List[CodeElement]) -> str:
        """总结方法列表"""
        if not methods:
            return ''

        # 分类方法
        getters = [m for m in methods if m.name.lower().startswith('get')]
        setters = [m for m in methods if m.name.lower().startswith('set')]
        handlers = [m for m in methods if 'handle' in m.name.lower() or 'process' in m.name.lower()]

        parts = []
        if getters:
            parts.append(f"{len(getters)} 个获取方法")
        if setters:
            parts.append(f"{len(setters)} 个设置方法")
        if handlers:
            parts.append(f"{len(handlers)} 个处理方法")

        other_count = len(methods) - len(getters) - len(setters) - len(handlers)
        if other_count > 0:
            parts.append(f"{other_count} 个其他方法")

        if parts:
            return f"提供 {', '.join(parts)}。"
        return ''

    def _build_element_context(self, element: CodeElement) -> str:
        """构建元素上下文信息"""
        lines = [
            f"名称: {element.name}",
            f"完整名称: {element.full_name}",
            f"类型: {element.element_type.value}",
        ]

        if element.file_path:
            lines.append(f"文件: {element.file_path}")

        if element.package:
            lines.append(f"包/模块: {element.package}")

        if element.docstring:
            lines.append(f"文档: {element.docstring[:500]}")

        if element.annotations:
            lines.append(f"注解/装饰器: {', '.join(element.annotations)}")

        extends = element.extra_attributes.get('extends')
        if extends:
            lines.append(f"继承: {extends}")

        implements = element.extra_attributes.get('implements', [])
        if implements:
            lines.append(f"实现: {', '.join(implements)}")

        if element.parameters:
            params = [f"{p.get('name', '')}:{p.get('type', '')}" for p in element.parameters]
            lines.append(f"参数: {', '.join(params)}")

        if element.return_type:
            lines.append(f"返回类型: {element.return_type}")

        # 子元素摘要
        if element.children:
            child_types = {}
            for child in element.children:
                t = child.element_type.value
                child_types[t] = child_types.get(t, 0) + 1
            summary = ', '.join([f"{v}个{k}" for k, v in child_types.items()])
            lines.append(f"子元素: {summary}")

        return '\n'.join(lines)
