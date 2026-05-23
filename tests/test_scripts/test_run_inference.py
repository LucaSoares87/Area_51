from pathlib import Path

import pytest

from scripts import run_inference


def test_run_inference_exits_cleanly_for_missing_image(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_image = tmp_path / "missing.png"

    monkeypatch.setattr(
        "sys.argv",
        ["run_inference.py", "--image", str(missing_image)],
    )

    with pytest.raises(SystemExit) as exc_info:
        run_inference.main()

    captured = capsys.readouterr()

    assert exc_info.value.code == 1
    assert "Image not found" in captured.out
