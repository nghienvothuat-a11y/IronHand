"""Read-only MCP checks; never creates Tripo tasks or spends credits."""
import asyncio
import json
import os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
PROMPT = "Đúng là MCP server. Mày kết nối với Blender và Tripo để làm cho nhanh. Cần tao làm gì thì báo"


async def check(name, command, args, extra_env, calls):
    env = dict(os.environ, **extra_env)
    params = StdioServerParameters(command=command, args=args, env=env)
    report = {"server": name}
    with (ROOT / 'tools/mcp-setup' / f'{name}-verification.log').open('w') as log:
        async with stdio_client(params, errlog=log) as (read, write):
            async with ClientSession(read, write) as session:
                init = await session.initialize()
                report['server_info'] = init.serverInfo.model_dump()
                report['tools'] = [t.name for t in (await session.list_tools()).tools]
                report['checks'] = {}
                for tool, arguments in calls:
                    result = await session.call_tool(tool, arguments)
                    report['checks'][tool] = result.model_dump(mode='json')
    return report


async def main():
    reports = await asyncio.gather(
        check('blender', '/Users/mrk/.local/bin/mcp-for-blender',
              ['--host', '127.0.0.1', '--port', '9876'],
              {'BLENDER_MCP_DISABLE_TELEMETRY': '1'},
              [('get_addon_status', {'user_prompt': PROMPT}),
               ('get_scene_info', {'user_prompt': PROMPT}),
               ('get_object_info', {'object_name': 'IronHand_Rig', 'user_prompt': PROMPT})]),
        check('tripo', '/opt/homebrew/bin/node',
              ['/Users/mrk/.local/share/ironhand-tripo/node_modules/tripo-cli/dist/cli.js', 'mcp'],
              {'TRIPO_NO_UPDATE_CHECK': '1'},
              [('tripo_balance', {})]),
    )
    path = ROOT / 'tools/mcp-setup/connection-report.json'
    path.write_text(json.dumps(reports, ensure_ascii=False, indent=2))
    for report in reports:
        print(report['server'], report['server_info'], len(report['tools']), 'tools')
        for name, result in report['checks'].items():
            print(name, json.dumps(result, ensure_ascii=False)[:6000])
    print('Report:', path)


asyncio.run(main())
