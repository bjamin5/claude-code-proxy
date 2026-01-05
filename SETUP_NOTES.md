# Claude Code Proxy - Setup Notes

## ✅ Successfully Configured

Your proxy is now working with your LLM provider at `https://albus.taxhawk.com/api`

### Configuration Summary

- **Provider**: Custom OpenAI-compatible API (gateway to Anthropic)
- **Base URL**: `https://albus.taxhawk.com/api`
- **SSL**: Self-signed certificate (verification disabled)
- **Authentication**: Client API key validation disabled
- **Models**:
  - Big (opus): `anthropic/claude-opus-4.5`
  - Middle (sonnet): `anthropic/claude-sonnet-4.5`
  - Small (haiku): `anthropic/claude-sonnet-4.5`

### Working Features ✅

All core functionality is working:

1. ✅ **Basic chat** - Text conversations
2. ✅ **System messages** - Custom system prompts
3. ✅ **Streaming** - Real-time response streaming
4. ✅ **Function calling** - Tool/function definitions
5. ✅ **Tool use** - Complete tool call and result flow
6. ✅ **Token counting** - Estimate token usage

### Known Limitation ⚠️

**Multimodal (Image) Support**: Image requests fail with `invalid base64 data` error.

**Why this happens:**
1. Claude Code sends image in Claude format
2. Proxy converts to OpenAI format (✅ works correctly)
3. Your API gateway receives OpenAI format
4. Gateway converts back to Claude format for Anthropic
5. ❌ Base64 data gets corrupted in double conversion

**Impact**: Text-based requests work perfectly. Image support would require your API provider to accept OpenAI format directly without re-conversion.

**Workaround**: For image-based tasks, use the Anthropic API directly instead of through the proxy.

## Usage with Claude Code

Your `.zshrc` is already configured:

```bash
export ANTHROPIC_BASE_URL=http://localhost:8082
export ANTHROPIC_API_KEY="any-value"
```

### Start the Proxy

```bash
python start_proxy.py
```

### Use Claude Code

```bash
claude
```

All text-based Claude Code features will work through your LLM provider!

## Test Results

Run tests with:
```bash
cd tests
python test_main.py
```

**Expected results:**
- 7/8 tests passing ✅
- 1/8 test failing (multimodal) ⚠️

## Troubleshooting

### If SSL errors return
The proxy disables SSL verification for self-signed certificates. If you see SSL errors, check that the changes to `src/core/client.py` are in place.

### If authentication errors return
Make sure `ANTHROPIC_API_KEY` is commented out in `.env` file:
```bash
# ANTHROPIC_API_KEY="your-expected-anthropic-api-key"
```

### If connection errors return
Verify your API is accessible:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://albus.taxhawk.com/api/v1/models
```

## Files Modified

1. `.env` - Configuration settings
2. `src/core/client.py` - SSL verification disabled, enhanced logging
3. `src/__init__.py` - Environment variable override enabled
4. `start_proxy.py` - Unset shell ANTHROPIC_API_KEY
5. `src/api/endpoints.py` - (no changes needed)

## Security Note

⚠️ **SSL verification is disabled** to support self-signed certificates. Only use this proxy with trusted APIs on your internal network.
