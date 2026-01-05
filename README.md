# Claude Code Proxy

A proxy server that enables **Claude Code** to work with OpenAI-compatible API providers. Convert Claude API requests to OpenAI API calls, allowing you to use various LLM providers through the Claude Code CLI.

## Features

- **Full Claude API Compatibility**: Complete `/v1/messages` endpoint support
- **Multiple Provider Support**: Works with any OpenAI-compatible API
- **Smart Model Mapping**: Configure BIG, MIDDLE, and SMALL models via environment variables
- **Function Calling**: Complete tool use support with proper conversion
- **Streaming Responses**: Real-time SSE streaming support
- **Image Support**: Base64 encoded image input
- **Custom Headers**: Automatic injection of custom HTTP headers for API requests
- **SSL Configuration**: Configurable SSL verification for self-signed certificates
- **Error Handling**: Comprehensive error handling and logging

## Quick Start

### 1. Install Dependencies

```bash
# Using UV 
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your API configuration
# Note: Environment variables are automatically loaded from .env file
```

### 3. Add Env Vars

```bash
# Set permanently (prefered) in your .bashrc / .zshrc etc.
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY="left-blank-on-purpose"

# Or run this inline when you run claude code
ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_API_KEY="left-blank-on-purpose" claude
```

### 4. Start Server

```bash
# Using Docker (recommended)
docker run -p 8082:8082 --env-file .env claude-code-proxy

# Or using Python
python start_proxy.py

# Or with UV
uv run claude-code-proxy
```

### 5. Open Claude Code
```bash
# Open claude from the terminal
claude
```

## Configuration

The application automatically loads environment variables from a `.env` file in the project root using `python-dotenv`. You can also set environment variables directly in your shell.

### Environment Variables

**Required:**

- `OPENAI_API_KEY` - Your Albus API key for the target provider (set in shell environment instead of .env)

**API Configuration:**

- `OPENAI_BASE_URL` - API base URL (default: `https://albus.taxhawk.com/api`)
- `AZURE_API_VERSION` - For Azure OpenAI (optional)

**Model Configuration:**

- `BIG_MODEL` - Model for Claude opus requests (default: `gpt-4o`)
- `MIDDLE_MODEL` - Model for Claude sonnet requests (default: `BIG_MODEL`)
- `SMALL_MODEL` - Model for Claude haiku requests (default: `gpt-4o-mini`)

**Security:**

- `ANTHROPIC_API_KEY` - Expected Anthropic API key for client validation (optional)
  - If set, clients must provide this exact API key to access the proxy
  - If not set, any API key will be accepted

**Server Settings:**

- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8082`)
- `LOG_LEVEL` - Logging level (default: `WARNING`)

**Performance:**

- `MAX_TOKENS_LIMIT` - Token limit (default: `4096`)
- `MIN_TOKENS_LIMIT` - Minimum tokens limit (default: `100`)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: `90`)
- `MAX_RETRIES` - Max retry attempts (default: `2`)

**SSL Configuration:**

- `SSL_VERIFY` - Enable/disable SSL certificate verification (default: `true`)
  - Set to `false` to allow connections to APIs with self-signed certificates
  - **WARNING**: Only disable for trusted APIs in development/testing environments

**Custom Headers:**

- `CUSTOM_HEADER_*` - Custom headers for API requests (e.g., `CUSTOM_HEADER_ACCEPT`, `CUSTOM_HEADER_AUTHORIZATION`)
  - Uncomment in `.env` file to enable custom headers

### Custom Headers Configuration

Add custom headers to your API requests by setting environment variables with the `CUSTOM_HEADER_` prefix:

```bash
# Examples - uncomment to enable custom headers
# CUSTOM_HEADER_ACCEPT="application/jsonstream"
# CUSTOM_HEADER_CONTENT_TYPE="application/json"
# CUSTOM_HEADER_USER_AGENT="your-app/1.0.0"
# CUSTOM_HEADER_AUTHORIZATION="Bearer your-token"
# CUSTOM_HEADER_X_API_KEY="your-api-key"
# CUSTOM_HEADER_X_CLIENT_ID="your-client-id"
```

Environment variables with the `CUSTOM_HEADER_` prefix are automatically converted to HTTP headers. The proxy will include these headers in all API requests to the target LLM provider.

### Model Mapping

The proxy maps Claude model requests to your configured models:

| Claude Request                 | Mapped To      | Environment Variable   |
| ------------------------------ | -------------- | ---------------------- |
| Models with "haiku"            | `SMALL_MODEL`  | Default: `gpt-4o-mini` |
| Models with "sonnet"           | `MIDDLE_MODEL` | Default: `BIG_MODEL`   |
| Models with "opus"             | `BIG_MODEL`    | Default: `gpt-4o`      |

## Development

### Using UV

```bash
# Install dependencies
uv sync

# Run server
uv run claude-code-proxy

# Format code
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/
```

### Testing

Verify your setup is working correctly:

```bash
# Run comprehensive tests (7/8 tests should pass)
cd tests
python test_main.py
```

## Known Limitations

**Multimodal (Image) Support**: Image requests fail with `invalid base64 data` errors due to using OpenWebUI (Albus)

- **Impact**: Text-based requests work perfectly
- **Workaround**: For image-based tasks, use the Anthropic API directly

## Security Note

⚠️ When `SSL_VERIFY="false"` is set, SSL certificate verification is disabled to support self-signed certificates. Only use this with trusted APIs on your internal network. 

## Docker (Alternative - Not Recommended)

Docker Compose is available but has had reliability issues. Using `python start_proxy.py` or `uv run claude-code-proxy` is preferred.

```bash
# If you want to try Docker anyway:
docker compose up -d
```

## License

MIT License
