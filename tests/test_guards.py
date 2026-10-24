"""Breaks every guard in check_tox.py once on purpose and checks that it fails; a guard that
has never failed guards nothing. Builds a small fake library (one effect, one bundle that
embeds every effect) in a temporary folder, checks that the intact copy passes, then breaks one thing
per copy.

    uv run tests/test_guards.py
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_tox  # noqa: E402

LIB = os.path.join(os.path.dirname(HERE), 'lib', 'tox_build.py')
IDIOMS = os.path.join(os.path.dirname(HERE), 'docs', 'TD_IDIOMS.md')


def write(root, rel, data):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb' if isinstance(data, bytes) else 'w') as f:
        f.write(data)


def build(root, kind, name, tox, embeds=None):
    """What a builder does after its save checks: write the .tox and its manifest."""
    lib = check_tox.load_lib(root)
    d = os.path.join(root, kind, name)
    write(root, '{}/{}/{}.tox'.format(kind, name, name), tox)
    version = open(os.path.join(d, 'build_{}.py'.format(name))).read().split("VERSION = '")[1].split("'")[0]
    manifest = dict(version=version, sources_sha256=lib['digest'](root, lib['component_sources'](root, d)),
                    touchdesigner_build='2025.33230', tox_sha256=hashlib.sha256(tox).hexdigest(), tox_bytes=len(tox))
    if embeds:
        manifest['embeds'] = embeds
        manifest['embeds_all'] = True
    write(root, '{}/{}/{}.json'.format(kind, name, name), json.dumps(manifest, indent=2) + '\n')
    return manifest


def fixture(root):
    shutil.copytree(os.path.dirname(LIB), os.path.join(root, 'lib'), ignore=shutil.ignore_patterns('__pycache__'))
    lib = check_tox.load_lib(root)
    os.makedirs(os.path.join(root, 'docs'))
    shutil.copy(IDIOMS, os.path.join(root, 'docs', 'TD_IDIOMS.md'))
    demo = add_effect(root, 'demo')
    pages(root, 'bundles', 'reel')
    build(root, 'bundles', 'reel', b'reel tox v1', embeds={'demo': demo['tox_sha256']})


def pages(root, kind, name):
    """A component's builder, docs page, preview and ticked review."""
    lib = check_tox.load_lib(root)
    write(root, '{0}/{1}/build_{1}.py'.format(kind, name), "VERSION = '0.1.0'\n")
    write(root, 'docs/effects/{}.md'.format(name), '# {0}\n\n![{0}]({0}.gif)\n\n[Download]({1}) · saved in '
          'TouchDesigner 2025.33230\n'.format(name, lib['DOWNLOAD_URL'].format(name)))
    write(root, 'docs/effects/{}.gif'.format(name), b'GIF89a')
    write(root, '{}/{}/review.md'.format(kind, name),
          check_tox.review_template(root, name, '0.1.0').replace('- [ ]', '- [x]'))


def add_effect(root, name):
    """A complete, built effect."""
    pages(root, 'effects', name)
    write(root, 'effects/{0}/src/{0}.glsl'.format(name), 'out vec4 fragColor;\nvoid main() { fragColor = vec4(1.0); }\n')
    return build(root, 'effects', name, '{} tox v1'.format(name).encode())


def edit(rel, old, new):
    def apply(root):
        path = os.path.join(root, rel)
        text = open(path).read()
        assert old in text, (rel, old)
        write(root, rel, text.replace(old, new))
    return apply


def remove(rel):
    return lambda root: os.remove(os.path.join(root, rel))


def bump_and_rebuild(root):
    """A new version built and the bundle rebuilt around it, but nobody reviewed it."""
    edit('effects/demo/build_demo.py', '0.1.0', '0.2.0')(root)
    demo = build(root, 'effects', 'demo', b'demo tox v2')
    build(root, 'bundles', 'reel', b'reel tox v2', embeds={'demo': demo['tox_sha256']})


def rebuild_effect_only(root):
    write(root, 'effects/demo/src/demo.glsl', '// v2\n')
    build(root, 'effects', 'demo', b'demo tox v2')


BREAKS = [
    ('a shader changed', edit('effects/demo/src/demo.glsl', 'vec4(1.0)', 'vec4(0.5)'), 'older than its sources'),
    ('a source file added', lambda r: write(r, 'effects/demo/src/extra.py', 'x = 1\n'), 'older than its sources'),
    ('the shared library changed', lambda r: write(r, 'lib/tox_build.py', open(os.path.join(r, 'lib/tox_build.py')).read()
                                                   + '\n# changed\n'), 'older than its sources'),
    ('another lib module changed', lambda r: write(r, 'lib/font5x7.py', open(os.path.join(r, 'lib/font5x7.py')).read()
                                                   + '\n# changed\n'), 'older than its sources'),
    ('the builder changed', edit('effects/demo/build_demo.py', "VERSION", "# tweak\nVERSION"), 'older than its sources'),
    ('the .tox swapped', lambda r: write(r, 'effects/demo/demo.tox', b'other tox'), 'is not the file'),
    ('VERSION bumped, not rebuilt', edit('effects/demo/build_demo.py', '0.1.0', '0.2.0'), 'built as 0.1.0'),
    ('never built', remove('effects/demo/demo.json'), 'never built'),
    ('no builder', lambda r: write(r, 'effects/orphan/src/a.glsl', '\n'), 'no builder'),
    ('no docs page', remove('docs/effects/demo.md'), 'no docs page'),
    ('a bundle without a docs page', remove('docs/effects/reel.md'), 'bundles/reel: no docs page'),
    ('a new effect the bundle leaves out', lambda r: add_effect(r, 'demo2'), 'does not embed demo2'),
    ('no download link', edit('docs/effects/demo.md', 'releases/latest/download', 'releases/download/v1'),
     'does not link'),
    ('no preview shown', edit('docs/effects/demo.md', '![demo](demo.gif)', ''), 'shows no preview'),
    ('preview missing', remove('docs/effects/demo.gif'), 'which does not exist'),
    ('bundle embeds an older effect', rebuild_effect_only, 'embeds an older demo.tox'),
    ('no idiom review', remove('effects/demo/review.md'), 'no review.md'),
    ('a review box left open', edit('effects/demo/review.md', '- [x] C5', '- [ ] C5'), 'leaves unchecked: C5'),
    ('a new version, not reviewed', bump_and_rebuild, 'reviews version 0.1.0, the builder is at 0.2.0'),
    ('an idiom added since the review', lambda r: write(r, 'docs/TD_IDIOMS.md', open(os.path.join(
        r, 'docs/TD_IDIOMS.md')).read() + '- **Z9** (review) A new idiom.\n'), 'leaves unchecked: Z9'),
    ('docs page without the build', edit('docs/effects/demo.md', ' · saved in TouchDesigner 2025.33230', ''),
     'does not state the build'),
    ('two components share a name', lambda r: write(r, 'bundles/demo/build_demo.py', "VERSION = '0.1.0'\n"),
     'share a name'),
]


def main():
    base = tempfile.mkdtemp(prefix='tdlib-guards-')
    try:
        intact = os.path.join(base, 'intact')
        fixture(intact)
        items = check_tox.review_items(intact)
        assert len(items) >= 10, ('docs/TD_IDIOMS.md must yield its review items', items)
        errors, n = check_tox.check(intact)
        assert errors == [] and n == 2, ('the intact fixture must pass', errors, n)
        print('ok    intact fixture passes ({} components)'.format(n))
        failed = 0
        for i, (what, breaker, expect) in enumerate(BREAKS):
            root = os.path.join(base, 'b{}'.format(i))
            shutil.copytree(intact, root)
            breaker(root)
            errors, _ = check_tox.check(root)
            if any(expect in e for e in errors):
                print('ok    {}: {}'.format(what, next(e for e in errors if expect in e)))
            else:
                failed += 1
                print('MISS  {}: expected {!r}, got {}'.format(what, expect, errors))
        print('ALL OK' if not failed else '{} guard(s) did not fire'.format(failed))
        return 1 if failed else 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
