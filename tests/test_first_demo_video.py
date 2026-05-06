"""First demo video builder tests."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from app.production_assembly.first_demo_video import build_first_demo_video


class _FakeImageResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return b"fake-image-bytes"


def _fake_run_factory(output_path: Path):
    def _fake_run(cmd, check, capture_output, text):
        if cmd[0] == "ffprobe":
            return subprocess.CompletedProcess(cmd, 0, stdout="2.500\n", stderr="")
        if cmd[0] == "ffmpeg":
            output_path.write_bytes(b"fake-mp4-bytes")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {cmd}")

    return _fake_run


def test_build_first_demo_video_from_local_image_and_mp3(tmp_path):
    image = tmp_path / "image.png"
    audio = tmp_path / "voice.mp3"
    output = tmp_path / "first_demo_video.mp4"
    image.write_bytes(b"png")
    audio.write_bytes(b"ID3audio")

    with patch("app.production_assembly.first_demo_video.shutil.which") as which:
        which.side_effect = lambda name: name
        with patch("app.production_assembly.first_demo_video.subprocess.run", side_effect=_fake_run_factory(output)) as run:
            result = build_first_demo_video(str(image), audio_path=audio, output_path=output)

    assert result.video_created is True
    assert result.output_path == str(output)
    assert result.duration_seconds == 2.5
    assert result.image_source == str(image)
    assert result.audio_source == str(audio)
    assert result.warnings == []
    assert result.blocking_reasons == []
    assert output.read_bytes() == b"fake-mp4-bytes"
    ffmpeg_cmd = run.call_args_list[-1].args[0]
    assert any("scale=1280:720:force_original_aspect_ratio=decrease" in arg for arg in ffmpeg_cmd)
    assert "-shortest" in ffmpeg_cmd


def test_build_first_demo_video_downloads_image_url_first(tmp_path):
    audio = tmp_path / "voice.mp3"
    output = tmp_path / "first_demo_video.mp4"
    download_base = tmp_path / "downloaded_image"
    audio.write_bytes(b"ID3audio")

    with patch("app.production_assembly.first_demo_video.shutil.which") as which:
        which.side_effect = lambda name: name
        with patch("app.production_assembly.first_demo_video.urlopen", return_value=_FakeImageResponse()) as uo:
            with patch("app.production_assembly.first_demo_video.subprocess.run", side_effect=_fake_run_factory(output)):
                result = build_first_demo_video(
                    "https://cdn.example.test/leonardo/image.png?token=secretish",
                    audio_path=audio,
                    output_path=output,
                    downloaded_image_path=download_base,
                )

    req = uo.call_args.args[0]
    assert req.full_url == "https://cdn.example.test/leonardo/image.png?token=secretish"
    assert result.video_created is True
    assert result.image_source == str(download_base.with_suffix(".png"))
    assert "secretish" not in result.model_dump_json()
    assert download_base.with_suffix(".png").read_bytes() == b"fake-image-bytes"


def test_build_first_demo_video_blocks_without_audio_or_ffmpeg(tmp_path):
    image = tmp_path / "image.png"
    image.write_bytes(b"png")

    with patch("app.production_assembly.first_demo_video.shutil.which", return_value=None):
        result = build_first_demo_video(str(image), audio_path=tmp_path / "missing.mp3", output_path=tmp_path / "out.mp4")

    assert result.video_created is False
    assert "audio_source_missing" in result.blocking_reasons
    assert "ffmpeg_missing" in result.blocking_reasons
    assert result.output_path == str(tmp_path / "out.mp4")


def test_build_first_demo_video_blocks_without_image_source(tmp_path):
    audio = tmp_path / "voice.mp3"
    audio.write_bytes(b"ID3audio")

    with patch("app.production_assembly.first_demo_video.shutil.which") as which:
        which.side_effect = lambda name: name
        result = build_first_demo_video("", audio_path=audio, output_path=tmp_path / "out.mp4")

    assert result.video_created is False
    assert result.blocking_reasons == ["image_source_missing"]


def test_cli_outputs_safe_json_without_image_source(tmp_path):
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        ["python", str(root / "scripts" / "build_first_demo_video.py")],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)

    assert payload["video_created"] is False
    assert payload["output_path"] == str(Path("output") / "first_demo_video.mp4")
    assert "image_source_missing" in payload["blocking_reasons"]
