# DS-CLI: DeepSeek CLI Development Agent

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful CLI development agent for DeepSeek API with vector memory, self-improvement capabilities, and comprehensive development tools.

## ✨ Features

### 🚀 Core Capabilities
- **DeepSeek API Integration**: Seamless interaction with DeepSeek models
- **Vector Memory System**: Persistent memory using Qdrant vector database
- **Self-Improvement**: Autonomous code improvement and documentation
- **Multi-Tool System**: File, shell, web, and memory tools

### 🛠️ Development Tools
- **File Operations**: Read, write, search, and manipulate files
- **Shell Execution**: Safe command execution with sandboxing
- **Web Integration**: Web search and content extraction
- **Memory Management**: Context-aware memory storage and retrieval

### 📊 Advanced Features
- **Plugin System**: Extensible architecture with custom plugins
- **Configuration Management**: YAML, JSON, and TOML support
- **Logging & Monitoring**: Structured logging with metrics
- **Testing Framework**: Comprehensive test suite

## 📦 Installation

### From PyPI (Coming Soon)
```bash
pip install ds-cli
```

### From Source
```bash
# Clone the repository
git clone https://github.com/your-username/ds-cli.git
cd ds-cli

# Install with pip
pip install -e .

# Or install with all optional dependencies
pip install -e .[all]
```

### Development Installation
```bash
# Install with development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

## 🚀 Quick Start

### Basic Usage
```bash
# Initialize the CLI
ds-cli init

# Start a development session
ds-cli start

# Use the agent for development tasks
ds-cli develop "Add a new feature to my project"
```

### Agent Commands
```bash
# File operations
ds-cli file read path/to/file.py
ds-cli file write path/to/file.py "content"

# Shell commands
ds-cli shell run "ls -la"
ds-cli shell check python

# Memory operations
ds-cli memory remember "Important fact" --category development
ds-cli memory recall "search query"

# Web operations
ds-cli web search "Python best practices"
ds-cli web fetch https://example.com
```

## 🏗️ Project Structure

```
ds-cli/
├── src/ds_cli/           # Main source code
│   ├── cli.py           # CLI entry point
│   ├── agent.py         # Agent core logic
│   ├── tools/           # Tool implementations
│   │   ├── file_tools.py
│   │   ├── shell_tools.py
│   │   ├── memory_tools.py
│   │   └── api_tools.py
│   ├── memory/          # Memory system
│   │   ├── vector_store.py
│   │   ├── embeddings.py
│   │   └── cli.py
│   ├── plugins/         # Plugin system
│   │   ├── file.py
│   │   ├── shell.py
│   │   ├── memory.py
│   │   └── web.py
│   └── utils/           # Utilities
│       ├── config.py
│       ├── logging.py
│       └── validation.py
├── config/              # Configuration files
│   ├── default.yaml
│   ├── development.yaml
│   └── production.yaml
├── templates/           # Template files
├── docs/               # Documentation
├── tests/              # Test suite
├── examples/           # Example usage
├── pyproject.toml      # Modern Python packaging
├── setup.py           # Legacy setup (backward compatibility)
├── requirements.txt   # Dependencies
├── MANIFEST.in        # Package manifest
└── README.md          # This file
```

## 🔧 Configuration

### Environment Variables
```bash
# DeepSeek API
DEEPSEEK_API_KEY=your_api_key_here

# Qdrant for vector memory
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Tavily for web search
TAVILY_API_KEY=your_tavily_api_key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Configuration Files
Create `config/local.yaml`:
```yaml
api:
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    base_url: https://api.deepseek.com
    model: deepseek-chat

memory:
  qdrant:
    host: localhost
    port: 6333
    collection_name: ds_cli_memory

logging:
  level: INFO
  format: rich

tools:
  shell:
    safe_mode: true
    timeout: 30
  web:
    timeout: 10
    user_agent: DS-CLI/0.1.0
```

## 🧠 Memory System

The vector memory system uses Qdrant to store and retrieve context:

```python
from ds_cli.memory import VectorMemory

# Initialize memory
memory = VectorMemory()

# Store information
memory.remember(
    information="Python best practice: Use type hints",
    category="development",
    metadata={"language": "python", "topic": "best_practices"}
)

# Retrieve context
results = memory.recall(
    query="Python type hints",
    max_results=5,
    filters={"category": "development"}
)
```

## 🔌 Plugin System

Create custom plugins in `plugins/custom.py`:
```python
from ds_cli.plugins import BasePlugin

class CustomPlugin(BasePlugin):
    """Custom plugin example."""
    
    def register_commands(self, cli):
        @cli.command()
        def custom_command():
            """Custom command example."""
            print("Custom plugin working!")
```

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ds_cli

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m e2e
```

## 📚 Documentation

Generate documentation:
```bash
# Build documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 and black formatting
- Write comprehensive docstrings
- Add tests for new features
- Update documentation
- Use type hints

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [DeepSeek](https://www.deepseek.com/) for the AI models
- [Qdrant](https://qdrant.tech/) for vector database
- [Click](https://click.palletsprojects.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for terminal formatting

## 📞 Support

- [Issues](https://github.com/your-username/ds-cli/issues)
- [Discussions](https://github.com/your-username/ds-cli/discussions)
- [Documentation](https://github.com/your-username/ds-cli/docs)

---

**Note**: This project is under active development. Features and APIs may change.
