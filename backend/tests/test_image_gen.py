import sys
import os
import asyncio
import base64

# --------------------------------------------------
# FIX PYTHON PATH (so `app` is found)
# --------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.agent import llm

# Optional: clean LiteLLM warning
from litellm.llms.custom_httpx.async_client_cleanup import (
    close_litellm_async_clients
)


async def test_image_generation():
    session_id = "test-session-1"
    prompt = "Generate a futuristic fashion model"

    # --------------------------------------------------
    # CALL AGENT
    # --------------------------------------------------
    result = await llm.generate(session_id, prompt)

    # --------------------------------------------------
    # ASSERTIONS
    # --------------------------------------------------
    assert isinstance(result, dict), "Result should be a dict"
    assert result["type"] == "image", "Expected image output"
    assert "image_base64" in result, "Missing image_base64"

    print("✅ Image generation test PASSED")
    print("Prompt:", result["prompt"])
    print("Base64 preview:", result["image_base64"][:60])

    # --------------------------------------------------
    # SAVE IMAGE TO FILE
    # --------------------------------------------------
    image_bytes = base64.b64decode(result["image_base64"])

    output_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "generated_image.png"
    )

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(f"🖼 Image saved at: {os.path.abspath(output_path)}")

    # --------------------------------------------------
    # CLEANUP (removes LiteLLM warning)
    # --------------------------------------------------
    await close_litellm_async_clients()


if __name__ == "__main__":
    asyncio.run(test_image_generation())
