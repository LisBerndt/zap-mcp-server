# GitHub Actions Workflows

Dieses Repository verwendet GitHub Actions für automatisierte CI/CD-Pipelines, Security-Scans und Code-Qualitätsprüfungen.

## 🚀 Workflows Übersicht

### 1. **CI/CD Pipeline** (`.github/workflows/ci.yml`)
**Trigger:** Push auf `master`/`develop`, Pull Requests

**Jobs:**
- **Test Suite**: Tests auf Python 3.8-3.11
- **Security**: Bandit, Safety, Semgrep Scans
- **Docker**: Container Build Tests
- **ZAP Integration**: Echte ZAP-Integration Tests

### 2. **Security Scan** (`.github/workflows/security.yml`)
**Trigger:** Wöchentlich, Push auf `master`/`develop`, Pull Requests

**Jobs:**
- **Security Analysis**: Bandit, Safety, Semgrep, TruffleHog
- **Dependency Check**: Vulnerabilitäts-Checks
- **Docker Security**: Trivy, Docker Scout Scans

### 3. **Release** (`.github/workflows/release.yml`)
**Trigger:** Git Tags (`v*`)

**Jobs:**
- **Create Release**: Automatische Release-Erstellung
- **Docker Release**: Multi-Platform Docker Builds
- **Notify**: Release-Benachrichtigungen

### 4. **Docker Build and Push** (`.github/workflows/docker.yml`)
**Trigger:** Push auf `master`/`develop`, Pull Requests, Wöchentlich

**Jobs:**
- **Docker Build**: Multi-Platform Container Builds
- **Docker Push**: Automatisches Pushen zu Docker Hub
- **Security Scan**: Container-Sicherheitsscans
- **Size Check**: Image-Größen-Validierung

### 5. **Code Quality** (`.github/workflows/code-quality.yml`)
**Trigger:** Push auf `master`/`develop`, Pull Requests

**Jobs:**
- **Code Quality**: Black, isort, flake8, mypy, Bandit
- **Documentation**: README, LICENSE, CHANGELOG Checks
- **Performance**: Import-Performance, Memory-Checks

## 🔧 Konfiguration

### Required Secrets
Für vollständige Funktionalität müssen folgende Secrets konfiguriert werden:

```bash
# Docker Hub Credentials (für Docker Push)
DOCKER_USERNAME=your-dockerhub-username
DOCKER_PASSWORD=your-dockerhub-password
```

### Branch Strategy
- **`master`**: Hauptbranch für stabile Releases
- **`develop`**: Entwicklungsbranch für Features
- **Feature Branches**: `feature/xyz` → `develop` → `master`

## 📊 Workflow Status

| Workflow | Status | Beschreibung |
|----------|--------|--------------|
| CI/CD | ✅ | Vollständige Test-Pipeline |
| Security | ✅ | Wöchentliche Security-Scans |
| Release | ✅ | Automatische Releases |
| Docker | ✅ | Container Build & Push |
| Code Quality | ✅ | Code-Qualitätsprüfungen |

## 🛠️ Lokale Entwicklung

### Pre-commit Hooks (Empfohlen)
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Lokale Tests
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black isort mypy bandit

# Run tests
pytest --cov=. --cov-report=html

# Run linting
flake8 .
black --check .
isort --check-only .
mypy .

# Run security scan
bandit -r .
```

## 🔒 Security Features

### Automatische Security-Scans
- **Bandit**: Python Security Linting
- **Safety**: Dependency Vulnerabilitäten
- **Semgrep**: SAST (Static Application Security Testing)
- **TruffleHog**: Secret Detection
- **Trivy**: Container Vulnerabilitäten
- **Docker Scout**: Container Security

### Security Reports
- Automatische Uploads zu GitHub Security Tab
- PR-Kommentare mit Security-Ergebnissen
- Wöchentliche Security-Reports

## 🐳 Docker Integration

### Multi-Platform Builds
- **Linux AMD64**: Standard x86_64
- **Linux ARM64**: ARM64 Unterstützung

### Container Features
- **Health Checks**: Automatische Container-Validierung
- **Security Scans**: Trivy + Docker Scout
- **Size Validation**: Image-Größen-Checks
- **Cache Optimization**: GitHub Actions Cache

## 📈 Monitoring & Notifications

### Workflow Notifications
- **Success**: Automatische Erfolgs-Benachrichtigungen
- **Failure**: Detaillierte Fehler-Reports
- **Security**: Security-Scan Ergebnisse

### Artifacts
- **Test Reports**: Coverage Reports
- **Security Reports**: Bandit, Safety, Semgrep
- **Docker Images**: Multi-Platform Builds

## 🚀 Deployment

### Automatische Deployments
- **Master Branch**: Automatisches Docker Hub Push
- **Tags**: Automatische Release-Erstellung
- **Multi-Platform**: AMD64 + ARM64 Support

### Release Process
1. **Tag erstellen**: `git tag v1.0.0`
2. **Push Tag**: `git push origin v1.0.0`
3. **Automatische Release**: GitHub Actions erstellt Release
4. **Docker Push**: Automatisches Pushen zu Docker Hub

## 🔧 Troubleshooting

### Häufige Probleme

#### Docker Build Failures
```bash
# Lokaler Test
docker build -t zap-mcp-server:test .
docker run --rm zap-mcp-server:test python -c "import sys; print(sys.version)"
```

#### Security Scan Failures
```bash
# Lokaler Security Scan
bandit -r .
safety check
```

#### Test Failures
```bash
# Lokale Tests
pytest -v
pytest --cov=. --cov-report=html
```

### Workflow Debugging
- **Logs**: GitHub Actions Logs in Repository
- **Artifacts**: Downloadable Reports und Builds
- **Security Tab**: Security-Scan Ergebnisse

## 📚 Weitere Informationen

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Docker Hub**: https://hub.docker.com/
- **Security Best Practices**: https://docs.github.com/en/code-security
- **ZAP MCP Server**: Hauptprojekt-Dokumentation

---

**💡 Tipp**: Alle Workflows sind so konfiguriert, dass sie sowohl auf `master` als auch auf `develop` Branches laufen, um eine kontinuierliche Qualitätssicherung zu gewährleisten.
