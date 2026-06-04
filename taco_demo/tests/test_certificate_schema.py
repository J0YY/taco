from taco_demo.policy_issuer import build_internal_underwriting_certificate
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import (
    InternalRiskMetrics,
    ReplayArtifacts,
    dataclass_to_dict,
    default_application,
    read_json,
    write_json,
)


def test_dataclass_json_roundtrip(tmp_path):
    app = default_application()
    path = tmp_path / "app.json"
    write_json(app, path)
    assert read_json(path)["application_id"] == app.application_id


def test_internal_underwriting_certificate_contains_application_quote_metrics():
    app = default_application()
    cert = DEMO_CERTIFICATES[0]
    metrics = InternalRiskMetrics(cert.certificate_id, 1, 0.5, 0.8, 1.0, 0.7, 0.45, "sig", True, "test", {})
    quote = generate_quote(app, [cert], {cert.certificate_id: metrics}, True)
    artifacts = ReplayArtifacts(cert.certificate_id, None, None, None, None, None, None, "test", {})
    issued = build_internal_underwriting_certificate(app, cert, metrics, quote, artifacts)
    data = dataclass_to_dict(issued)
    assert data["application"]["application_id"] == "APP-APEX-001"
    assert data["insurance_decision"]["quote_id"] == quote.quote_id
    assert data["internal_evidence"]["certificate_id"] == cert.certificate_id

