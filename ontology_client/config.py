"""
Ontology Client Configuration

Configuration for connecting to the ontology project.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class OntologyConfig:
    """Configuration for ontology project connection"""

    # Path to ontology project
    ontology_path: str = ""

    # TTL output directory within ontology project
    ttl_dir: str = "ontology_build/ttl"

    # Domain name for R&D ontology
    domain: str = "rd"

    # Neo4j connection (if available)
    neo4j_uri: Optional[str] = None
    neo4j_user: Optional[str] = None
    neo4j_password: Optional[str] = None
    neo4j_database: Optional[str] = None

    # Embedding configuration
    embedding_api_base: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dim: Optional[int] = None

    @classmethod
    def from_env(cls) -> 'OntologyConfig':
        """Create config from environment variables"""
        embedding_dim_str = os.environ.get('EMBEDDING_DIM')
        return cls(
            ontology_path=os.environ.get('ONTOLOGY_PATH', ''),
            ttl_dir=os.environ.get('ONTOLOGY_TTL_DIR', 'ontology_build/ttl'),
            domain=os.environ.get('ONTOLOGY_DOMAIN', 'rd'),
            neo4j_uri=os.environ.get('NEO4J_URI'),
            neo4j_user=os.environ.get('NEO4J_USER'),
            neo4j_password=os.environ.get('NEO4J_PASSWORD'),
            neo4j_database=os.environ.get('NEO4J_DATABASE'),
            embedding_api_base=os.environ.get('EMBEDDING_API_BASE'),
            embedding_model=os.environ.get('EMBEDDING_MODEL'),
            embedding_dim=int(embedding_dim_str) if embedding_dim_str else None,
        )

    @classmethod
    def from_file(cls, config_path: str) -> 'OntologyConfig':
        """Load config from file"""
        import json

        path = Path(config_path)
        if not path.exists():
            return cls()

        with open(path, 'r') as f:
            data = json.load(f)

        # 过滤掉不支持的字段
        supported_fields = {
            'ontology_path', 'ttl_dir', 'domain',
            'neo4j_uri', 'neo4j_user', 'neo4j_password', 'neo4j_database',
            'embedding_api_base', 'embedding_model', 'embedding_dim'
        }
        filtered_data = {k: v for k, v in data.items() if k in supported_fields}

        return cls(**filtered_data)

    def save(self, config_path: str):
        """Save config to file"""
        import json

        data = {
            'ontology_path': self.ontology_path,
            'ttl_dir': self.ttl_dir,
            'domain': self.domain,
            'neo4j_uri': self.neo4j_uri,
            'neo4j_user': self.neo4j_user,
            'neo4j_password': self.neo4j_password,
            'neo4j_database': self.neo4j_database,
            'embedding_api_base': self.embedding_api_base,
            'embedding_model': self.embedding_model,
            'embedding_dim': self.embedding_dim,
        }

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_ttl_path(self) -> Path:
        """Get full path to TTL directory"""
        if self.ontology_path:
            return Path(self.ontology_path) / self.ttl_dir
        return Path(self.ttl_dir)

    def validate(self) -> bool:
        """Validate configuration"""
        if not self.ontology_path:
            return False

        ontology_path = Path(self.ontology_path)
        if not ontology_path.exists():
            return False

        return True


# Default config file location
DEFAULT_CONFIG_PATH = ".ontology_config.json"


def get_config(config_path: str = None) -> OntologyConfig:
    """Get ontology configuration"""
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH

    # Try file first
    if Path(config_path).exists():
        return OntologyConfig.from_file(config_path)

    # Fall back to environment
    return OntologyConfig.from_env()
