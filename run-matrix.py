import json
import os
import signal
import subprocess
import time
from pathlib import Path

root = Path(__file__).parent
logs = root / 'logs'
logs.mkdir(exist_ok=True)

base_env = os.environ.copy()
base_env.pop('CI', None)

cases = [
    {
        'name': 'versions',
        'cmd': ['bash', '-lc', 'bun --revision && node --version && bun vitest --version && bun pm ls --depth 0'],
        'timeout': 20,
    },
    {
        'name': 'pw-chromium-bun-runtime-headless',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--browser.headless', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-firefox-bun-runtime-headless',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.firefox.config.ts', '--browser.headless', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-webkit-bun-runtime-headless',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.webkit.config.ts', '--browser.headless', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-chromium-bun-runtime-headed',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-firefox-bun-runtime-headed',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.firefox.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-webkit-bun-runtime-headed',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.webkit.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-chromium-bun-runtime-headed-debug',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--reporter=verbose'],
        'timeout': 35,
        'env': {'DEBUG': 'pw:browser,pw:protocol,vitest:*'},
    },
    {
        'name': 'pw-chromium-node-via-bun-headed',
        'cmd': ['bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-firefox-node-via-bun-headed',
        'cmd': ['bun', 'vitest', 'run', '--config', 'vitest.playwright.firefox.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-webkit-node-via-bun-headed',
        'cmd': ['bun', 'vitest', 'run', '--config', 'vitest.playwright.webkit.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-chromium-direct-node-headed',
        'cmd': ['node', 'node_modules/vitest/vitest.mjs', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'preview-bun-runtime',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.preview.config.ts', '--reporter=verbose'],
        'timeout': 25,
    },
    {
        'name': 'preview-node-via-bun',
        'cmd': ['bun', 'vitest', 'run', '--config', 'vitest.preview.config.ts', '--reporter=verbose'],
        'timeout': 25,
    },
    {
        'name': 'preview-direct-node',
        'cmd': ['node', 'node_modules/vitest/vitest.mjs', 'run', '--config', 'vitest.preview.config.ts', '--reporter=verbose'],
        'timeout': 25,
    },
    {
        'name': 'pw-chromium-explicit-headed-no-screenshots',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium-explicit-headed.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-chromium-no-deps',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium-no-deps.config.ts', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-chromium-pool-threads',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--pool=threads', '--reporter=verbose'],
        'timeout': 35,
    },
    {
        'name': 'pw-chromium-pool-forks',
        'cmd': ['bun', '--bun', 'vitest', 'run', '--config', 'vitest.playwright.chromium.config.ts', '--pool=forks', '--reporter=verbose'],
        'timeout': 35,
    },
]


def snapshot(pgid: int) -> str:
    ps = subprocess.run(
        ['ps', '-axo', 'pid,ppid,pgid,stat,command'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ).stdout
    lines = []
    for line in ps.splitlines():
        parts = line.split(None, 4)
        if len(parts) >= 3 and parts[2] == str(pgid):
            lines.append(line)
    return '\n'.join(lines)


results = []

for case in cases:
    name = case['name']
    cmd = case['cmd']
    timeout = case['timeout']
    env = base_env.copy()
    env.update(case.get('env', {}))
    log_path = logs / f'{name}.log'
    print(f'===== {name} =====', flush=True)
    started = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    chunks = []
    snapshots = []
    timed_out = False
    next_snapshot = 2.0

    while True:
        if proc.poll() is not None:
            break
        elapsed = time.monotonic() - started
        if elapsed >= timeout:
            timed_out = True
            snapshots.append((elapsed, snapshot(proc.pid)))
            os.killpg(proc.pid, signal.SIGTERM)
            break
        if elapsed >= next_snapshot:
            snapshots.append((elapsed, snapshot(proc.pid)))
            next_snapshot += 5.0
        time.sleep(0.2)

    try:
        out, _ = proc.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, _ = proc.communicate(timeout=3)

    elapsed = time.monotonic() - started
    if out:
        chunks.append(out)

    lingering = snapshot(proc.pid)
    if lingering:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    body = []
    body.append(f'$ {" ".join(cmd)}')
    if case.get('env'):
        body.append(f'env: {case["env"]}')
    body.append('')
    body.append('--- output ---')
    body.append(''.join(chunks))
    body.append('--- process snapshots ---')
    for snap_elapsed, snap in snapshots:
        body.append(f'[{snap_elapsed:.1f}s]')
        body.append(snap or '(none)')
    body.append('--- lingering after communicate ---')
    body.append(lingering or '(none)')
    body.append(f'--- exit={proc.returncode} timeout={timed_out} elapsed={elapsed:.2f}s ---')
    log_path.write_text('\n'.join(body), encoding='utf-8')

    summary = {
        'name': name,
        'cmd': cmd,
        'exit': proc.returncode,
        'timeout': timed_out,
        'elapsed': round(elapsed, 2),
        'log': str(log_path),
    }
    results.append(summary)
    print(json.dumps(summary), flush=True)

(logs / 'summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
