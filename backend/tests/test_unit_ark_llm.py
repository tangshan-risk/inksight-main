"""
Unit tests for Volcengine Ark LLM integration (no real API calls).
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from openai import AsyncOpenAI

from core.content import (
    LLM_CONFIGS,
    _get_client,
    LLMClient,
    call_llm,
)
from core.config import get_default_llm_model_for_provider
from core.errors import LLMKeyMissingError


class TestArkLLMConfig:
    """Test Ark LLM configuration."""

    def test_ark_config_exists(self):
        """Test that 'ark' provider is defined in LLM_CONFIGS."""
        assert "ark" in LLM_CONFIGS

    def test_ark_base_url(self):
        """Test Ark base_url is correctly configured."""
        assert LLM_CONFIGS["ark"]["base_url"] == "https://ark.cn-beijing.volces.com/api/v3"

    def test_ark_models_list(self):
        """Test Ark models are correctly configured."""
        models = LLM_CONFIGS["ark"]["models"]
        assert "doubao-seed-2-1-pro-260628" in models
        assert "doubao-1.5-pro" in models
        assert "doubao-1.5-flash" in models
        assert "doubao-1.5-vision" in models
        assert "doubao-seedream-5-0-260128" in models

    def test_ark_model_max_tokens(self):
        """Test Ark models have correct max_tokens."""
        for model_name, model_config in LLM_CONFIGS["ark"]["models"].items():
            assert model_config["max_tokens"] == 4096

    def test_ark_model_names(self):
        """Test Ark model display names."""
        assert LLM_CONFIGS["ark"]["models"]["doubao-seed-2-1-pro-260628"]["name"] == "豆包 Seed 2.1 Pro"
        assert LLM_CONFIGS["ark"]["models"]["doubao-1.5-pro"]["name"] == "豆包 1.5 Pro"
        assert LLM_CONFIGS["ark"]["models"]["doubao-1.5-flash"]["name"] == "豆包 1.5 Flash"


class TestArkDefaultModel:
    """Test default model mapping for Ark provider."""

    def test_ark_default_model(self):
        """Test that Ark provider returns correct default model."""
        model = get_default_llm_model_for_provider("ark")
        assert model == "doubao-seed-2-1-pro-260628"

    def test_ark_default_model_case_insensitive(self):
        """Test Ark provider name is case insensitive."""
        assert get_default_llm_model_for_provider("ARK") == "doubao-seed-2-1-pro-260628"
        assert get_default_llm_model_for_provider("Ark") == "doubao-seed-2-1-pro-260628"


class TestArkClientCreation:
    """Test Ark LLM client creation."""

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": ""})
    def test_get_client_ark(self):
        """Test creating client for Ark provider."""
        client, max_tokens, resolved_model = _get_client(provider="ark", model="doubao-seed-2-1-pro-260628")
        assert isinstance(client, AsyncOpenAI)
        assert max_tokens == 4096
        assert resolved_model == "doubao-seed-2-1-pro-260628"
        assert client.base_url.host == "ark.cn-beijing.volces.com"

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": ""})
    def test_get_client_ark_with_custom_model(self):
        """Test creating client for Ark with custom model."""
        client, max_tokens, resolved_model = _get_client(provider="ark", model="doubao-1.5-flash")
        assert isinstance(client, AsyncOpenAI)
        assert max_tokens == 4096
        assert resolved_model == "doubao-1.5-flash"

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": "ep-test-endpoint"})
    def test_get_client_ark_with_endpoint(self):
        """Test creating client for Ark with endpoint ID."""
        client, max_tokens, resolved_model = _get_client(provider="ark", model="doubao-seed-2-1-pro-260628")
        assert isinstance(client, AsyncOpenAI)
        assert max_tokens == 4096
        assert resolved_model == "ep-test-endpoint"
        assert client.base_url.host == "ark.cn-beijing.volces.com"

    def test_get_client_ark_missing_api_key(self):
        """Test that missing Ark API key raises LLMKeyMissingError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMKeyMissingError) as exc_info:
                _get_client(provider="ark", model="doubao-seed-2-1-pro-260628")
            assert "ark" in str(exc_info.value).lower()

    def test_get_client_ark_invalid_api_key(self):
        """Test that placeholder Ark API key raises LLMKeyMissingError."""
        with patch.dict("os.environ", {"ARK_API_KEY": "sk-your-ark-api-key-here"}):
            with pytest.raises(LLMKeyMissingError):
                _get_client(provider="ark", model="doubao-seed-2-1-pro-260628")


class TestArkLLMClient:
    """Test LLMClient with Ark provider."""

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": ""})
    def test_llm_client_init_ark(self):
        """Test LLMClient initialization with Ark provider."""
        client = LLMClient(provider="ark", model="doubao-seed-2-1-pro-260628")
        assert client.provider == "ark"
        assert client.model == "doubao-seed-2-1-pro-260628"
        assert client._resolved_model == "doubao-seed-2-1-pro-260628"

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": "ep-test-endpoint"})
    def test_llm_client_init_ark_with_endpoint(self):
        """Test LLMClient initialization with Ark endpoint ID."""
        client = LLMClient(provider="ark", model="doubao-seed-2-1-pro-260628")
        assert client.provider == "ark"
        assert client.model == "doubao-seed-2-1-pro-260628"
        assert client._resolved_model == "ep-test-endpoint"

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123"})
    @pytest.mark.asyncio
    async def test_llm_client_call_ark(self):
        """Test LLMClient.call with mocked Ark API response."""
        client = LLMClient(provider="ark", model="doubao-seed-2-1-pro-260628")
        
        mock_choice = MagicMock()
        mock_choice.message.content = "这是豆包的回复"
        mock_choice.finish_reason = "stop"
        
        mock_usage = MagicMock()
        mock_usage.total_tokens = 42
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        with patch.object(client._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            result = await client.call("你好")
            assert result == "这是豆包的回复"
            mock_create.assert_called_once()

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": "ep-test-endpoint"})
    @pytest.mark.asyncio
    async def test_llm_client_call_ark_with_endpoint(self):
        """Test LLMClient.call with endpoint ID uses correct model parameter."""
        client = LLMClient(provider="ark", model="doubao-seed-2-1-pro-260628")
        
        mock_choice = MagicMock()
        mock_choice.message.content = "通过接入点调用的回复"
        mock_choice.finish_reason = "stop"
        
        mock_usage = MagicMock()
        mock_usage.total_tokens = 42
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        with patch.object(client._client.chat.completions, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response
            result = await client.call("你好")
            assert result == "通过接入点调用的回复"
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["model"] == "ep-test-endpoint"


class TestArkCallLLM:
    """Test call_llm with Ark provider."""

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123"})
    @pytest.mark.asyncio
    async def test_call_llm_ark(self):
        """Test call_llm with Ark provider."""
        mock_choice = MagicMock()
        mock_choice.message.content = "豆包生成的内容"
        mock_choice.finish_reason = "stop"
        
        mock_usage = MagicMock()
        mock_usage.total_tokens = 100
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        with patch("core.content._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = (mock_client, 4096, "doubao-seed-2-1-pro-260628")
            
            result = await call_llm(
                prompt="测试提示词",
                llm_provider="ark",
                llm_model="doubao-seed-2-1-pro-260628",
            )
            
            assert result == "豆包生成的内容"
            mock_get_client.assert_called_once_with(
                "ark",
                "doubao-seed-2-1-pro-260628",
                api_key=None,
                base_url=None,
            )

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123", "ARK_ENDPOINT_ID": "ep-test-endpoint"})
    @pytest.mark.asyncio
    async def test_call_llm_ark_with_endpoint(self):
        """Test call_llm with Ark provider using endpoint ID."""
        mock_choice = MagicMock()
        mock_choice.message.content = "通过接入点生成的内容"
        mock_choice.finish_reason = "stop"
        
        mock_usage = MagicMock()
        mock_usage.total_tokens = 100
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        with patch("core.content._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = (mock_client, 4096, "ep-test-endpoint")
            
            result = await call_llm(
                prompt="测试提示词",
                llm_provider="ark",
                llm_model="doubao-seed-2-1-pro-260628",
            )
            
            assert result == "通过接入点生成的内容"
            mock_create = mock_client.chat.completions.create
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["model"] == "ep-test-endpoint"

    @patch.dict("os.environ", {"ARK_API_KEY": "sk-test-ark-key-123"})
    @pytest.mark.asyncio
    async def test_call_llm_ark_with_system_prompt(self):
        """Test call_llm with Ark provider and system prompt."""
        mock_choice = MagicMock()
        mock_choice.message.content = "带系统提示的回复"
        mock_choice.finish_reason = "stop"
        
        mock_usage = MagicMock()
        mock_usage.total_tokens = 150
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        
        with patch("core.content._get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = (mock_client, 4096, "doubao-seed-2-1-pro-260628")
            
            result = await call_llm(
                prompt="用户问题",
                system_prompt="你是一个专业助手",
                llm_provider="ark",
                llm_model="doubao-seed-2-1-pro-260628",
            )
            
            assert result == "带系统提示的回复"
            mock_create = mock_client.chat.completions.create
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert len(call_args["messages"]) == 2
            assert call_args["messages"][0]["role"] == "system"
            assert call_args["messages"][0]["content"] == "你是一个专业助手"
            assert call_args["messages"][1]["role"] == "user"
            assert call_args["messages"][1]["content"] == "用户问题"