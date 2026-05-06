"""BA 20.13 — Local Preview Cleanup / Retention Guard."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = _ROOT / "scripts" / "cleanup_local_previews.py"


@pytest.fixture
def cleanup_mod():
    spec = importlib.util.spec_from_file_location("cleanup_local_previews", _SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_out_root_missing_found_zero_no_crash(cleanup_mod, tmp_path):
    missing = tmp_path / "nope" / "out"
    plan = cleanup_mod.plan_local_preview_cleanup(missing, keep_latest=5, max_delete=20)
    assert plan["found_count"] == 0
    assert plan["delete_candidates"] == []
    assert cleanup_mod.discover_local_preview_runs(missing) == []


def test_only_local_preview_directories_counted(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    (root / "local_preview_a").mkdir()
    (root / "local_preview_b").mkdir()
    (root / "other_folder").mkdir()
    (root / "local_preview_file.txt").write_text("x", encoding="utf-8")
    d = cleanup_mod.discover_local_preview_runs(root)
    assert len(d) == 2
    names = sorted(p.name for p in d)
    assert names == ["local_preview_a", "local_preview_b"]


def test_keep_latest_newest_by_mtime(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    old = root / "local_preview_old"
    new = root / "local_preview_new"
    old.mkdir()
    new.mkdir()
    os.utime(old, (100, 100))
    os.utime(new, (200, 200))
    plan = cleanup_mod.plan_local_preview_cleanup(root, keep_latest=1, max_delete=20)
    assert plan["found_count"] == 2
    assert plan["kept_count"] == 1
    assert "local_preview_new" in plan["kept_paths"][0]
    assert any("local_preview_old" in c for c in plan["delete_candidates"])


def test_stable_sort_same_mtime(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    b = root / "local_preview_b"
    a = root / "local_preview_a"
    b.mkdir()
    a.mkdir()
    t = 500.0
    os.utime(a, (t, t))
    os.utime(b, (t, t))
    plan = cleanup_mod.plan_local_preview_cleanup(root, keep_latest=1, max_delete=20)
    kept_name = Path(plan["kept_paths"][0]).name
    assert kept_name == "local_preview_a"


def test_dry_run_plan_does_not_delete(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    d = root / "local_preview_x"
    d.mkdir()
    plan = cleanup_mod.plan_local_preview_cleanup(root, keep_latest=0, max_delete=10)
    assert plan["would_delete_count"] >= 1
    assert d.is_dir()


def test_apply_deletes_direct_candidates(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    a = root / "local_preview_delme"
    a.mkdir()
    plan = cleanup_mod.plan_local_preview_cleanup(root, keep_latest=0, max_delete=10)
    plan["dry_run"] = False
    assert a.is_dir()
    ex = cleanup_mod.apply_local_preview_cleanup(plan)
    assert ex["deleted_count"] == 1
    assert not a.exists()


def test_max_delete_caps_candidates(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    for i in range(8):
        (root / f"local_preview_{i}").mkdir()
        os.utime(root / f"local_preview_{i}", (1000 + i, 1000 + i))
    plan = cleanup_mod.plan_local_preview_cleanup(root, keep_latest=0, max_delete=3)
    assert plan["would_delete_count"] == 3
    assert any("truncated" in w for w in plan["warnings"])


def test_symlink_skipped_in_discover(cleanup_mod, tmp_path):
    real = tmp_path / "real_lp"
    real.mkdir()
    root = tmp_path / "out"
    root.mkdir()
    target = root / "local_preview_real"
    target.mkdir()
    try:
        link = root / "local_preview_link"
        link.symlink_to(target.resolve(), target_is_directory=True)
    except OSError:
        pytest.skip("symlink not supported in this environment")
    d = cleanup_mod.discover_local_preview_runs(root)
    names = {p.name for p in d}
    assert "local_preview_link" not in names
    assert "local_preview_real" in names


def test_apply_skips_symlink_candidate(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    tdir = root / "local_preview_target"
    tdir.mkdir()
    try:
        lnk = root / "local_preview_sym"
        lnk.symlink_to(tdir.resolve(), target_is_directory=True)
    except OSError:
        pytest.skip("symlink not supported")
    plan = {
        "out_root": str(root.resolve()),
        "delete_candidates": [str(lnk)],
    }
    ex = cleanup_mod.apply_local_preview_cleanup(plan)
    assert ex["deleted_count"] == 0
    assert lnk.exists()
    assert any("symlink" in w.lower() or "skip_symlink" in w for w in ex["apply_warnings"])


def test_summary_dry_run_has_next_step(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    (root / "local_preview_1").mkdir()
    plan = cleanup_mod.plan_local_preview_cleanup(root, keep_latest=0, max_delete=5)
    plan["dry_run"] = True
    plan["deleted_count"] = 0
    plan["deleted_paths"] = []
    s = cleanup_mod.build_local_preview_cleanup_summary(plan)
    assert "Found:" in s
    assert "Would delete:" in s
    assert "Kept:" in s
    assert "--apply" in s or "apply" in s.lower()


def test_summary_apply_shows_deleted(cleanup_mod, tmp_path):
    root = tmp_path / "out"
    root.mkdir()
    plan = {
        "out_root": str(root),
        "keep_latest": 5,
        "max_delete": 20,
        "found_count": 1,
        "kept_count": 0,
        "would_delete_count": 1,
        "delete_candidates": ["/x"],
        "dry_run": False,
        "deleted_count": 2,
        "deleted_paths": ["/a", "/b"],
    }
    s = cleanup_mod.build_local_preview_cleanup_summary(plan)
    assert "Deleted: 2" in s
    assert "APPLY" in s


def test_cli_dry_run_smoke(cleanup_mod, tmp_path, capsys):
    root = tmp_path / "out"
    root.mkdir()
    (root / "local_preview_z").mkdir()
    rc = cleanup_mod.main(["--out-root", str(root), "--keep-latest", "1", "--max-delete", "5"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY RUN" in out
    assert (root / "local_preview_z").is_dir()


def test_cli_apply_removes(cleanup_mod, tmp_path, capsys):
    root = tmp_path / "out"
    root.mkdir()
    d = root / "local_preview_rm"
    d.mkdir()
    rc = cleanup_mod.main(["--out-root", str(root), "--keep-latest", "0", "--max-delete", "10", "--apply"])
    assert rc == 0
    assert not d.exists()
    assert "Deleted: 1" in capsys.readouterr().out


def test_print_json_includes_delete_candidates(cleanup_mod, tmp_path, capsys):
    root = tmp_path / "out"
    root.mkdir()
    (root / "local_preview_j").mkdir()
    cleanup_mod.main(["--out-root", str(root), "--keep-latest", "0", "--max-delete", "5", "--print-json"])
    out = capsys.readouterr().out
    assert "---" in out
    j = json.loads(out.split("---", 1)[1].strip())
    assert "delete_candidates" in j
    assert isinstance(j["delete_candidates"], list)


def test_main_module_import():
    spec = importlib.util.spec_from_file_location("cln2", _SCRIPT)
    assert spec and spec.loader
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert callable(m.main)
