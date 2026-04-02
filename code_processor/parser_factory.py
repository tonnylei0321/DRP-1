"""
Parser Factory

Auto-detects project language type and creates appropriate parsers.
Supports mixed-language project analysis.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Union

from .base_parser import BaseCodeParser, LanguageType, ProjectInfo
from .java_parser import JavaParser
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser, TypeScriptParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """Code parser factory class"""

    _parsers: Dict[LanguageType, Type[BaseCodeParser]] = {}

    _extension_mapping = {
        '.java': LanguageType.JAVA,
        '.py': LanguageType.PYTHON,
        '.js': LanguageType.JAVASCRIPT,
        '.jsx': LanguageType.JAVASCRIPT,
        '.ts': LanguageType.TYPESCRIPT,
        '.tsx': LanguageType.TYPESCRIPT,
    }

    _project_indicators = {
        LanguageType.JAVA: ['pom.xml', 'build.gradle', 'gradle.properties', 'src/main/java'],
        LanguageType.PYTHON: ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', '__init__.py'],
        LanguageType.JAVASCRIPT: ['package.json', 'node_modules', 'webpack.config.js'],
        LanguageType.TYPESCRIPT: ['tsconfig.json', 'package.json'],
    }

    @classmethod
    def register_parser(cls, language: LanguageType, parser_class: Type[BaseCodeParser]):
        """Register parser class"""
        cls._parsers[language] = parser_class
        logger.info(f"Registered {language.value} parser: {parser_class.__name__}")

    @classmethod
    def detect_project_language(cls, project_path: Union[str, Path]) -> LanguageType:
        """Auto-detect project main language type"""
        project_path = Path(project_path)

        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        language_scores = {lang: 0 for lang in LanguageType if lang != LanguageType.UNKNOWN}

        for language, indicators in cls._project_indicators.items():
            for indicator in indicators:
                indicator_path = project_path / indicator
                if indicator_path.exists():
                    language_scores[language] += 2
                    logger.debug(f"Found {language.value} indicator: {indicator}")

        file_counts = {lang: 0 for lang in LanguageType if lang != LanguageType.UNKNOWN}

        excluded_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache',
                        'target', 'build', 'dist', '.idea', '.vscode', 'venv',
                        '.venv', 'env', '.env', 'virtualenv', 'workspaces'}

        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                if not any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                    ext = file_path.suffix.lower()
                    if ext in cls._extension_mapping:
                        language = cls._extension_mapping[ext]
                        file_counts[language] += 1

        for language, count in file_counts.items():
            language_scores[language] += count * 0.1

        if not any(language_scores.values()):
            logger.warning(f"Cannot detect project language: {project_path}")
            return LanguageType.UNKNOWN

        detected_language = max(language_scores, key=language_scores.get)
        logger.info(f"Detected project language: {detected_language.value} (score: {language_scores[detected_language]:.1f})")

        return detected_language

    @classmethod
    def detect_mixed_languages(cls, project_path: Union[str, Path]) -> List[LanguageType]:
        """Detect all language types in project (mixed project)"""
        project_path = Path(project_path)
        detected_languages = set()

        for language, indicators in cls._project_indicators.items():
            for indicator in indicators:
                if (project_path / indicator).exists():
                    detected_languages.add(language)
                    break

        excluded_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache',
                        'target', 'build', 'dist', '.idea', '.vscode', 'venv',
                        '.venv', 'env', '.env', 'virtualenv', 'workspaces'}

        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                if not any(excluded_dir in file_path.parts for excluded_dir in excluded_dirs):
                    ext = file_path.suffix.lower()
                    if ext in cls._extension_mapping:
                        detected_languages.add(cls._extension_mapping[ext])

        languages = list(detected_languages)
        if languages:
            logger.info(f"Detected multiple languages: {[lang.value for lang in languages]}")
        else:
            logger.warning(f"No supported language detected: {project_path}")
            languages = [LanguageType.UNKNOWN]

        return languages

    @classmethod
    def create_parser(cls, project_path: Union[str, Path],
                     language: Optional[LanguageType] = None) -> BaseCodeParser:
        """Create code parser instance"""
        project_path = Path(project_path)

        if language is None:
            language = cls.detect_project_language(project_path)

        if language not in cls._parsers:
            available_parsers = list(cls._parsers.keys())
            raise ValueError(f"Unsupported language: {language.value}. "
                           f"Available parsers: {[lang.value for lang in available_parsers]}")

        parser_class = cls._parsers[language]
        parser = parser_class(str(project_path))

        logger.info(f"Created {language.value} parser: {parser_class.__name__}")
        return parser

    @classmethod
    def create_mixed_parsers(cls, project_path: Union[str, Path]) -> List[BaseCodeParser]:
        """Create multiple parsers for mixed-language project"""
        languages = cls.detect_mixed_languages(project_path)
        parsers = []

        for language in languages:
            if language in cls._parsers:
                try:
                    parser = cls.create_parser(project_path, language)
                    parsers.append(parser)
                except Exception as e:
                    logger.warning(f"Failed to create {language.value} parser: {e}")

        if not parsers:
            raise ValueError(f"Cannot create any parser for project: {project_path}")

        logger.info(f"Created {len(parsers)} parsers for mixed project")
        return parsers

    @classmethod
    def get_supported_languages(cls) -> List[LanguageType]:
        """Get list of supported language types"""
        return list(cls._parsers.keys())

    @classmethod
    def is_language_supported(cls, language: LanguageType) -> bool:
        """Check if language is supported"""
        return language in cls._parsers


class MultiLanguageProjectAnalyzer:
    """Multi-language project analyzer"""

    def __init__(self, project_path: Union[str, Path]):
        self.project_path = Path(project_path)
        self.parsers = ParserFactory.create_mixed_parsers(project_path)
        self.analysis_results = {}

    def analyze_all_languages(self) -> Dict[LanguageType, Dict]:
        """Analyze all languages in project"""
        results = {}

        for parser in self.parsers:
            language = parser.get_language_type()
            logger.info(f"Analyzing {language.value} code...")

            try:
                project_info = parser.parse_project()
                results[language] = project_info.to_dict()
                logger.info(f"{language.value} code analysis complete")
            except Exception as e:
                logger.error(f"{language.value} code analysis failed: {e}")
                results[language] = {'error': str(e)}

        self.analysis_results = results
        return results

    def save_combined_results(self, output_path: Optional[str] = None):
        """Save combined analysis results"""
        if output_path is None:
            output_path = self.project_path / "multi_language_analysis_result.json"

        import json
        combined_result = {
            'project_path': str(self.project_path),
            'analyzed_languages': [lang.value for lang in self.analysis_results.keys()],
            'results': {lang.value: result for lang, result in self.analysis_results.items()}
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined_result, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Multi-language analysis results saved to: {output_path}")

    def get_project_overview(self) -> Dict:
        """Get project overview information"""
        overview = {
            'total_languages': len(self.analysis_results),
            'languages': [],
            'total_elements': 0,
            'total_relations': 0,
            'total_files': 0
        }

        for language, result in self.analysis_results.items():
            if 'error' not in result:
                lang_info = {
                    'language': language.value,
                    'elements': result.get('statistics', {}).get('total_elements', 0),
                    'relations': result.get('statistics', {}).get('total_relations', 0),
                    'files': result.get('statistics', {}).get('total_files', 0)
                }
                overview['languages'].append(lang_info)
                overview['total_elements'] += lang_info['elements']
                overview['total_relations'] += lang_info['relations']
                overview['total_files'] += lang_info['files']

        return overview


# Register default parsers
ParserFactory.register_parser(LanguageType.JAVA, JavaParser)
ParserFactory.register_parser(LanguageType.PYTHON, PythonParser)
ParserFactory.register_parser(LanguageType.JAVASCRIPT, JavaScriptParser)
ParserFactory.register_parser(LanguageType.TYPESCRIPT, TypeScriptParser)
