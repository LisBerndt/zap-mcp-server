# Contributing to ZAP MCP Server

Thank you for your interest in contributing to the ZAP MCP Server! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- OWASP ZAP installed and accessible via PATH
- Java (required by ZAP)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/LisBerndt/zap-custom-mcp.git
   cd zap-custom-mcp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up development environment**
   ```bash
   # Copy environment template
   cp env.example .env
   
   # Edit .env for your local setup
   # Make sure ZAP is accessible via PATH
   ```

4. **Test your setup**
   ```bash
   python -m zap_custom_mcp
   ```

## 🛠️ Development Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write clear, descriptive variable and function names
- Add docstrings for functions and classes

### Testing

- Test your changes locally before submitting
- Ensure ZAP integration works correctly
- Test both local and Docker deployments

### Documentation

- Update README.md if you add new features
- Add docstrings to new functions
- Update this CONTRIBUTING.md if needed

## 📝 How to Contribute

### Reporting Issues

1. Check existing issues first
2. Use the issue template
3. Provide detailed information:
   - OS and version
   - Python version
   - ZAP version
   - Steps to reproduce
   - Expected vs actual behavior

### Suggesting Features

1. Check existing feature requests
2. Describe the use case clearly
3. Explain how it fits with the project goals
4. Consider implementation complexity

### Submitting Code

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Write clean, well-documented code
   - Test thoroughly
   - Update documentation as needed
4. **Commit your changes**
   ```bash
   git commit -m "Add: brief description of changes"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Create a Pull Request**
   - Use the PR template
   - Describe your changes clearly
   - Link any related issues

## 🏗️ Project Structure

```
zap-custom-mcp/
├── scans/           # Scan implementations
├── models.py        # Data models
├── utils.py         # Utility functions
├── config.py        # Configuration management
├── server.py        # MCP server implementation
├── http_server.py   # HTTP server wrapper
├── docker/          # Docker configuration
└── docs/           # Documentation
```

## 🔧 Development Tips

### Running Tests

```bash
# Test MCP server
python server.py

# Test HTTP server
python -m zap_custom_mcp

# Test Docker setup
docker-compose up --build
```

### Debugging

- Enable debug logging: `ZAP_LOG_LEVEL=DEBUG`
- Check ZAP logs in `logs/` directory
- Use ZAP GUI for manual testing

### Common Issues

1. **ZAP not starting**: Check Java installation and PATH
2. **Port conflicts**: Modify ports in `.env`
3. **Permission issues**: Check Docker permissions

## 📋 Pull Request Process

1. **Ensure your PR:**
   - Has a clear title and description
   - Includes tests for new functionality
   - Updates documentation if needed
   - Follows the coding style guidelines

2. **PR will be reviewed for:**
   - Code quality and style
   - Functionality and testing
   - Documentation completeness
   - Security considerations

3. **After approval:**
   - Maintainer will merge the PR
   - Feature will be included in next release

## 🎯 Areas for Contribution

### High Priority
- Bug fixes and stability improvements
- Performance optimizations
- Enhanced error handling
- Better documentation

### Medium Priority
- New scan types
- Additional MCP tools
- UI improvements
- CI/CD enhancements

### Low Priority
- Advanced features
- Integration with other tools
- Custom scan policies

## 🤝 Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and best practices
- Follow the code of conduct

## 📞 Getting Help

- 📖 Check the [Documentation](README.md)
- 🐛 [Report Issues](https://github.com/LisBerndt/zap-custom-mcp/issues)
- 💬 [Join Discussions](https://github.com/LisBerndt/zap-custom-mcp/discussions)

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to the ZAP MCP Server! 🚀
