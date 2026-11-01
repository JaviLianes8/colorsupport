"""External consumer programs for compatibility with the published release."""

from __future__ import annotations

SNAPSHOT = """
import json, pickle, random
from pathlib import Path
from colorsupport import ColorLevel, Detection, detect, level, supports_color

class Stream:
    def __init__(self, tty): self.tty = tty
    def isatty(self): return self.tty

rng = random.Random(20261101)
choices = {
    'TERM': ['', 'dumb', 'xterm', 'foot', 'xterm-256color', 'wezterm'],
    'COLORTERM': ['', 'truecolor', '24bit', 'yes'],
    'NO_COLOR': ['', '1'], 'FORCE_COLOR': ['', '0', 'false', 'yes', ' 2 ', '3', '99'],
    'CI': ['', '1'], 'GITHUB_ACTIONS': [''], 'CLICOLOR': ['0', '1'],
    'CLICOLOR_FORCE': ['', '1'], 'WT_SESSION': [''],
}
records = []
for _ in range(2000):
    env = {k: rng.choice(v) for k, v in choices.items() if rng.randrange(4) == 0}
    stream = Stream(bool(rng.randrange(2)))
    options = dict(env=env, platform=rng.choice(['linux', 'win32']),
        vt=bool(rng.randrange(2)), windows_build=rng.choice([0, 10585, 10586, 14930, 14931]),
        when=rng.choice(['auto', 'always', 'never']), terminfo=lambda t: 256)
    found = detect(stream, **options)
    records.append([int(found.level), found.reason, str(found), int(level(stream, **options)),
        supports_color(stream, **options)])
path = Path('value.pickle')
value = Detection(ColorLevel.ANSI256, 'saved in 0.1.0')
if path.exists():
    assert pickle.loads(path.read_bytes()) == value
else:
    path.write_bytes(pickle.dumps(value))
print(json.dumps(records))
"""

CHANGES = """
import colorsupport as cs
old = cs.__version__ == '0.1.0'

def error(call):
    try: call()
    except Exception as exc: return type(exc).__name__, str(exc)
    return None, None

kind, message = error(lambda: cs.ColorLevel.parse('secret-token'))
assert kind == 'ValueError' and ('secret-token' in message) == old
kind, message = error(lambda: cs.detect(when='secret-token'))
assert kind == 'ValueError' and ('secret-token' in message) == old
assert error(lambda: cs.terminfo_colors(None, {}))[0] == (None if old else 'TypeError')
assert error(lambda: cs.terminfo_colors(7, {}))[0] == ('AttributeError' if old else 'TypeError')
kind, message = error(lambda: cs.ColorLevel.parse(type('x' * 100, (), {})()))
assert kind == 'TypeError' and (len(message) > 100) == old

class Tty:
    def isatty(self): return True

huge = 1 << 100000
for options in [dict(platform='win32', vt=True, windows_build=huge, env={}),
                dict(platform='linux', terminfo=lambda t: huge, env={'TERM': 'foot'})]:
    if old:
        assert error(lambda: cs.detect(Tty(), **options))[0] == 'ValueError'
    else:
        found = cs.detect(Tty(), **options)
        assert found.level is cs.ColorLevel.TRUECOLOR and 'a large integer' in found.reason
assert cs.detect.__annotations__['stream'] == ('Any' if old else 'object')
print('upgrade changes verified')
"""
