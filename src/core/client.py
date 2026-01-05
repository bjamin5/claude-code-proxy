import asyncio
import json
from fastapi import HTTPException
from typing import Optional, AsyncGenerator, Dict, Any
from openai import AsyncOpenAI, AsyncAzureOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai._exceptions import APIError, RateLimitError, AuthenticationError, BadRequestError
import logging
import httpx

logger = logging.getLogger(__name__)

class OpenAIClient:
    """Async OpenAI client with cancellation support."""

    def __init__(self, api_key: str, base_url: str, timeout: int = 90, api_version: Optional[str] = None, custom_headers: Optional[Dict[str, str]] = None, ssl_verify: bool = True):
        self.api_key = api_key
        self.base_url = base_url
        self.custom_headers = custom_headers or {}
        self.ssl_verify = ssl_verify
        
        # Prepare default headers
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": "claude-proxy/1.0.0"
        }
        
        # Merge custom headers with default headers
        all_headers = {**default_headers, **self.custom_headers}

        # Create HTTP client with configurable SSL verification
        # When ssl_verify=False, allows connections to APIs with self-signed certificates
        http_client = httpx.AsyncClient(verify=self.ssl_verify)
        if not self.ssl_verify:
            logger.warning("SSL verification is DISABLED - only use this with trusted APIs")

        # Detect if using Azure and instantiate the appropriate client
        if api_version:
            self.client = AsyncAzureOpenAI(
                api_key=api_key,
                azure_endpoint=base_url,
                api_version=api_version,
                timeout=timeout,
                default_headers=all_headers,
                http_client=http_client
            )
        else:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
                default_headers=all_headers,
                http_client=http_client
            )
        self.active_requests: Dict[str, asyncio.Event] = {}
    
    async def create_chat_completion(self, request: Dict[str, Any], request_id: Optional[str] = None) -> Dict[str, Any]:
        """Send chat completion to OpenAI API with cancellation support."""

        # Log the request details
        logger.info(f"=== OpenAI API Request ===")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Model: {request.get('model', 'N/A')}")
        logger.info(f"Max Tokens: {request.get('max_tokens', 'N/A')}")
        logger.info(f"Messages Count: {len(request.get('messages', []))}")

        # Log sanitized headers
        sanitized_headers = {k: ('***' if k.lower() in ['authorization', 'api-key'] else v)
                            for k, v in self.custom_headers.items()}
        logger.info(f"Custom Headers: {sanitized_headers}")

        # Log first message for context
        if request.get('messages'):
            first_msg = request['messages'][0]
            logger.info(f"First Message Role: {first_msg.get('role', 'N/A')}")
            content = first_msg.get('content', '')
            if isinstance(content, str):
                logger.info(f"First Message Content (truncated): {content[:100]}...")

        # Create cancellation token if request_id provided
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event
        
        try:
            # Create task that can be cancelled
            completion_task = asyncio.create_task(
                self.client.chat.completions.create(**request)
            )
            
            if request_id:
                # Wait for either completion or cancellation
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait(
                    [completion_task, cancel_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel pending tasks
                for task in pending:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                
                # Check if request was cancelled
                if cancel_task in done:
                    completion_task.cancel()
                    raise HTTPException(status_code=499, detail="Request cancelled by client")
                
                completion = await completion_task
            else:
                completion = await completion_task
            
            # Convert to dict format that matches the original interface
            logger.info(f"=== OpenAI API Response Success ===")
            return completion.model_dump()

        except AuthenticationError as e:
            logger.error(f"=== Authentication Error ===")
            logger.error(f"Error Type: AuthenticationError")
            logger.error(f"Error Message: {str(e)}")
            logger.error(f"Error Details: {repr(e)}")
            raise HTTPException(status_code=401, detail=self.classify_openai_error(str(e)))
        except RateLimitError as e:
            logger.error(f"=== Rate Limit Error ===")
            logger.error(f"Error Message: {str(e)}")
            raise HTTPException(status_code=429, detail=self.classify_openai_error(str(e)))
        except BadRequestError as e:
            logger.error(f"=== Bad Request Error ===")
            logger.error(f"Error Message: {str(e)}")
            logger.error(f"Error Details: {repr(e)}")
            raise HTTPException(status_code=400, detail=self.classify_openai_error(str(e)))
        except APIError as e:
            logger.error(f"=== API Error ===")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            logger.error(f"Error Details: {repr(e)}")
            logger.error(f"Status Code: {getattr(e, 'status_code', 'N/A')}")
            logger.error(f"Response Body: {getattr(e, 'body', 'N/A')}")
            logger.error(f"Response: {getattr(e, 'response', 'N/A')}")

            # Log the underlying cause if available
            if hasattr(e, '__cause__') and e.__cause__:
                logger.error(f"Underlying Cause: {type(e.__cause__).__name__}: {str(e.__cause__)}")

            status_code = getattr(e, 'status_code', 500)
            raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(e)))
        except Exception as e:
            logger.error(f"=== Unexpected Error ===")
            logger.error(f"Error Type: {type(e).__name__}")
            logger.error(f"Error Message: {str(e)}")
            logger.error(f"Error Details: {repr(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        
        finally:
            # Clean up active request tracking
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]
    
    async def create_chat_completion_stream(self, request: Dict[str, Any], request_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """Send streaming chat completion to OpenAI API with cancellation support."""
        
        # Create cancellation token if request_id provided
        if request_id:
            cancel_event = asyncio.Event()
            self.active_requests[request_id] = cancel_event
        
        try:
            # Ensure stream is enabled
            request["stream"] = True
            if "stream_options" not in request:
                request["stream_options"] = {}
            request["stream_options"]["include_usage"] = True
            
            # Create the streaming completion
            streaming_completion = await self.client.chat.completions.create(**request)
            
            async for chunk in streaming_completion:
                # Check for cancellation before yielding each chunk
                if request_id and request_id in self.active_requests:
                    if self.active_requests[request_id].is_set():
                        raise HTTPException(status_code=499, detail="Request cancelled by client")
                
                # Convert chunk to SSE format matching original HTTP client format
                chunk_dict = chunk.model_dump()
                chunk_json = json.dumps(chunk_dict, ensure_ascii=False)
                yield f"data: {chunk_json}"
            
            # Signal end of stream
            yield "data: [DONE]"
                
        except AuthenticationError as e:
            raise HTTPException(status_code=401, detail=self.classify_openai_error(str(e)))
        except RateLimitError as e:
            raise HTTPException(status_code=429, detail=self.classify_openai_error(str(e)))
        except BadRequestError as e:
            raise HTTPException(status_code=400, detail=self.classify_openai_error(str(e)))
        except APIError as e:
            status_code = getattr(e, 'status_code', 500)
            raise HTTPException(status_code=status_code, detail=self.classify_openai_error(str(e)))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        
        finally:
            # Clean up active request tracking
            if request_id and request_id in self.active_requests:
                del self.active_requests[request_id]

    def classify_openai_error(self, error_detail: Any) -> str:
        """Provide specific error guidance for common OpenAI API issues."""
        error_str = str(error_detail).lower()
        
        # Region/country restrictions
        if "unsupported_country_region_territory" in error_str or "country, region, or territory not supported" in error_str:
            return "OpenAI API is not available in your region. Consider using a VPN or Azure OpenAI service."
        
        # API key issues
        if "invalid_api_key" in error_str or "unauthorized" in error_str:
            return "Invalid API key. Please check your OPENAI_API_KEY configuration."
        
        # Rate limiting
        if "rate_limit" in error_str or "quota" in error_str:
            return "Rate limit exceeded. Please wait and try again, or upgrade your API plan."
        
        # Model not found
        if "model" in error_str and ("not found" in error_str or "does not exist" in error_str):
            return "Model not found. Please check your BIG_MODEL and SMALL_MODEL configuration."
        
        # Billing issues
        if "billing" in error_str or "payment" in error_str:
            return "Billing issue. Please check your OpenAI account billing status."
        
        # Default: return original message
        return str(error_detail)
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request by request_id."""
        if request_id in self.active_requests:
            self.active_requests[request_id].set()
            return True
        return False