"""Live modules are frozen: once a module's open date has passed, deploy.py
leaves it (and the Activity Verification assignment) alone unless --force."""
import deploy


def _at(y, m, d, hh=12, mm=0):
    return deploy.datetime(y, m, d, hh, mm, tzinfo=deploy.TZ)


def test_is_live_once_module_opens():
    opens = deploy.date(2027, 1, 18)
    assert deploy.is_live(opens, _at(2027, 1, 18, 0, 0))        # midnight ET on open date
    assert deploy.is_live(opens, _at(2027, 1, 20))
    assert not deploy.is_live(opens, _at(2027, 1, 17, 23, 59))  # the night before


def test_dry_run_skips_live_weeks(course, monkeypatch, capsys):
    monkeypatch.setattr(deploy, "now_et", lambda: _at(2027, 1, 20))
    assert deploy.main(["--all", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "[frozen] exercises/introductions" in out
    assert "[frozen] exercises/one_selfie" in out
    assert "[dry-run] module 'Week Three: Comic'" in out
    assert not (course / "preview" / "one_selfie.html").exists()
    assert (course / "preview" / "two_comic.html").exists()


def test_week_flag_on_live_week_refuses_without_force(course, monkeypatch, capsys):
    monkeypatch.setattr(deploy, "now_et", lambda: _at(2027, 1, 20))
    assert deploy.main(["--week", "one_selfie", "--dry-run"]) != 0
    assert "--force" in capsys.readouterr().out
    assert not (course / "preview" / "one_selfie.html").exists()
    assert deploy.main(["--week", "one_selfie", "--dry-run", "--force"]) == 0
    assert (course / "preview" / "one_selfie.html").exists()


def test_break_module_freezes_too(course, monkeypatch, capsys):
    monkeypatch.setattr(deploy, "now_et", lambda: _at(2027, 3, 16))
    deploy.main(["--all", "--dry-run"])
    out = capsys.readouterr().out
    assert "[frozen] Week Ten: Spring Break" in out
    assert "[dry-run] break module" not in out
    assert "[dry-run] module 'Final Reflection'" in out


def test_activity_verification_frozen_once_open():
    av = {"open": deploy.date(2027, 1, 11)}
    assert deploy.av_is_live(av, _at(2027, 1, 12))
    assert not deploy.av_is_live(av, _at(2027, 1, 10))
    assert not deploy.av_is_live({}, _at(2027, 1, 12))  # no open date: never frozen
