"""Guard smartosse/figures/MANIFEST.yml against drifting from the code.

A manifest's failure mode is silent staleness: someone adds a figure module, or
renames a cache, and the manifest still claims the old shape. These tests are
deliberately cheap -- they read source paths and parse YAML, and never import a
figure module or touch model data -- so they can run in CI with no inputs.
"""
import os

import pytest

yaml = pytest.importorskip('yaml')

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       'smartosse', 'figures')
MANIFEST_PATH = os.path.join(FIG_DIR, 'MANIFEST.yml')

# Modules in figures/ that are deliberately not figures or builders.
NOT_A_FIGURE = {'__init__.py', '__main__.py', 'figs_utils.py'}


@pytest.fixture(scope='module')
def man():
    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def test_manifest_parses(man):
    assert 'figures' in man and 'builders' in man
    assert man['figures'], 'manifest lists no figures'


def test_ids_unique(man):
    ids = [e['id'] for e in man['figures']]
    assert len(ids) == len(set(ids)), f'duplicate manifest ids: {ids}'


def test_required_keys(man):
    for e in man['figures']:
        for key in ('id', 'module', 'tier'):
            assert key in e, f"figure {e.get('id', '?')} is missing '{key}'"
        assert e['tier'] in (0, 1, 2), f"{e['id']}: tier {e['tier']} not in 0/1/2"


def test_modules_exist_on_disk(man):
    """Every module named in the manifest is a real file (not imported -- just present)."""
    for e in man['figures'] + man['builders']:
        rel = e['module'].split('.')[-1] + '.py'
        path = os.path.join(FIG_DIR, rel)
        assert os.path.exists(path), f"{e['module']} -> missing file {path}"


def test_every_figure_module_is_in_the_manifest():
    """A new fig*.py must be added to the manifest, or this fails."""
    on_disk = {f for f in os.listdir(FIG_DIR)
               if f.startswith('fig') and f.endswith('.py') and f not in NOT_A_FIGURE}
    with open(MANIFEST_PATH) as f:
        man = yaml.safe_load(f)
    listed = {e['module'].split('.')[-1] + '.py' for e in man['figures']}
    assert on_disk == listed, (
        f'manifest out of sync with figures/\n'
        f'  on disk but not in manifest: {sorted(on_disk - listed)}\n'
        f'  in manifest but not on disk: {sorted(listed - on_disk)}')


def test_every_builder_module_is_in_the_manifest():
    on_disk = {f for f in os.listdir(FIG_DIR)
               if f.startswith('gen_') and f.endswith('.py')}
    with open(MANIFEST_PATH) as f:
        man = yaml.safe_load(f)
    listed = {b['module'].split('.')[-1] + '.py' for b in man['builders']}
    assert on_disk == listed, (
        f'manifest builders out of sync with figures/\n'
        f'  on disk but not listed: {sorted(on_disk - listed)}\n'
        f'  listed but not on disk: {sorted(listed - on_disk)}')


def test_tier0_figures_declare_something_checkable(man):
    """Tier 0 means 'renders from data that ships' -- so it must name that data.

    Usually that is a `.nc` cache, but it can instead be `required_files` (fig1
    renders from shipped CSVs, no cache). What is not allowed is a tier-0 entry
    naming neither: that is the manifest claiming a figure needs no model data
    while giving the driver nothing to verify, which is exactly the overclaim
    ROADMAP section 0 exists to prevent.
    """
    for e in man['figures']:
        if e['tier'] == 0:
            assert e.get('caches') or e.get('required_files'), (
                f"{e['id']}: tier 0 but declares neither caches nor required_files")


def test_required_files_exist(man):
    """Anything listed in `required_files` must actually be in the package."""
    for e in man['figures']:
        for rel in (e.get('required_files') or []):
            path = os.path.join(FIG_DIR, rel)
            assert os.path.exists(path), (
                f"{e['id']}: required_files names a missing file: {rel}")


def test_required_files_are_not_gitignored(man):
    """required_files must ship -- so none of them may sit under an ignored path."""
    import subprocess
    repo = os.path.dirname(os.path.dirname(FIG_DIR))
    for e in man['figures']:
        for rel in (e.get('required_files') or []):
            tracked_path = os.path.join('smartosse', 'figures', rel)
            p = subprocess.run(['git', 'check-ignore', tracked_path],
                               cwd=repo, capture_output=True, text=True)
            assert p.returncode == 1, (
                f"{e['id']}: required file {tracked_path} is gitignored "
                f"(matched: {p.stdout.strip()}) -- it would not ship")


def test_higher_tier_figures_explain_why(man):
    """A figure a stranger cannot render must say what blocks it."""
    for e in man['figures']:
        if e['tier'] > 0:
            assert e.get('tier_blocker'), (
                f"{e['id']}: tier {e['tier']} but no tier_blocker explaining why")


def test_driver_can_read_the_manifest():
    """The driver's own loader agrees with these tests (no data, no rendering)."""
    from smartosse.figures.__main__ import load_manifest, missing_caches
    m = load_manifest()
    assert len(m['figures']) == len(man_ids(m))
    # missing_caches must be total when the cache dir does not exist at all
    e = next(f for f in m['figures'] if f.get('caches'))
    assert missing_caches(e, '/nonexistent-cache-dir') == e['caches']


def man_ids(m):
    return {e['id'] for e in m['figures']}


def test_shipped_cable_data_is_present_and_parses():
    """Fig. 1's global cable CSVs must ship and keep their expected schema.

    These are static figure inputs, not regenerable model output, so losing them
    silently un-ships a figure. Guarded here because they sit outside the
    gitignored figures/data/ precisely so that they DO ship -- a well-meaning
    move back into data/ would break Tier 0 with no other test noticing.
    """
    pd = pytest.importorskip('pandas')
    cable_dir = os.path.join(FIG_DIR, 'cable_data')
    assert os.path.isdir(cable_dir), f'missing {cable_dir}'
    for name, min_rows in [('smart_cables_may2024.csv', 200),
                           ('global_total_coord.csv', 3000)]:
        path = os.path.join(cable_dir, name)
        assert os.path.exists(path), f'missing shipped cable CSV: {path}'
        df = pd.read_csv(path)
        assert list(df.columns) == ['Longitude', 'Latitude'], (
            f'{name}: unexpected columns {list(df.columns)}')
        assert len(df) >= min_rows, f'{name}: only {len(df)} rows'


def test_cable_data_is_not_gitignored():
    """The CSVs must be tracked, not sitting under an ignored path."""
    import subprocess
    # FIG_DIR is <repo>/smartosse/figures, so two dirnames up is the repo root.
    repo = os.path.dirname(os.path.dirname(FIG_DIR))
    rel = 'smartosse/figures/cable_data/global_total_coord.csv'
    p = subprocess.run(['git', 'check-ignore', rel], cwd=repo,
                       capture_output=True, text=True)
    # exit 1 == "not ignored", which is what we require
    assert p.returncode == 1, (
        f'{rel} is gitignored (matched: {p.stdout.strip()}) -- it would not ship')
