
import os
import asyncio
import httpx

from mcp.server.fastmcp import FastMCP

ASHNA_BASE_URL = os.getenv(
    "ASHNA_BASE_URL",
    "https://api.ashna.ai/v1/api"
).rstrip("/")

ASHNA_API_KEY = os.getenv("ASHNA_API_KEY", "")
DEFAULT_MODEL = os.getenv("ASHNA_MODEL", "glm-5.3-flash")

MAX_RETRIES = 3
REQUEST_TIMEOUT = 120

# Limit simultaneous requests to Ashna API
REQUEST_LIMIT = asyncio.Semaphore(2)

mcp = FastMCP(
    "Ashna Roblox Studio Assistant",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)

ROBLOX_SYSTEM = """
You are an expert Roblox Studio and Luau assistant.
Help a beginner Roblox creator.

Return complete, copy-paste-ready Luau scripts when requested.
State the exact Explorer location and object type.
Prefer safe, server-authoritative designs.
Do not claim code was tested in Roblox unless it actually was.
Explain required Parts, Models, RemoteEvents, and folders.
Never ask the user to reveal API keys.
"""


async def ashna_request(method, endpoint, **kwargs):
    if not ASHNA_API_KEY:
        raise RuntimeError(
            "Missing ASHNA_API_KEY. "
            "Configure it in Render Environment Variables."
        )

    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {ASHNA_API_KEY}"

    async with REQUEST_LIMIT:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT
        ) as client:

            for attempt in range(MAX_RETRIES):
                try:
                    response = await client.request(
                        method,
                        f"{ASHNA_BASE_URL}{endpoint}",
                        headers=headers,
                        **kwargs
                    )

                    # Rate limit or temporary server error
                    if response.status_code == 429 or response.status_code >= 500:
                        if attempt == MAX_RETRIES - 1:
                            raise RuntimeError(
                                f"Ashna API HTTP {response.status_code}: "
                                f"{response.text[:1000]}"
                            )

                        retry_after = response.headers.get("Retry-After")

                        try:
                            delay = float(retry_after)
                        except (TypeError, ValueError):
                            delay = 3 * (2 ** attempt)

                        await asyncio.sleep(min(delay, 30))
                        continue

                    response.raise_for_status()
                    return response.json()

                except (httpx.TimeoutException, httpx.ConnectError):
                    if attempt == MAX_RETRIES - 1:
                        raise RuntimeError(
                            "Ashna API connection failed after retries."
                        )

                    await asyncio.sleep(2 ** attempt)

                except httpx.HTTPStatusError as exc:
                    raise RuntimeError(
                        f"Ashna API HTTP {exc.response.status_code}: "
                        f"{exc.response.text[:1000]}"
                    ) from exc

    raise RuntimeError("Ashna API request failed.")


async def ashna_chat(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: str = ROBLOX_SYSTEM
) -> str:

    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }

    data = await ashna_request(
        "POST",
        "/chat/completions",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return f"Unexpected Ashna API response: {data}"


@mcp.tool()
async def list_models() -> str:
    """List models available to the configured Ashna API key."""

    try:
        data = await ashna_request("GET", "/models")

        models = [
            item.get("id", "")
            for item in data.get("data", [])
            if item.get("id")
        ]

        return "\n".join(models) if models else str(data)

    except Exception as exc:
        return f"Model listing failed: {exc}"


@mcp.tool()
async def generate_luau(
    task: str,
    model: str = DEFAULT_MODEL
) -> str:
    """Generate a complete Roblox Luau script."""

    try:
        return await ashna_chat(
            "Create Roblox Luau code for this task:\n"
            + task
            + "\nReturn the complete script, exact Explorer placement, "
              "setup steps, and a short test checklist.",
            model=model
        )
    except Exception as exc:
        return f"Luau generation failed: {exc}"


@mcp.tool()
async def fix_luau_error(
    script: str,
    error_message: str,
    expected_behavior: str = "",
    model: str = DEFAULT_MODEL
) -> str:
    """Debug a Roblox Luau script."""

    prompt = (
        "Fix this Roblox Luau script. Return one complete replacement script.\n\n"
        f"ERROR:\n{error_message}\n\n"
        f"EXPECTED BEHAVIOR:\n{expected_behavior}\n\n"
        f"SCRIPT:\n```lua\n{script}\n```\n"
        "Explain the root cause, exact placement, and how to test it. "
        "Do not omit unchanged code."
    )

    try:
        return await ashna_chat(prompt, model=model)
    except Exception as exc:
        return f"Luau debugging failed: {exc}"


@mcp.tool()
async def create_creature(
    name: str,
    creature_description: str,
    rank: str = "Mortal",
    model: str = DEFAULT_MODEL
) -> str:
    """Design a Roblox cultivation beast."""

    prompt = (
        f"Design a Roblox Cultivation World beast named {name}.\n"
        f"Rank: {rank}\n"
        f"Description: {creature_description}\n"
        "Provide appearance, colors, body parts, scale, stats, abilities, "
        "AI behavior, and a complete beginner-friendly Luau implementation "
        "with exact Explorer placement."
    )

    try:
        return await ashna_chat(prompt, model=model)
    except Exception as exc:
        return f"Creature creation failed: {exc}"


@mcp.tool()
async def create_game_system(
    system_name: str,
    requirements: str,
    model: str = DEFAULT_MODEL
) -> str:
    """Create a complete Roblox game system."""

    prompt = (
        f"Build this Roblox system: {system_name}\n"
        f"Requirements:\n{requirements}\n"
        "Give a complete architecture, exact Explorer hierarchy, "
        "every required full script, RemoteEvents/RemoteFunctions setup, "
        "and mobile-friendly testing steps. "
        "Use server-side validation for important gameplay actions."
    )

    try:
        return await ashna_chat(prompt, model=model)
    except Exception as exc:
        return f"Game system creation failed: {exc}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
