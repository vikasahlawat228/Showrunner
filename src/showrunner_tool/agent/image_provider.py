"""Multi-model image provider abstraction.

Supports Gemini Imagen, DALL-E, Stable Diffusion, and Flux
with provider-specific prompt adaptation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ImageProviderType(str, Enum):
    GEMINI = "gemini"
    DALLE = "dalle"
    STABLE_DIFFUSION = "stable_diffusion"
    FLUX = "flux"


class ImageResult(BaseModel):
    """Result from an image generation request."""

    provider: ImageProviderType
    model: str = ""
    prompt_used: str = ""
    negative_prompt: str = ""
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    seed: Optional[int] = None
    status: str = "pending"  # pending, generating, success, failed
    error_message: str = ""
    generation_time_seconds: Optional[float] = None
    metadata: dict = Field(default_factory=dict)


class ImageProvider(ABC):
    """Abstract base class for image generation providers."""

    provider_type: ImageProviderType

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> ImageResult:
        """Generate an image from a text prompt."""
        ...

    @abstractmethod
    def adapt_prompt(self, generic_prompt: str) -> str:
        """Adapt a generic prompt to this provider's optimal format."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""
        ...


class GeminiImagenProvider(ImageProvider):
    """Google Gemini Imagen image generation provider."""

    provider_type = ImageProviderType.GEMINI

    def __init__(self, api_key: Optional[str] = None, model: str = "imagen-4"):
        import os
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> ImageResult:
        """Generate using Gemini Imagen API."""
        if not self.is_available():
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=prompt,
                status="failed",
                error_message="GEMINI_API_KEY not set",
            )

        adapted = self.adapt_prompt(prompt)

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            imagen = genai.ImageGenerationModel(self.model)

            result = imagen.generate_images(
                prompt=adapted,
                number_of_images=1,
                aspect_ratio=_aspect_ratio_from_dims(width, height),
            )

            if result.images and output_path:
                result.images[0].save(str(output_path))

            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                image_path=str(output_path) if output_path else None,
                status="success",
            )
        except Exception as e:
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                status="failed",
                error_message=str(e),
            )

    def adapt_prompt(self, generic_prompt: str) -> str:
        """Gemini works well with detailed, descriptive prompts."""
        return generic_prompt

    def is_available(self) -> bool:
        return bool(self.api_key)


class DalleProvider(ImageProvider):
    """OpenAI DALL-E image generation provider."""

    provider_type = ImageProviderType.DALLE

    def __init__(self, api_key: Optional[str] = None, model: str = "dall-e-3"):
        import os
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> ImageResult:
        if not self.is_available():
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=prompt,
                status="failed",
                error_message="OPENAI_API_KEY not set",
            )

        adapted = self.adapt_prompt(prompt)
        size = _dalle_size(width, height)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.images.generate(
                model=self.model,
                prompt=adapted,
                size=size,
                quality="hd",
                n=1,
            )

            image_url = response.data[0].url if response.data else None

            if image_url and output_path:
                import urllib.request
                urllib.request.urlretrieve(image_url, str(output_path))

            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                image_url=image_url,
                image_path=str(output_path) if output_path and image_url else None,
                status="success",
            )
        except Exception as e:
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                status="failed",
                error_message=str(e),
            )

    def adapt_prompt(self, generic_prompt: str) -> str:
        """DALL-E prefers concise, focused prompts."""
        # Truncate extremely long prompts for DALL-E
        if len(generic_prompt) > 4000:
            return generic_prompt[:3900] + "..."
        return generic_prompt

    def is_available(self) -> bool:
        return bool(self.api_key)


class StableDiffusionProvider(ImageProvider):
    """Stable Diffusion provider (via local API or Stability AI)."""

    provider_type = ImageProviderType.STABLE_DIFFUSION

    def __init__(self, api_url: str = "http://127.0.0.1:7860", model: str = "sd-xl"):
        self.api_url = api_url
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> ImageResult:
        adapted = self.adapt_prompt(prompt)

        try:
            import requests
            import base64

            payload = {
                "prompt": adapted,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "steps": kwargs.get("steps", 30),
                "cfg_scale": kwargs.get("cfg_scale", 7),
            }
            if seed is not None:
                payload["seed"] = seed

            response = requests.post(
                f"{self.api_url}/sdapi/v1/txt2img",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("images") and output_path:
                img_data = base64.b64decode(data["images"][0])
                output_path.write_bytes(img_data)

            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                negative_prompt=negative_prompt,
                image_path=str(output_path) if output_path else None,
                seed=data.get("info", {}).get("seed"),
                status="success",
            )
        except Exception as e:
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                status="failed",
                error_message=str(e),
            )

    def adapt_prompt(self, generic_prompt: str) -> str:
        """SD uses comma-separated tags. Convert narrative to tags."""
        # Basic adaptation: keep as-is but add quality tags
        quality_suffix = ", masterpiece, best quality, detailed, sharp focus"
        return generic_prompt + quality_suffix

    def is_available(self) -> bool:
        try:
            import requests
            resp = requests.get(f"{self.api_url}/sdapi/v1/sd-models", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False


class FluxProvider(ImageProvider):
    """Flux image generation provider (via API)."""

    provider_type = ImageProviderType.FLUX

    def __init__(self, api_key: Optional[str] = None, model: str = "flux-1.1-pro"):
        import os
        self.api_key = api_key or os.environ.get("BFL_API_KEY", "")
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        output_path: Optional[Path] = None,
        **kwargs,
    ) -> ImageResult:
        if not self.is_available():
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=prompt,
                status="failed",
                error_message="BFL_API_KEY not set",
            )

        adapted = self.adapt_prompt(prompt)

        try:
            import requests

            payload = {
                "prompt": adapted,
                "width": width,
                "height": height,
            }
            if seed is not None:
                payload["seed"] = seed

            headers = {"X-Key": self.api_key}
            response = requests.post(
                "https://api.bfl.ml/v1/flux-pro-1.1",
                json=payload,
                headers=headers,
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()

            image_url = data.get("sample")
            if image_url and output_path:
                import urllib.request
                urllib.request.urlretrieve(image_url, str(output_path))

            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                image_url=image_url,
                image_path=str(output_path) if output_path and image_url else None,
                status="success",
            )
        except Exception as e:
            return ImageResult(
                provider=self.provider_type,
                model=self.model,
                prompt_used=adapted,
                status="failed",
                error_message=str(e),
            )

    def adapt_prompt(self, generic_prompt: str) -> str:
        """Flux works well with natural language descriptions."""
        return generic_prompt

    def is_available(self) -> bool:
        return bool(self.api_key)


# ── Provider Registry ─────────────────────────────────────────

_PROVIDERS: dict[ImageProviderType, type[ImageProvider]] = {
    ImageProviderType.GEMINI: GeminiImagenProvider,
    ImageProviderType.DALLE: DalleProvider,
    ImageProviderType.STABLE_DIFFUSION: StableDiffusionProvider,
    ImageProviderType.FLUX: FluxProvider,
}


def get_provider(provider_type: ImageProviderType, **kwargs) -> ImageProvider:
    """Get an image provider instance by type."""
    cls = _PROVIDERS.get(provider_type)
    if not cls:
        raise ValueError(f"Unknown provider: {provider_type}")
    return cls(**kwargs)


def list_providers() -> list[ImageProviderType]:
    """List all available provider types."""
    return list(_PROVIDERS.keys())


# ── Helpers ───────────────────────────────────────────────────

def _aspect_ratio_from_dims(width: int, height: int) -> str:
    """Convert pixel dimensions to aspect ratio string."""
    ratio = width / height
    if abs(ratio - 1.0) < 0.1:
        return "1:1"
    elif abs(ratio - 16 / 9) < 0.1:
        return "16:9"
    elif abs(ratio - 9 / 16) < 0.1:
        return "9:16"
    elif abs(ratio - 4 / 3) < 0.1:
        return "4:3"
    elif abs(ratio - 3 / 4) < 0.1:
        return "3:4"
    return "1:1"


def _dalle_size(width: int, height: int) -> str:
    """Map to DALL-E supported sizes."""
    if width == height:
        return "1024x1024"
    elif width > height:
        return "1792x1024"
    else:
        return "1024x1792"
