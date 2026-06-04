from __future__ import annotations

import json
import subprocess
import sys
import zipfile


def test_export_data_room_packet_cli_builds_verified_zip(tmp_path):
    output_path = tmp_path / "TACO-DATAROOM.zip"
    manifest_path = tmp_path / "manifest.json"
    memo_path = tmp_path / "diligence_memo.md"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "taco_demo.scripts.export_data_room_packet",
            "--data-root",
            str(tmp_path / "data"),
            "--force-bootstrap",
            "--output",
            str(output_path),
            "--manifest-output",
            str(manifest_path),
            "--memo-output",
            str(memo_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(result.stdout)

    assert summary["valid"] is True
    assert summary["issues"] == []
    assert summary["packet_format"] == "taco_data_room_zip_v27"
    assert summary["certificate_count"] == 3
    assert summary["metric_count"] == 3
    assert summary["suite_size"] == 40
    assert output_path.exists()
    assert manifest_path.exists()
    assert memo_path.exists()
    with zipfile.ZipFile(output_path, mode="r") as archive:
        names = set(archive.namelist())
        index = json.loads(archive.read("packet/index.json"))
        provenance = json.loads(archive.read("evidence/provenance_audit.json"))

    assert "diligence_memo.md" in names
    assert "technical/technical_diligence_runbook.json" in names
    assert index["packet_format"] == summary["packet_format"]
    assert provenance["audit_id"] == "PROV-APP-APEX-001"
    assert provenance["current_counts"]["generated_suite_videos"] == 40
