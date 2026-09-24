import textwrap

import pytest

from smartosse import paths


@pytest.fixture
def sites_yml(tmp_path):
    """A small sites.yml, independent of the real config/sites.yml."""
    p = tmp_path / "sites.yml"
    p.write_text(textwrap.dedent("""
        sites:
          alpha:
            detect:
              hostname: ["alpha*"]
            grid_dir: /alpha/grid
          beta:
            detect:
              hostname: ["beta*"]
            grid_dir: /beta/grid
            run_root: /beta/runs
          bare:
            {}
    """))
    return p


def test_env_var_wins_over_everything(monkeypatch, sites_yml):
    monkeypatch.setenv('SMARTOSSE_GRID_DIR', '/env/grid')
    monkeypatch.setenv('SMARTOSSE_SITE', 'alpha')
    assert paths.resolve('grid_dir', sites_yml=sites_yml) == '/env/grid'


def test_smartosse_site_overrides_hostname_detection(monkeypatch, sites_yml):
    monkeypatch.setattr(paths.socket, 'gethostname', lambda: 'nothing-matches')
    monkeypatch.setenv('SMARTOSSE_SITE', 'beta')
    assert paths.detect_site(sites_yml=sites_yml) == 'beta'
    assert paths.resolve('run_root', sites_yml=sites_yml) == '/beta/runs'


def test_hostname_detection_without_smartosse_site(monkeypatch, sites_yml):
    monkeypatch.delenv('SMARTOSSE_SITE', raising=False)
    monkeypatch.setattr(paths.socket, 'gethostname', lambda: 'alpha07.example.edu')
    assert paths.detect_site(sites_yml=sites_yml) == 'alpha'
    assert paths.resolve('grid_dir', sites_yml=sites_yml) == '/alpha/grid'


def test_missing_key_raises_with_actionable_message(monkeypatch, sites_yml):
    monkeypatch.setenv('SMARTOSSE_SITE', 'alpha')
    with pytest.raises(paths.PathNotConfiguredError) as exc:
        paths.resolve('run_root', sites_yml=sites_yml)
    msg = str(exc.value)
    assert 'run_root' in msg
    assert 'SMARTOSSE_RUN_ROOT' in msg
    assert 'alpha' in msg


def test_run_root_absent_is_not_an_error_by_itself(monkeypatch, sites_yml):
    # A site with no run_root at all (e.g. docker/Tier 0) must not raise just
    # from being detected -- only resolve('run_root', ...) should raise.
    monkeypatch.setenv('SMARTOSSE_SITE', 'bare')
    assert paths.detect_site(sites_yml=sites_yml) == 'bare'
    with pytest.raises(paths.PathNotConfiguredError):
        paths.resolve('run_root', sites_yml=sites_yml)


def test_unknown_site_raises_cleanly(monkeypatch, sites_yml):
    monkeypatch.setattr(paths.socket, 'gethostname', lambda: 'totally-unrecognized')
    monkeypatch.delenv('SMARTOSSE_SITE', raising=False)
    assert paths.detect_site(sites_yml=sites_yml) is None
    with pytest.raises(paths.PathNotConfiguredError):
        paths.resolve('grid_dir', sites_yml=sites_yml)


def test_cache_dir_falls_back_instead_of_raising(monkeypatch, tmp_path):
    # cache_dir() itself always reads the real config/sites.yml (it takes no
    # sites_yml param), so isolate it from whatever real site this test
    # happens to run on and confirm it still returns something instead of
    # raising -- that's what makes Tier 0 work with zero configuration.
    monkeypatch.delenv('SMARTOSSE_CACHE_DIR', raising=False)
    monkeypatch.setenv('SMARTOSSE_SITE', 'nonexistent-site-for-this-test')
    assert paths.cache_dir() == str(paths._DEFAULT_CACHE_DIR)

    # resolve() itself, given a sites.yml that doesn't exist, raises -- it's
    # cache_dir()'s job specifically to catch that and fall back.
    missing = tmp_path / "does_not_exist.yml"
    with pytest.raises(paths.PathNotConfiguredError):
        paths.resolve('cache_dir', sites_yml=missing)
