from taco_demo.dreamaudit_adapter import DreamAuditAdapter
from taco_demo.scripts.bootstrap_demo_data import bootstrap


def test_normalize_minimal_raw_certificate():
    raw = {"certificate_id": "C-1", "patch_recipe": {"type": "runtime_monitor"}}
    cert = DreamAuditAdapter(repo_root=None).normalize_certificate(raw)
    assert cert.certificate_id == "C-1"
    assert cert.patch_recipe["type"] == "runtime_monitor"


def test_load_bootstrapped_certificates(tmp_path):
    bootstrap(tmp_path, force=True)
    certs = DreamAuditAdapter(repo_root=tmp_path, data_root=tmp_path).load_certificates(tmp_path / "dreamaudit_certs")
    assert {cert.certificate_id for cert in certs} == {"FR-001", "FR-002", "FR-003"}


def test_missing_fields_do_not_crash():
    cert = DreamAuditAdapter(repo_root=None).normalize_certificate({})
    assert cert.certificate_id == "CERT-UNKNOWN"
    assert cert.metadata["source"] == "normalized_missing_fields"

