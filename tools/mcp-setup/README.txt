IRONHAND — MCP CONNECTIONS
Verified 2026-10-04 on this Mac.

Blender
- Package: mcp-for-blender 2.1.3 (community project ahujasid/mcp-for-blender).
- Add-on installed in Blender 5.2 user scripts and enabled in saved preferences.
- Local socket: 127.0.0.1:9876. Auto-starts with Blender; no LAN binding.
- MCP: 36 tools; get_addon_status, get_scene_info, get_object_info passed.
- Verified live IronHand_MK1_Armour, IronHand_Rig and Palm_Muzzle in current scene.
- Telemetry disabled; premium generators not enabled.

Tripo
- Official tripo-cli 0.5.1, installed from npm in ~/.local/share/ironhand-tripo.
- Uses `tripo mcp` over stdio; independent of Blender socket.
- 5 tools: tripo_make, tripo_task_get, tripo_task_wait, tripo_balance, tripo_history.
- User completed browser device authorization; credentials kept in ~/.tripo/config.json (0600).
- MCP balance check passed: balance 0, frozen 0.
- No generation, paid API operation, purchase, or credit spend during setup.
- Tripo Studio subscription and API credits are separate. Existing exported models remain usable.
- Use an absolute output_dir for generation. Then import the local model through Blender MCP.
- Generation can block; Codex tool_timeout_sec is 1800 for this server.

Codex
- Both stdio servers added to ~/.codex/config.toml with absolute executable paths.
- Existing MCP servers preserved.
- Backup: ~/.codex/config.toml.before-ironhand-mcp-20261004-235400.bak
- This running turn did not hot-load the new native tool catalog. Reopen Codex to load it.
- Protocol checks already succeeded through a local MCP client against both actual servers.

Repeat read-only checks:
/Users/mrk/.local/share/uv/tools/mcp-for-blender/bin/python /Users/mrk/IronHand/tools/mcp-setup/verify_connections.py

Evidence: connection-report.json (contains no API key).
Remove Codex entries if needed: codex mcp remove blender; codex mcp remove tripo.
Do not restore the entire config backup over later unrelated settings changes.

Sources
https://github.com/ahujasid/mcp-for-blender
https://github.com/vast-enterprise/Tripo-API-CLI
https://www.npmjs.com/package/tripo-cli
https://developers.openai.com/codex/mcp
https://www.tripo3d.ai/help/api-plugins/tripo-studiotripo-api
