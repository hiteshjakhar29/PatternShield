# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.x     | ✅ Active  |
| 2.x     | ⚠️ Patch only |
| < 2.0   | ❌ No longer supported |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues by emailing the maintainer directly (see GitHub profile). Include:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You will receive a response within 72 hours. If the issue is confirmed:
- A fix will be developed in a private branch
- A patched release will be published
- You will be credited in the release notes (unless you prefer anonymity)

## Security Considerations

### API Key Handling
- `ANTHROPIC_API_KEY` and `API_KEY` must be set via environment variables only
- Never commit `.env` files — `.gitignore` excludes them
- Use `secrets.token_hex(32)` to generate `SECRET_KEY`

### Rate Limiting
- Default: 500 req/hr, 60 req/min per IP
- Set `RATE_LIMIT_ENABLED=true` in production

### Data Privacy
- PatternShield does **not** store raw browsing history
- Only element text snippets (≤500 chars) are persisted when users scan a page
- Feedback is optional and user-initiated
- No cookies, no tracking

### Production Checklist
- [ ] Set a strong `SECRET_KEY`
- [ ] Set `API_KEY_REQUIRED=true` + a random `API_KEY`
- [ ] Configure `CORS_ORIGINS` to specific extension ID, not `*`
- [ ] Use `DATABASE_URL` pointing to PostgreSQL (not SQLite) for multi-instance deployments
- [ ] Enable HTTPS (Talisman is active when `FLASK_DEBUG=false`)
