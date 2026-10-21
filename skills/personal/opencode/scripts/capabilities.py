#!/usr/bin/env python3
"""Print a capability table for opencode models, from `opencode models --verbose`.

usage: capabilities.py [provider] [--json]
"""
import json
import subprocess
import sys

args = [a for a in sys.argv[1:] if not a.startswith("--")]
as_json = "--json" in sys.argv

out = subprocess.run(
    ["opencode", "models", *args, "--verbose"],
    capture_output=True, text=True, check=True,
).stdout

# The output is "<provider/model>" on its own line, followed by that model's JSON object.
models, decoder, i = [], json.JSONDecoder(), 0
while (start := out.find("{", i)) != -1:
    obj, i = decoder.raw_decode(out, start)
    caps = obj.get("capabilities", {})
    inp = caps.get("input", {})
    models.append({
        "model": f'{obj["providerID"]}/{obj["id"]}',
        "status": obj.get("status", ""),
        "image": inp.get("image", False),
        "pdf": inp.get("pdf", False),
        "audio": inp.get("audio", False),
        "tools": caps.get("toolcall", False),
        "reasoning": caps.get("reasoning", False),
        "context": obj.get("limit", {}).get("context", 0),
        "free": obj.get("cost", {}).get("input", 1) == 0 and obj.get("cost", {}).get("output", 1) == 0,
    })

if as_json:
    print(json.dumps(models, indent=2))
    sys.exit()

yes = lambda v: "yes" if v else "-"
print("| model | image | pdf | audio | tools | reasoning | context | free |")
print("|---|---|---|---|---|---|---|---|")
for m in models:
    print(f'| `{m["model"]}` | {yes(m["image"])} | {yes(m["pdf"])} | {yes(m["audio"])} '
          f'| {yes(m["tools"])} | {yes(m["reasoning"])} | {m["context"] // 1000}k | {yes(m["free"])} |')
