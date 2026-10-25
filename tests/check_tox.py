"""The checked-in .tox files are exactly what their sources build. Runs before every commit
(.githooks/pre-commit) and in CI, with plain Python: no TouchDesigner needed.

    uv run tests/check_tox.py

A component is a folder effects/<name>/ or bundles/<name>/ holding build_<name>.py. For each,
it fails when:
  - the component was never built (no <name>.tox or <name>.json beside the builder),
  - a source changed since the last build (lib/tox_build.py, the builder, anything in src/),
  - the .tox is not the file its manifest describes,
  - the builder's VERSION is not the version the .tox was built as,
  - a component has no docs page (docs/effects/<name>.md, bundles too), the page doesn't link the
    latest-release download, state the build the .tox was saved in or carry its Credits and license
    (what it uses or follows, docs/BUILDING.md), or the preview it shows is missing,
  - a component's idiom review (<kind>/<name>/review.md, docs/TD_IDIOMS.md) is missing, leaves a
    box open, reviews an older version, or lacks an item the checklist has gained since,
  - a bundle embeds an older build of a component than the one checked in, or, built to embed
    every effect (embeds_all in its manifest, like the showreel), leaves one out.
tests/test_guards.py breaks each of these on purpose and checks that it fails.

    uv run tests/check_tox.py --review-template <name>    # print a blank review.md to start from
"""

import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = ('effects', 'bundles')
PREVIEW = re.compile(r"\]\(([^)\s]+\.(?:webp|gif|mp4|webm|png|jpg))\)")
CREDITS = re.compile(r'^## Credits and license\n+\S', re.M)
REVIEW_ITEM = re.compile(r'^- \*\*([A-Z]\d+)\*\* \(review\) (.*(?:\n  .*)*)', re.M)
CHECKED = re.compile(r'^- \[[xX]\] ([A-Z]\d+)\b', re.M)
REVIEWED = re.compile(r'^Reviewed version: (\S+)', re.M)


def load_lib(root):
    path = os.path.join(root, 'lib', 'tox_build.py')
    lib = {}
    exec(compile(open(path).read(), path, 'exec'), lib)
    return lib


def components(root):
    for kind in KINDS:
        for d in sorted(glob.glob(os.path.join(root, kind, '*', ''))):
            name = os.path.basename(os.path.dirname(d))
            if not name.startswith(('.', '_')):
                yield kind, name, os.path.dirname(d)


def review_items(root):
    """The (review) items of docs/TD_IDIOMS.md, as (id, text on one line)."""
    text = open(os.path.join(root, 'docs', 'TD_IDIOMS.md')).read()
    return [(i, ' '.join(body.split())) for i, body in REVIEW_ITEM.findall(text)]


def review_template(root, name, version):
    lines = ['# {}: idiom review'.format(name), '', 'Reviewed version: {}'.format(version), '',
             'The review items of docs/TD_IDIOMS.md, checked by hand for this version: tick each box',
             '(`- [x]`) and say in a few words how it holds.', '']
    lines += ['- [ ] {} {}'.format(i, text) for i, text in review_items(root)]
    return '\n'.join(lines) + '\n'


def _review(root, rel, d, version, errors):
    path = os.path.join(d, 'review.md')
    if not os.path.isfile(path):
        errors.append('{}: no review.md; every version gets the idiom review (docs/TD_IDIOMS.md, '
                      'check_tox.py --review-template)'.format(rel))
        return
    text = open(path).read()
    reviewed = REVIEWED.search(text)
    if reviewed is None or reviewed.group(1) != version:
        errors.append('{}/review.md reviews version {}, the builder is at {}: review it again'.format(
            rel, reviewed.group(1) if reviewed else 'none', version))
    checked = set(CHECKED.findall(text))
    open_items = [i for i, _ in review_items(root) if i not in checked]
    if open_items:
        errors.append('{}/review.md leaves unchecked: {}'.format(rel, ' '.join(open_items)))


def _docs(root, lib, rel, name, errors):
    page = os.path.join(root, 'docs', 'effects', name + '.md')
    if not os.path.isfile(page):
        errors.append('{}: no docs page docs/effects/{}.md'.format(rel, name))
        return
    text = open(page).read()
    if lib['DOWNLOAD_URL'].format(name) not in text:
        errors.append('docs/effects/{}.md does not link {}'.format(name, lib['DOWNLOAD_URL'].format(name)))
    if not CREDITS.search(text):
        errors.append('docs/effects/{}.md has no "## Credits and license" section saying what it uses or follows '
                      '(docs/BUILDING.md, Credits)'.format(name))
    previews = PREVIEW.findall(text)
    if not previews:
        errors.append('docs/effects/{}.md shows no preview (an animated .webp or .gif, or a clip)'.format(name))
    for target in previews:
        if '://' not in target and not os.path.isfile(os.path.join(root, 'docs', 'effects', target)):
            errors.append('docs/effects/{}.md shows {}, which does not exist'.format(name, target))


def check(root=ROOT):
    """Every problem found, as one line each, and how many components were checked."""
    lib = load_lib(root)
    errors, built, found = [], {}, list(components(root))
    seen = {}
    for kind, name, d in found:
        rel = '{}/{}'.format(kind, name)
        if name in seen:
            errors.append('{} and {} share a name; release assets need unique names'.format(seen[name], rel))
        seen[name] = rel
        builder = os.path.join(d, 'build_{}.py'.format(name))
        if not os.path.isfile(builder):
            errors.append('{}: no builder build_{}.py'.format(rel, name))
            continue
        _docs(root, lib, rel, name, errors)
        tox_path, manifest_path = (os.path.join(d, name + ext) for ext in ('.tox', '.json'))
        if not (os.path.isfile(tox_path) and os.path.isfile(manifest_path)):
            errors.append('{}: never built; run build_{}.py in TouchDesigner (docs/BUILDING.md)'.format(rel, name))
            continue
        manifest = json.load(open(manifest_path))
        tox = open(tox_path, 'rb').read()
        if hashlib.sha256(tox).hexdigest() != manifest.get('tox_sha256'):
            errors.append('{0}/{1}.tox is not the file {1}.json describes'.format(rel, name))
        if lib['digest'](root, lib['component_sources'](root, d)) != manifest.get('sources_sha256'):
            errors.append('{}/{}.tox is older than its sources: rebuild it in TouchDesigner (docs/BUILDING.md)'.format(
                rel, name))
        version = re.search(r"^VERSION = '([^']+)'", open(builder).read(), re.M)
        if version is None:
            errors.append('{}/build_{}.py has no VERSION line'.format(rel, name))
        elif version.group(1) != manifest.get('version'):
            errors.append('{}: the builder says VERSION {} but the .tox was built as {}; rebuild it'.format(
                rel, version.group(1), manifest.get('version')))
        if version is not None:
            _review(root, rel, d, version.group(1), errors)
        page = os.path.join(root, 'docs', 'effects', name + '.md')
        build = manifest.get('touchdesigner_build', '')
        if os.path.isfile(page) and (not build or build not in open(page).read()):
            errors.append('docs/effects/{}.md does not state the build the .tox was saved in ({})'.format(
                name, build))
        built[name] = (kind, manifest)
    for kind, name, d in found:
        manifest = built.get(name, (kind, {}))[1]
        embeds = manifest.get('embeds', {})
        for inner, sha in sorted(embeds.items()):
            if inner not in built:
                errors.append('{}/{} embeds {}, which is not a built component'.format(kind, name, inner))
            elif built[inner][1]['tox_sha256'] != sha:
                errors.append('{}/{}.tox embeds an older {}.tox: rebuild the bundle after the component'.format(
                    kind, name, inner))
        if manifest.get('embeds_all'):
            for inner in sorted(n for n, (k, _) in built.items() if k == 'effects' and n not in embeds):
                errors.append('{}/{} does not embed {}: rebuild the bundle, which takes every effect'.format(
                    kind, name, inner))
    return errors, len(found)


def main():
    if sys.argv[1:2] == ['--review-template']:
        name = sys.argv[2]
        kind = next(k for k in KINDS if os.path.isdir(os.path.join(ROOT, k, name)))
        builder = open(os.path.join(ROOT, kind, name, 'build_{}.py'.format(name))).read()
        sys.stdout.write(review_template(ROOT, name, re.search(r"^VERSION = '([^']+)'", builder, re.M).group(1)))
        return 0
    errors, n = check(ROOT)
    for e in errors:
        print('FAIL', e)
    print('{} component(s) checked, {} problem(s)'.format(n, len(errors)))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
