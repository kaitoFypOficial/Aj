import os
import httpx
from mcp.server.fastmcp import FastMCP

ASHNA_BASE_URL = os.getenv("ASHNA_BASE_URL", "https://api.ashna.ai/v1/api").rstrip("/")
ASHNA_API_KEY = os.getenv("ASHNA_API_KEY", "")
DEFAULT_MODEL = os.getenv("ASHNA_MODEL", "glm-5.3-flash")

mcp = FastMCP(
    "Ashna Roblox Studio Assistant",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)

ROBLOX_SYSTEM = """You are an expert Roblox Studio and Luau assistant.
Help a beginner Roblox creator. Return complete, copy-paste-ready Luau scripts
when requested, and state the exact Explorer location and object type.
Prefer safe, server-authoritative designs. Do not claim code was tested in Roblox
unless it actually was. Explain required Parts, Models, RemoteEvents, and folders.
When fixing code, preserve intended behavior and return the full corrected script
if the user asks for a whole script. Never ask the user to reveal API keys.
"""

async def ashna_chat(prompt: str, model: str = DEFAULT_MODEL, system: str = ROBLOX_SYSTEM) -> str:
    if not ASHNA_API_KEY:
        return "Server is missing ASHNA_API_KEY. Add it in your hosting provider's environment variables."
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {ASHNA_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{ASHNA_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return str(data)

@mcp.tool()
async def list_models() -> str:
    """List Ashna AI model IDs available to the API key configured on this server."""
    if not ASHNA_API_KEY:
        return "Server is missing ASHNA_API_KEY."
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            f"{ASHNA_BASE_URL}/models",
            headers={"Authorization": f"Bearer {ASHNA_API_KEY}"},
        )
        response.raise_for_status()
        data = response.json()
    models = [item.get("id", "") for item in data.get("data", []) if item.get("id")]
    return "\n".join(models) if models else str(data)

@mcp.tool()
async def generate_luau(task: str, model: str = DEFAULT_MODEL) -> str:
    """Generate a complete Roblox Luau script. Include the desired behavior and where it should run."""
    return await ashna_chat(
        "Create Roblox Luau code for this task:\n" + task +
        "\nReturn the complete script, exact Explorer placement, setup steps, and a short test checklist.",
        model=model,
    )

@mcp.tool()
async def fix_luau_error(script: str, error_message: str, expected_behavior: str = "", model: str = DEFAULT_MODEL) -> str:
    """Debug a Roblox Luau script and return a complete corrected replacement, not just fragments."""
    prompt = (
        "Fix this Roblox Luau script. Return one complete replacement script.\n\n"
        f"ERROR:\n{error_message}\n\nEXPECTED BEHAVIOR:\n{expected_behavior}\n\n"
        f"SCRIPT:\n```lua\n{script}\n```\n"
        "Explain the root cause, exact placement, and how to test it. Do not omit unchanged code."
    )
    return await ashna_chat(prompt, model=model)

@mcp.tool()
async def create_creature(name: str, creature_description: str, rank: str = "Mortal", model: str = DEFAULT_MODEL) -> str:
    """Design a cultivation beast and its Roblox implementation, including stats, abilities, colors, and scripts."""
    prompt = (
        f"Design a Roblox Cultivation World beast named {name}.\n"
        f"Rank: {rank}\nDescription: {creature_description}\n"
        "Provide appearance and color details, body parts/materials, scale, stats, abilities, "
        "AI behavior, and a complete beginner-friendly Luau implementation with exact Explorer placement."
    )
    return await ashna_chat(prompt, model=model)

@mcp.tool()
async def create_game_system(system_name: str, requirements: str, model: str = DEFAULT_MODEL) -> str:
    """Create a complete Roblox game system such as inventory, combat, cultivation, UI, pets, or saving."""
    prompt = (
        f"Build this Roblox system: {system_name}\nRequirements:\n{requirements}\n"
        "Give a complete architecture, exact Explorer hierarchy, every required full script, "
        "RemoteEvents/RemoteFunctions setup, and mobile-friendly testing steps. "
        "Use server-side validation for important gameplay actions."
    )
    return await ashna_chat(prompt, model=model)

if __name__ == "__main__":
    # Streamable HTTP MCP endpoint is /mcp.
    mcp.run(transport="streamable-http")
