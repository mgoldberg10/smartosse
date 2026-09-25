"""Render the paper figures from the manifest -- ROADMAP.md section 5's driver.

    python -m smartosse.figures --list           # the manifest as a table
    python -m smartosse.figures --all            # render everything renderable
    python -m smartosse.figures --only fig5 fig6
    python -m smartosse.figures --tier 0         # default: cache-only figures
    python -m smartosse.figures --check          # resolve + report, render nothing

The point of this module is that it **reports what it skipped and why** instead
of failing halfway. A figure is skipped, never attempted, when its caches are
missing or its tier needs data this machine does not have; the summary then says
which cache was absent. That is the difference between "Tier 0 works" as a claim
and as something a stranger can check in one command.

Each figure is rendered by running its module's own ``__main__`` in a
subprocess. That is deliberate: the modules already have working ``__main__``
blocks with their own argparse flags and matplotlib setup (``use_latex_times``,
``use_embedded_pdf_fonts``, the indexed-PDF bitdepth patch), and per-figure
rcParam state does not survive being run in-process one after another. The
driver orchestrates; it does not reimplement.
"""
import argparse
import os
import re
import subprocess
import sys
import time

from ..paths import cache_dir

try:
    import yaml
except ImportError:
    sys.exit('PyYAML is required to read MANIFEST.yml (pip install pyyaml)')

MANIFEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MANIFEST.yml')


def load_manifest(path=MANIFEST):
    with open(path) as f:
        return yaml.safe_load(f)


FIG_PKG_DIR = os.path.dirname(os.path.abspath(__file__))


def missing_caches(entry, cdir):
    """Cache filenames this entry needs that are not present in `cdir`."""
    return [c for c in (entry.get('caches') or [])
            if not os.path.exists(os.path.join(cdir, c))]


def missing_required_files(entry, pkg_dir=FIG_PKG_DIR):
    """Non-cache input files this entry needs that are absent.

    Paths are relative to the figures package directory. This exists so a
    cacheless figure (fig1 renders from shipped CSVs, not a .nc) is still
    verifiable -- otherwise the driver would have nothing to check and would
    attempt it blindly, which is the half-failing behaviour it exists to avoid.
    """
    return [f for f in (entry.get('required_files') or [])
            if not os.path.exists(os.path.join(pkg_dir, f))]


def skip_reason(entry, cdir, want_tier):
    """Why this entry cannot or should not be rendered now, or None to proceed."""
    if entry.get('library_only') or not entry.get('entrypoint', True):
        return 'library-only (no __main__)'
    tier = entry.get('tier')
    if want_tier is not None and tier > want_tier:
        blocker = ' '.join((entry.get('tier_blocker') or '').split())
        if not blocker:
            blocker = 'needs higher-tier inputs'
        elif len(blocker) > 140:
            # Truncate on a word boundary. (Don't cut at the first '.' -- blockers
            # legitimately start with things like "HALF FIXED 2026-09-24.")
            blocker = blocker[:137].rsplit(' ', 1)[0] + '...'
        return f'tier {tier} > requested tier {want_tier}: {blocker}'
    absent = missing_caches(entry, cdir)
    if absent:
        return f"missing cache(s) in {cdir}: {', '.join(absent)}"
    absent_files = missing_required_files(entry)
    if absent_files:
        return f"missing input file(s): {', '.join(absent_files)}"
    return None


# Rendering needs the `plotting` extra (matplotlib, cartopy, cmocean, pyresample,
# ecco_v4_py). An extraction-only env has the DATA but not these, and that is a very
# different problem from a missing cache -- so say so rather than reporting a generic
# failure that reads like the figure is broken.
_PLOTTING_MODULES = {'matplotlib', 'cartopy', 'cmocean', 'pyresample', 'ecco_v4_py',
                     'mpl_toolkits', 'xgcm'}


def _missing_module(output):
    """Module name from a ModuleNotFoundError in `output`, or None."""
    m = re.search(r"No module named '([^']+)'", output or '')
    return m.group(1) if m else None


def render(entry, extra_args=(), dry_run=False):
    """Run one figure module's __main__.

    Returns (status, seconds, tail) where status is 'ok', 'failed', or
    'missing-dep'.
    """
    cmd = [sys.executable, '-m', entry['module'], *extra_args]
    if dry_run:
        print(f"    would run: {' '.join(cmd)}")
        return 'ok', 0.0, ''
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.time() - t0
    if p.returncode == 0:
        return 'ok', dt, ''
    out = (p.stderr or '') + (p.stdout or '')
    mod = _missing_module(out)
    if mod and mod.split('.')[0] in _PLOTTING_MODULES:
        return 'missing-dep', dt, mod
    tail = out.strip().splitlines()
    return 'failed', dt, '\n'.join(tail[-8:])


def cmd_list(man):
    cdir = cache_dir()
    print(f'cache_dir: {cdir}'
          f"{'' if os.path.isdir(cdir) else '   <-- DOES NOT EXIST'}\n")
    print(f"{'id':10} {'tier':5} {'caches present':16} module")
    print('-' * 78)
    for e in man['figures']:
        absent = missing_caches(e, cdir)
        total = len(e.get('caches') or [])
        req_total = len(e.get('required_files') or [])
        if total == 0 and req_total:
            req_absent = len(missing_required_files(e))
            state = f'{req_total - req_absent}/{req_total} files'
        elif total == 0:
            state = 'n/a (no cache)'
        else:
            state = f'{total - len(absent)}/{total}'
        flag = '' if e.get('entrypoint', True) else '  (library-only)'
        print(f"{e['id']:10} {e.get('tier', '?'):<5} {state:16} {e['module']}{flag}")
    print()
    for b in man.get('builders', []):
        print(f"builder  {b['module']}  [paths: {b.get('paths', '?')}]")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='python -m smartosse.figures',
        description='Render paper figures from the manifest (ROADMAP.md section 5).')
    ap.add_argument('--list', action='store_true', help='print the manifest and exit')
    ap.add_argument('--all', action='store_true',
                    help='attempt every entrypoint figure regardless of tier')
    ap.add_argument('--tier', type=int, default=None,
                    help='render figures of this tier or lower (default: 0)')
    ap.add_argument('--only', nargs='+', metavar='ID',
                    help='render just these manifest ids')
    ap.add_argument('--check', action='store_true',
                    help='resolve caches and report, render nothing')
    ap.add_argument('--manifest', default=MANIFEST)
    args = ap.parse_args(argv)

    man = load_manifest(args.manifest)

    if args.list:
        cmd_list(man)
        return 0

    want_tier = None if args.all else (0 if args.tier is None else args.tier)
    cdir = cache_dir()

    entries = man['figures']
    if args.only:
        ids = set(args.only)
        entries = [e for e in entries if e['id'] in ids]
        unknown = ids - {e['id'] for e in entries}
        if unknown:
            ap.error(f"unknown manifest id(s): {', '.join(sorted(unknown))}")

    print(f'cache_dir : {cdir}'
          f"{'' if os.path.isdir(cdir) else '   <-- DOES NOT EXIST'}")
    print(f"selection : {'all tiers' if want_tier is None else f'tier <= {want_tier}'}"
          f"{' (check only)' if args.check else ''}")
    print(f'figures   : {len(entries)} considered\n')

    rendered, skipped, failed = [], [], []
    for e in entries:
        reason = skip_reason(e, cdir, want_tier)
        if reason:
            print(f"  SKIP    {e['id']:10} {reason}")
            skipped.append((e['id'], reason))
            continue
        print(f"  RENDER  {e['id']:10} {e['module']}", flush=True)
        status, dt, tail = render(e, dry_run=args.check)
        if status == 'ok':
            print(f"          {'checked' if args.check else f'ok ({dt:.1f}s)'}")
            rendered.append(e['id'])
        elif status == 'missing-dep':
            reason = (f"needs the `plotting` extra (no '{tail}') -- "
                      f"its input data IS present")
            print(f'          SKIP: {reason}')
            skipped.append((e['id'], reason))
        else:
            print(f'          FAILED ({dt:.1f}s)')
            for line in tail.splitlines():
                print(f'            | {line}')
            failed.append((e['id'], tail))

    print('\n' + '=' * 60)
    print(f'rendered {len(rendered)}   skipped {len(skipped)}   failed {len(failed)}')
    if rendered:
        print(f"  rendered: {', '.join(rendered)}")
    if skipped:
        print('  skipped:')
        for fid, reason in skipped:
            # Full reason was already printed inline above; keep the summary scannable.
            brief = reason if len(reason) <= 88 else reason[:85].rstrip() + '...'
            print(f'    {fid:10} {brief}')
    if failed:
        print(f"  failed:   {', '.join(f for f, _ in failed)}")
    print('=' * 60)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
