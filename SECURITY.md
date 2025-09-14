# Security Policy

## 🔒 Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## 🚨 Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. **DO NOT** create a public issue

Security vulnerabilities should be reported privately to prevent exploitation.

### 2. **Email us directly**

Send an email to: `security@yourdomain.com` (replace with your actual email)

Include the following information:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### 3. **What to expect**

- **Response time**: We aim to respond within 48 hours
- **Acknowledgment**: You'll receive confirmation that we received your report
- **Updates**: We'll keep you informed of our progress
- **Resolution**: We'll work with you to resolve the issue

### 4. **Disclosure timeline**

- **Initial response**: Within 48 hours
- **Status update**: Within 1 week
- **Resolution**: Within 30 days (depending on complexity)
- **Public disclosure**: After fix is released and deployed

## 🛡️ Security Best Practices

### For Users

1. **Keep ZAP updated**
   - Always use the latest version of OWASP ZAP
   - Update your Java runtime regularly

2. **Secure your environment**
   - Use strong API keys if enabled
   - Limit network access to ZAP instances
   - Run ZAP in isolated environments when possible

3. **Monitor your scans**
   - Review scan results regularly
   - Set up alerts for critical vulnerabilities
   - Keep scan data secure

### For Developers

1. **Code security**
   - Follow secure coding practices
   - Validate all inputs
   - Use parameterized queries
   - Implement proper error handling

2. **Dependencies**
   - Keep dependencies updated
   - Use dependency scanning tools
   - Review third-party code

3. **Testing**
   - Include security tests in your CI/CD
   - Perform regular security audits
   - Test with real-world scenarios

## 🔍 Security Features

### Built-in Protections

- **API Key Protection**: Optional API key authentication
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Secure error messages without information disclosure
- **Session Management**: Proper session handling and cleanup
- **Network Security**: Configurable network access controls

### Container Security

- **Non-root User**: ZAP runs as non-root user in containers
- **Minimal Attack Surface**: Only necessary ports exposed
- **Regular Updates**: Base images updated regularly
- **Security Scanning**: Container images scanned for vulnerabilities

## 📋 Security Checklist

Before deploying ZAP MCP Server:

- [ ] ZAP is updated to latest version
- [ ] Java runtime is updated
- [ ] API keys are configured (if needed)
- [ ] Network access is properly restricted
- [ ] Log files are secured
- [ ] Backup procedures are in place
- [ ] Monitoring is configured
- [ ] Security policies are defined

## 🚫 Known Limitations

### Current Limitations

1. **API Key**: Disabled by default in Docker (can be enabled)
2. **Network Access**: ZAP API accessible on all interfaces by default
3. **Session Storage**: Sessions stored locally (consider external storage for production)
4. **Logging**: Debug logs may contain sensitive information

### Mitigation Strategies

1. **Enable API Key**: Set `ZAP_APIKEY` environment variable
2. **Restrict Network**: Use firewall rules or Docker networks
3. **Secure Storage**: Use encrypted volumes for session storage
4. **Log Management**: Configure log rotation and secure storage

## 🔄 Security Updates

### How we handle security updates:

1. **Critical vulnerabilities**: Immediate patch release
2. **High severity**: Patch within 1 week
3. **Medium severity**: Patch within 1 month
4. **Low severity**: Included in next regular release

### Update notifications:

- GitHub security advisories
- Release notes
- Email notifications (for critical issues)

## 📞 Contact

For security-related questions or concerns:

- **Email**: `security@yourdomain.com`
- **GitHub**: Create a private security issue
- **Discord**: Use the security channel (if available)

## 🙏 Acknowledgments

We appreciate security researchers who help us improve the security of ZAP MCP Server. Responsible disclosure helps us protect all users.

---

**Last updated**: January 2025
**Next review**: July 2025
