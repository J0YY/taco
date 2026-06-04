from taco_demo.maniskill_suite import SUITE_SIZE, build_maniskill_suite_cases, write_maniskill_suite
from taco_demo.schemas import read_json


def test_maniskill_suite_has_40_varied_cases():
    cases = build_maniskill_suite_cases()
    assert len(cases) == SUITE_SIZE
    assert len({case["failure_family"] for case in cases}) >= 8
    assert len({case["env_id"] for case in cases}) >= 5
    for case in cases:
        assert case["identified_signal"]
        assert case["underwriting_readout"]
        assert case["required_control"]
        assert case["video_path"].endswith(".gif")


def test_write_maniskill_suite_manifest_and_videos(tmp_path):
    manifest_path = write_maniskill_suite(tmp_path, force=True, count=4)
    manifest = read_json(manifest_path)
    assert manifest["suite_size"] == 4
    assert len(manifest["cases"]) == 4
    for case in manifest["cases"]:
        assert (tmp_path / "maniskill_suite" / "videos" / case["video_path"]).exists()
