# Ashna AI → Roblox Studio MCP Bridge

This project exposes Ashna AI through an MCP server with Roblox-focused tools.

## Tools
- `list_models` — list models available to your Ashna API key.
- `generate_luau` — generate complete Roblox Luau scripts.
- `fix_luau_error` — repair a script and return a complete replacement.
- `create_creature` — design Cultivation World beasts and their Roblox implementation.
- `create_game_system` — create systems such as inventory, combat, cultivation, pets, UI, and saving.

## Important security warning
A key was pasted into a chat earlier. Revoke that key in Ashna AI and create a new one.
Never put the new key in this project, a public GitHub repository, or a screenshot.
Set it only as a private environment variable on your hosting provider.

A public MCP endpoint can let other people use your Ashna API quota if it is not protected.
Before deploying publicly, configure authentication/access control supported by your MCP host.
Do not choose "No authentication" for a publicly reachable production server unless you
understand and accept that risk. This starter is a prototype and does not implement OAuth.

## Deploy (computer/browser required for easiest route)
1. Create a private GitHub repository and upload these project files.
2. Create a web service on Render and connect the repository.
3. Render can use `render.yaml`; otherwise set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `python server.py`
4. In Render → Environment, add:
   - `ASHNA_API_KEY` = your newly rotated Ashna API key
   - `ASHNA_MODEL` = a model ID available to your key, e.g. `glm-5.3-flash`
   - `ASHNA_BASE_URL` = `https://api.ashna.ai/v1/api`
5. Deploy. Render gives you a public service domain.
6. The MCP endpoint for this server is:
   `https://YOUR-SERVICE.onrender.com/mcp`
   Replace the hostname with your actual Render hostname.

## Add to ChatGPT
In ChatGPT's Apps / custom MCP server screen:
- Name: Ashna Roblox Assistant
- Server URL: your deployed `https://...onrender.com/mcp` URL
- Authentication: use a supported secure authentication method once configured.
- Do not paste your Ashna API key into the MCP URL field.

Custom MCP availability and authentication options depend on your ChatGPT plan/workspace. If ChatGPT requires OAuth and does not accept a static bearer token, this starter needs an OAuth-capable gateway before it can be connected.

## Run locally
Python 3.10+:
```bash
pip install -r requirements.txt
```
Set environment variables (never commit them), then:
```bash
python server.py
```
The MCP endpoint is `http://localhost:8000/mcp`.

## API details
Ashna uses the OpenAI-compatible Chat Completions endpoint:
`POST https://api.ashna.ai/v1/api/chat/completions`
and model discovery:
`GET https://api.ashna.ai/v1/api/models`

This project forwards requests to Ashna. It does not access or edit your Roblox place automatically.
Generated scripts must be reviewed and tested in Roblox Studio.
