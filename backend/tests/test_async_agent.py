import asyncio
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.agent import llm

async def main():
    response = await llm.generate(
        "Explain artificial intelligence in simple words."
    )
    print(response)

asyncio.run(main())
