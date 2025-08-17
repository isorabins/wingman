"""
Claude API Client for Direct Integration
Replaces LangChain/LangGraph with direct Anthropic API calls
"""
import os
import re
import logging
import httpx
import asyncio
import math
import json
import inspect
from typing import Optional, List, Dict, Any, Union, Callable, AsyncGenerator


logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Custom exception for Claude API related errors"""
    pass


class ClaudeCredentials:
    """Handles Claude API credential management and validation"""
    
    def __init__(self):
        """Initialize credentials from environment variables"""
        self.api_key = self._load_api_key()
        self._validate_api_key_format()
    
    def _load_api_key(self) -> str:
        """Load API key from environment variable"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if api_key is None:
            raise ClaudeAPIError("ANTHROPIC_API_KEY environment variable not found")
        
        if not api_key.strip():
            raise ClaudeAPIError("ANTHROPIC_API_KEY cannot be empty")
        
        return api_key.strip()
    
    def _validate_api_key_format(self) -> None:
        """Validate that API key follows expected format"""
        # Anthropic API keys typically start with 'sk-ant-'
        if not re.match(r'^sk-ant-', self.api_key):
            raise ClaudeAPIError("Invalid API key format")
    
    async def validate(self) -> bool:
        """Validate credentials by making a test API call"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 10,
                        "messages": [
                            {"role": "user", "content": "test"}
                        ]
                    }
                )
                
                if response.status_code == 401:
                    logger.warning("Invalid Claude API credentials")
                    return False
                
                if response.status_code == 200:
                    logger.info("Claude API credentials validated successfully")
                    return True
                
                # Other status codes might indicate issues but not invalid creds
                logger.warning(f"Unexpected response status: {response.status_code}")
                return False
                
        except httpx.NetworkError as e:
            raise ClaudeAPIError(f"Network error during credential validation: {str(e)}")
        except httpx.TimeoutException as e:
            raise ClaudeAPIError(f"Timeout during credential validation: {str(e)}")
        except Exception as e:
            raise ClaudeAPIError(f"Unexpected error during credential validation: {str(e)}")
    
    def __str__(self) -> str:
        """String representation with masked API key for security"""
        if len(self.api_key) > 10:
            masked_key = self.api_key[:7] + "***"
        else:
            masked_key = "***"
        return f"ClaudeCredentials(api_key={masked_key})"
    
    def __repr__(self) -> str:
        """Representation with masked API key for security"""
        return self.__str__()


class ClaudeAPIClient:
    """Direct Claude API client for sending messages and managing requests"""
    
    def __init__(self, credentials: ClaudeCredentials, timeout: float = 30.0, max_retries: int = 3):
        """Initialize Claude API client with credentials and configuration"""
        self.credentials = credentials
        self.base_url = "https://api.anthropic.com/v1"
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def send_message(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20240620",
        max_tokens: int = 1000,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """Send a message to Claude API and return the response or stream events"""
        self._validate_messages(messages)
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if system:
            payload["system"] = system
        if temperature is not None:
            payload["temperature"] = temperature
        if tools:
            payload["tools"] = tools
        if stream:
            payload["stream"] = True
        
        payload.update(kwargs)
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.credentials.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        if not stream:
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(
                            f"{self.base_url}/messages",
                            headers=headers,
                            json=payload
                        )
                        return await self._handle_response(response)
                except (httpx.NetworkError, httpx.TimeoutException) as e:
                    if attempt == self.max_retries - 1:
                        if isinstance(e, httpx.NetworkError):
                            raise ClaudeAPIError(f"Network error: {str(e)}")
                        else:
                            raise ClaudeAPIError(f"Request timeout: {str(e)}")
                    await asyncio.sleep(2 ** attempt)
                    continue
            raise ClaudeAPIError("Failed to send message after multiple retries.")

        else:
            async def _stream_events():
                for attempt in range(self.max_retries):
                    try:
                        async with httpx.AsyncClient(timeout=self.timeout) as client:
                            async with client.stream(
                                "POST",
                                f"{self.base_url}/messages",
                                headers=headers,
                                json=payload
                            ) as response:
                                print(f"DEBUG _stream_events: id(response)={id(response)}, response.status_code={response.status_code}, type={type(response.status_code)}")
                                # TEMPORARILY BYPASS STATUS CHECK
                                # if response.status_code != 200:
                                #     raw_error_body = await response.aread()
                                #     print(f"DEBUG _stream_events: Calling _handle_response_streaming_error because status_code is {response.status_code}")
                                #     await self._handle_response_streaming_error(response, raw_error_body.decode())

                                buffer = ""
                                print(f"DEBUG _stream_events: About to loop. response.aiter_bytes is {response.aiter_bytes}")
                                async for line_bytes in response.aiter_bytes(): 
                                    print(f"DEBUG _stream_events loop: Received line_bytes: {line_bytes[:50]}...") 
                                    line = line_bytes.decode('utf-8')
                                    print(f"DEBUG _stream_events loop: Decoded line: {line.strip()[:100]}...")
                                    buffer += line
                                    while "\n\n" in buffer:
                                        event_str, buffer = buffer.split("\n\n", 1)
                                        if event_str.startswith("event:"):
                                            event_type = ""
                                            data_json = ""
                                            for part in event_str.split("\n"):
                                                if part.startswith("event:"):
                                                    event_type = part.split(":", 1)[1].strip()
                                                elif part.startswith("data:"):
                                                    data_json = part.split(":", 1)[1].strip()
                                            
                                            if data_json:
                                                try:
                                                    parsed_event = json.loads(data_json)
                                                    print(f"DEBUG _stream_events loop: Yielding event: {parsed_event}")
                                                    yield parsed_event
                                                except json.JSONDecodeError:
                                                    logger.warning(f"Failed to decode JSON from event data: {data_json}")
                                if buffer.strip() and buffer.strip() != "event: message_stop" and not buffer.strip().startswith("data: {"):
                                    if buffer.startswith("data: {") and buffer.endswith("}"):
                                        try:
                                            final_data_json = buffer.split("data: ", 1)[1].strip()
                                            yield json.loads(final_data_json)
                                        except json.JSONDecodeError:
                                            logger.warning(f"Failed to decode trailing JSON from buffer: {buffer}")
                                    elif buffer.strip() != "data: {\"type\": \"message_stop\"}":
                                        logger.warning(f"Non-empty buffer remaining after stream: {buffer}")
                                return
                    except (httpx.NetworkError, httpx.TimeoutException) as e:
                        if attempt == self.max_retries - 1:
                            if isinstance(e, httpx.NetworkError):
                                raise ClaudeAPIError(f"Network error during stream: {str(e)}")
                            else:
                                raise ClaudeAPIError(f"Request timeout during stream: {str(e)}")
                        await asyncio.sleep(2 ** attempt)
                        continue
                    except Exception as e: 
                        logger.error(f"Unexpected error during stream processing: {e}")
                        raise ClaudeAPIError(f"Unexpected error during stream: {str(e)}")
                raise ClaudeAPIError("Failed to stream message after multiple retries.")
            return _stream_events()

    async def _handle_response_streaming_error(self, response: httpx.Response, error_body: str):
        """Handle API error responses during streaming. This should raise an exception."""
        print(f"DEBUG _handle_response_streaming_error: id(response)={id(response)}, response.status_code={response.status_code}, type={type(response.status_code)}")
        if response.status_code == 401:
            try:
                error_data = json.loads(error_body)
                error_message = error_data.get("error", {}).get("message", "Unknown authentication error")
                raise ClaudeAPIError(f"Authentication failed during stream: {error_message} (Status: {response.status_code})")
            except (json.JSONDecodeError, KeyError):
                raise ClaudeAPIError(f"Authentication failed during stream: Invalid API key or malformed error response (Status: {response.status_code})")
        
        elif response.status_code == 429:
            try:
                error_data = json.loads(error_body)
                error_message = error_data.get("error", {}).get("message", "Unknown rate limit error")
                raise ClaudeAPIError(f"Rate limit exceeded during stream: {error_message} (Status: {response.status_code})")
            except (json.JSONDecodeError, KeyError):
                raise ClaudeAPIError(f"Rate limit exceeded during stream (Status: {response.status_code})")
        
        elif response.status_code >= 500:
            raise ClaudeAPIError(f"Server error during stream ({response.status_code}): {error_body}")
        
        else:
            raise ClaudeAPIError(f"API error during stream ({response.status_code}): {error_body}")

    async def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and error cases"""
        if response.status_code == 200:
            return response.json()
        
        # Handle error responses
        if response.status_code == 401:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown authentication error")
                raise ClaudeAPIError(f"Authentication failed: {error_message}")
            except (ValueError, KeyError):
                raise ClaudeAPIError("Authentication failed: Invalid API key")
        
        elif response.status_code == 429:
            try:
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Unknown rate limit error")
                raise ClaudeAPIError(f"Rate limit exceeded: {error_message}")
            except (ValueError, KeyError):
                raise ClaudeAPIError("Rate limit exceeded")
        
        elif response.status_code >= 500:
            raise ClaudeAPIError(f"Server error ({response.status_code}): {response.text}")
        
        else:
            raise ClaudeAPIError(f"API error ({response.status_code}): {response.text}")
    
    def _validate_messages(self, messages: Union[List[Dict[str, str]], Any]) -> None:
        """Validate message format"""
        if not isinstance(messages, list):
            raise ClaudeAPIError("Messages must be a list")
        
        for message in messages:
            if not isinstance(message, dict):
                raise ClaudeAPIError("Each message must be a dictionary")
            
            if "role" not in message or "content" not in message:
                raise ClaudeAPIError("Message must have 'role' and 'content' fields")
            
            if message["role"] not in ["user", "assistant"]:
                raise ClaudeAPIError(f"Invalid role: {message['role']}. Must be 'user' or 'assistant'")


class ClaudeContextManager:
    """Context management for Claude API replacing LangChain functionality"""
    
    def __init__(self, max_tokens: int = 4000):
        """Initialize context manager with token limits"""
        self.max_tokens = max_tokens
        self.message_buffer: List[Dict[str, Any]] = []
        self.system_prompt_template = self._load_system_prompt_template()
    
    def _load_system_prompt_template(self) -> str:
        """Load base system prompt template"""
        return """You are Hai, an AI assistant for Fridays at Four, helping creative professionals turn their dream projects into reality.

User Context:
- User ID: {user_id}
- Project: {project_name}
- Current State: {conversation_state}

Your role is to be a supportive creative partner who helps with project planning, provides encouragement, and maintains context throughout the conversation."""
    
    def add_message(self, role: str, content: str, is_system_important: bool = False) -> None:
        """Add a message to the context buffer"""
        message = {
            "role": role,
            "content": content,
            "is_system_important": is_system_important,
            "timestamp": asyncio.get_event_loop().time() if asyncio._get_running_loop() else 0
        }
        self.message_buffer.append(message)
    
    def build_system_prompt(self, user_context: Dict[str, Any]) -> str:
        """Build system prompt with user context injection"""
        return self.system_prompt_template.format(
            user_id=user_context.get("user_id", "unknown"),
            project_name=user_context.get("project_name", "New Project"),
            conversation_state=user_context.get("conversation_state", "initial")
        )
    
    def build_onboarding_system_prompt(self, user_context: Dict[str, Any]) -> str:
        """Build specialized system prompt for onboarding flow"""
        base_prompt = self.build_system_prompt(user_context)
        
        onboarding_context = f"""

Onboarding Context:
- Stage: {user_context.get('onboarding_stage', 'unknown')}
- Previous Responses: {user_context.get('previous_responses', [])}

You are guiding the user through project discovery. Ask thoughtful questions that help them clarify their vision, identify challenges, and build confidence in their creative project."""
        
        return base_prompt + onboarding_context
    
    def inject_memory_context(self, db_memory: Dict[str, Any]) -> str:
        """Inject memory context from database into system prompt"""
        memory_prompt = "\nMemory Context:\n"
        
        if "project_overview" in db_memory:
            overview = db_memory["project_overview"]
            memory_prompt += f"- Project: {overview.get('project_name', 'N/A')}\n"
            memory_prompt += f"- Goals: {', '.join(overview.get('goals', []))}\n"
            memory_prompt += f"- Challenges: {', '.join(overview.get('challenges', []))}\n"
        
        if "user_preferences" in db_memory:
            prefs = db_memory["user_preferences"]
            memory_prompt += f"- Communication Style: {prefs.get('communication_style', 'N/A')}\n"
            memory_prompt += f"- Technical Level: {prefs.get('technical_level', 'N/A')}\n"
        
        return self.system_prompt_template + memory_prompt
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        # Rough estimate: 1 token ≈ 4 characters for English text
        return math.ceil(len(text) / 4)
    
    def format_messages_for_api(self) -> List[Dict[str, str]]:
        """Format messages for Claude API, handling token limits"""
        if not self.message_buffer:
            return []
        
        # Calculate total tokens
        total_tokens = sum(self.estimate_tokens(msg["content"]) for msg in self.message_buffer)
        
        if total_tokens <= self.max_tokens:
            # No truncation needed
            return [{"role": msg["role"], "content": msg["content"]} for msg in self.message_buffer]
        
        # Need to truncate - preserve important messages and recent context
        important_messages = [msg for msg in self.message_buffer if msg.get("is_system_important", False)]
        recent_messages = self.message_buffer[-10:]  # Keep last 10 messages
        
        # Combine and deduplicate
        preserved_messages = []
        seen_indices = set()
        
        # Add important messages first
        for msg in important_messages:
            if id(msg) not in seen_indices:
                preserved_messages.append(msg)
                seen_indices.add(id(msg))
        
        # Add recent messages
        for msg in recent_messages:
            if id(msg) not in seen_indices:
                preserved_messages.append(msg)
                seen_indices.add(id(msg))
        
        # Sort by original order (using timestamp or index)
        preserved_messages.sort(key=lambda x: self.message_buffer.index(x))
        
        return [{"role": msg["role"], "content": msg["content"]} for msg in preserved_messages]
    
    def load_conversation_history(self, conversation_history: List[Dict[str, str]]) -> None:
        """Load conversation history from database"""
        self.message_buffer = []
        for msg in conversation_history:
            self.add_message(msg["role"], msg["content"])
    
    def create_message_batches(self) -> List[List[Dict[str, str]]]:
        """Create message batches for large contexts"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for message in self.message_buffer:
            msg_tokens = self.estimate_tokens(message["content"])
            
            # If single message exceeds max tokens, split it
            if msg_tokens > self.max_tokens:
                # Finish current batch if it has content
                if current_batch:
                    batches.append([{"role": msg["role"], "content": msg["content"]} for msg in current_batch])
                    current_batch = []
                    current_tokens = 0
                
                # Split large message into chunks
                content = message["content"]
                chunk_size = self.max_tokens * 4  # Approximate characters per batch
                
                for i in range(0, len(content), chunk_size):
                    chunk_content = content[i:i + chunk_size]
                    chunk_message = {"role": message["role"], "content": chunk_content}
                    batches.append([chunk_message])
                
            elif current_tokens + msg_tokens > self.max_tokens and current_batch:
                # Start new batch
                batches.append([{"role": msg["role"], "content": msg["content"]} for msg in current_batch])
                current_batch = [message]
                current_tokens = msg_tokens
            else:
                current_batch.append(message)
                current_tokens += msg_tokens
        
        if current_batch:
            batches.append([{"role": msg["role"], "content": msg["content"]} for msg in current_batch])
        
        return batches
    
    def validate_context(self) -> bool:
        """Validate context before API calls"""
        if not self.message_buffer:
            return False
        
        for message in self.message_buffer:
            if not isinstance(message, dict):
                return False
            if "role" not in message or "content" not in message:
                return False
            if message["role"] not in ["user", "assistant"]:
                return False
        
        return True
    
    def compress_context(self) -> List[Dict[str, Any]]:
        """Compress context for very long conversations"""
        if len(self.message_buffer) <= 20:
            return self.message_buffer
        
        # Keep first few messages (conversation start)
        start_messages = self.message_buffer[:3]
        
        # Keep important messages
        important_messages = [msg for msg in self.message_buffer if msg.get("is_system_important", False)]
        
        # Keep recent messages
        recent_messages = self.message_buffer[-10:]
        
        # Combine without duplicates
        compressed = []
        added_indices = set()
        
        for msg_list in [start_messages, important_messages, recent_messages]:
            for msg in msg_list:
                original_index = self.message_buffer.index(msg)
                if original_index not in added_indices:
                    compressed.append(msg)
                    added_indices.add(original_index)
        
        # Sort by original order
        compressed.sort(key=lambda x: self.message_buffer.index(x))
        
        return compressed


class ClaudeToolManager:
    """Tool management for Claude API replacing LangGraph tool functionality"""
    
    def __init__(self, credentials: ClaudeCredentials):
        """Initialize tool manager with Claude credentials"""
        self.credentials = credentials
        self.available_tools: Dict[str, Callable] = {}
        self.tool_schemas: Dict[str, Dict[str, Any]] = {}
        self.api_client = ClaudeAPIClient(credentials)
    
    def register_tool(self, name: str, func: Callable, schema: Optional[Dict[str, Any]] = None) -> None:
        """Register a tool function with optional schema"""
        self.available_tools[name] = func
        
        if schema:
            self.tool_schemas[name] = schema
        else:
            # Auto-generate schema from function signature
            self.tool_schemas[name] = self._generate_schema_from_function(name, func)
    
    def _generate_schema_from_function(self, name: str, func: Callable) -> Dict[str, Any]:
        """Generate JSON schema from function signature"""
        signature = inspect.signature(func)
        docstring = inspect.getdoc(func) or f"Tool function: {name}"
        
        properties = {}
        required = []
        
        for param_name, param in signature.parameters.items():
            param_type = self._python_type_to_json_type(param.annotation)
            
            properties[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
            
            # Check if parameter has default value
            if param.default == param.empty:
                required.append(param_name)
            else:
                properties[param_name]["default"] = param.default
        
        return {
            "name": name,
            "description": docstring,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def _python_type_to_json_type(self, python_type) -> str:
        """Convert Python type annotation to JSON schema type"""
        if python_type == str:
            return "string"
        elif python_type == int:
            return "integer"
        elif python_type == float:
            return "number"
        elif python_type == bool:
            return "boolean"
        elif python_type == list:
            return "array"
        elif python_type == dict:
            return "object"
        else:
            # Handle generic types and fallback
            type_str = str(python_type)
            if 'dict' in type_str.lower():
                return "object"
            elif 'list' in type_str.lower():
                return "array"
            return "string"  # Default fallback
    
    def validate_tool_input(self, tool_name: str, input_data: Dict[str, Any]) -> bool:
        """Validate tool input against schema"""
        if tool_name not in self.tool_schemas:
            return False
        
        schema = self.tool_schemas[tool_name]
        input_schema = schema["input_schema"]
        
        # Check required parameters
        required_params = input_schema.get("required", [])
        for param in required_params:
            if param not in input_data:
                return False
        
        # Check parameter types
        properties = input_schema.get("properties", {})
        for param_name, param_value in input_data.items():
            if param_name in properties:
                expected_type = properties[param_name]["type"]
                if not self._validate_parameter_type(param_value, expected_type):
                    return False
        
        return True
    
    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type against JSON schema type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type, str)
        return isinstance(value, expected_python_type)
    
    def execute_tool(self, tool_name: str, input_data: Dict[str, Any]) -> Any:
        """Execute a tool with given input"""
        if tool_name not in self.available_tools:
            raise ClaudeAPIError(f"Tool '{tool_name}' not found")
        
        if not self.validate_tool_input(tool_name, input_data):
            raise ClaudeAPIError(f"Tool input validation failed for '{tool_name}'")
        
        try:
            func = self.available_tools[tool_name]
            result = func(**input_data)
            return result
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return {"error": str(e), "tool": tool_name}
    
    def format_tool_result(self, tool_use_id: str, tool_name: str, result: Any) -> Dict[str, Any]:
        """Format tool result for Claude API"""
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": json.dumps(result, default=str)
        }
    
    def get_tools_for_claude_api(self) -> List[Dict[str, Any]]:
        """Get tools formatted for Claude API"""
        return list(self.tool_schemas.values())
    
    async def send_message_with_tools(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_iterations: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """Send message to Claude with tool support and handle tool execution cycles"""
        tools = self.get_tools_for_claude_api() if self.available_tools else None
        conversation_messages = messages.copy()
        
        for iteration in range(max_iterations):
            # Send message to Claude
            response = await self.api_client.send_message(
                messages=conversation_messages,
                system=system,
                tools=tools,
                **kwargs
            )
            
            # Check if Claude wants to use tools
            if response.get("stop_reason") == "tool_use":
                tool_results = []
                
                # Execute each requested tool
                for content in response.get("content", []):
                    if content.get("type") == "tool_use":
                        tool_name = content["name"]
                        tool_input = content["input"]
                        tool_use_id = content["id"]
                        
                        # Execute the tool
                        result = self.execute_tool(tool_name, tool_input)
                        
                        # Format result for Claude
                        tool_result = self.format_tool_result(tool_use_id, tool_name, result)
                        tool_results.append(tool_result)
                
                # Add Claude's response and tool results to conversation
                conversation_messages.append({
                    "role": "assistant",
                    "content": response["content"]
                })
                
                conversation_messages.append({
                    "role": "user",
                    "content": tool_results
                })
                
                # Continue conversation for next iteration
                continue
            else:
                # No tool use, return final response
                return response 