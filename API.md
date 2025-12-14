# PatternShield API

## Authentication
- Send API key in header `${API_KEY_HEADER}`.
- For transformer/ensemble endpoints also include `Authorization: Bearer <token>`.

## Endpoints
### `GET /health`
Returns service status.

### `GET /health/ready`
Checks database, cache, and model availability.

### `POST /analyze`
- Body: `{ "text": "...", "element_type": "div", "color": "#000000" }`
- Requires API key.

### `POST /analyze/transformer`
- Body same as above.
- Requires API key and JWT.

### `POST /analyze/ensemble`
- Combines transformer and rule-based outputs.

### `GET /metrics`
Prometheus metrics endpoint.

## Errors
- 400 validation error
- 401 authentication failure
- 429 rate limited
- 503 model unavailable
