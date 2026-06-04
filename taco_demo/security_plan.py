"""Enterprise security and data-governance plan for TACO diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


SECURITY_SOURCES: list[dict[str, str]] = [
    {
        "source_id": "nist_csf_2_0",
        "title": "NIST Cybersecurity Framework 2.0",
        "url": "https://www.nist.gov/cyberframework",
        "fact_used": "NIST CSF 2.0 organizes cybersecurity risk management around Govern, Identify, Protect, Detect, Respond, and Recover functions.",
    },
    {
        "source_id": "nist_ai_rmf_1_0",
        "title": "NIST Artificial Intelligence Risk Management Framework 1.0",
        "url": "https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10",
        "fact_used": "NIST AI RMF provides voluntary guidance for managing AI risks across governance, mapping, measurement, and management activities.",
    },
    {
        "source_id": "aicpa_trust_services_criteria",
        "title": "AICPA Trust Services Criteria",
        "url": "https://us.aicpa.org/content/dam/aicpa/interestareas/frc/assuranceadvisoryservices/downloadabledocuments/trust-services-criteria-redlined.pdf",
        "fact_used": "AICPA Trust Services Criteria support SOC 2 reporting across Security, Availability, Processing Integrity, Confidentiality, and Privacy.",
    },
]


def build_enterprise_security_plan(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    data_room_manifest: dict[str, Any],
    dreamaudit_summary: dict[str, Any],
    capacity_roadmap: dict[str, Any],
) -> dict[str, Any]:
    """Return a security and data-governance plan for enterprise diligence."""

    packet_files = int(len(data_room_manifest.get("primary_certificates", [])) + len(data_room_manifest.get("internal_metrics", [])))
    dreamaudit_attached = bool(dreamaudit_summary.get("attached"))
    return {
        "plan_id": f"SEC-{application.application_id}",
        "status": "security_plan_defined_not_audited",
        "boundary": "This is a security and data-governance diligence plan, not SOC 2 certification, penetration-test evidence, legal advice, customer security approval, or production control attestation.",
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "data_room_manifest_id": data_room_manifest.get("manifest_id"),
            "dreamaudit_attached": dreamaudit_attached,
        },
        "trust_posture": {
            "nist_csf_functions": ["govern", "identify", "protect", "detect", "respond", "recover"],
            "soc2_categories": ["security", "availability", "processing_integrity", "confidentiality", "privacy"],
            "ai_rmf_functions": ["govern", "map", "measure", "manage"],
            "current_evidence_files": packet_files,
            "packet_index_required": True,
        },
        "sensitive_data_classes": [
            _data_class(
                "robot_policy_artifacts",
                "DreamAudit certificates, simulator source paths, replay commands, and robot task metadata.",
                "May expose model behavior, customer operations, and failure modes.",
                "customer_restricted",
                ["access_control", "source_path_redaction", "retention_policy", "customer_approval_for_sharing"],
            ),
            _data_class(
                "model_activation_traces",
                "Torch activation NPZ files and layer-to-signal maps used for internal-risk scoring.",
                "May reveal proprietary model internals or partner policy behavior.",
                "customer_confidential",
                ["encryption_at_rest", "role_based_access", "hash_indexing", "least_privilege_exports"],
            ),
            _data_class(
                "insurance_submission_data",
                "Applications, quote worksheets, required controls, exclusions, renewal events, and incident records.",
                "May contain insured operations, risk posture, and claims-sensitive information.",
                "regulated_business_confidential",
                ["segregated_workspaces", "retention_policy", "audit_log", "claims_boundary_review"],
            ),
            _data_class(
                "reviewer_feedback",
                "Pilot walkthrough notes, accepted/rejected claims, missing evidence lists, and commercial follow-up commitments.",
                "May contain non-public buyer, broker, carrier, or OEM feedback.",
                "commercial_confidential",
                ["permission_to_quote_tracking", "redaction_workflow", "access_expiration", "customer_export_review"],
            ),
        ],
        "control_backlog": [
            _control(
                "packet_chain_of_custody",
                "security",
                "protect",
                "Every diligence ZIP includes packet/index.json with SHA-256 hashes and verifier output.",
                "implemented_in_local_packet_verifier",
                "Add signed export metadata, verifier screenshots, and immutable audit-log events for customer transfers.",
            ),
            _control(
                "role_based_data_room_access",
                "security",
                "protect",
                "Limit investor, broker, carrier, OEM, and internal operator access by artifact class and customer permission.",
                "planned",
                "Implement workspace-level RBAC and time-boxed reviewer access before external production pilots.",
            ),
            _control(
                "source_artifact_redaction",
                "confidentiality",
                "govern",
                "Separate source paths and replay commands that are safe to share from customer-private simulator or model paths.",
                "planned",
                "Add redaction profiles and customer export approval workflow.",
            ),
            _control(
                "activation_trace_retention",
                "privacy",
                "identify",
                "Define retention periods and deletion approvals for model activations and trace bundles.",
                "planned",
                "Attach retention policy and deletion receipt workflow to DreamAudit/activation intake.",
            ),
            _control(
                "evidence_processing_integrity",
                "processing_integrity",
                "detect",
                "Verify trace, certificate, and quote artifacts are internally consistent before packet export.",
                "partially_implemented",
                "Promote current tests and packet verifier into customer-visible CI evidence.",
            ),
            _control(
                "incident_response_for_evidence_leak",
                "security",
                "respond",
                "Define response steps if confidential robot-policy evidence or activation traces are exposed.",
                "planned",
                "Create incident severity matrix, customer notification template, and evidence revocation workflow.",
            ),
            _control(
                "service_availability_for_diligence_room",
                "availability",
                "recover",
                "Define recovery objectives for packet export, verifier, and customer evidence portals.",
                "planned",
                "Document backup, restore, and continuity procedures before paid enterprise pilots.",
            ),
        ],
        "data_room_operating_model": [
            {
                "workflow": "customer_packet_preparation",
                "owner": "TACO evidence operator",
                "required_controls": [
                    "source_artifact_redaction",
                    "packet_chain_of_custody",
                    "customer_export_review",
                ],
                "evidence_output": "approved packet manifest, verifier result, and customer export approval.",
            },
            {
                "workflow": "external_reviewer_access",
                "owner": "TACO customer success or compliance operator",
                "required_controls": [
                    "role_based_data_room_access",
                    "access_expiration",
                    "permission_to_quote_tracking",
                ],
                "evidence_output": "reviewer access log, accepted/missing claim form, and feedback quote permission.",
            },
            {
                "workflow": "activation_trace_intake",
                "owner": "TACO engineering operator",
                "required_controls": [
                    "activation_trace_retention",
                    "least_privilege_exports",
                    "evidence_processing_integrity",
                ],
                "evidence_output": "hash-indexed NPZ trace bundle, layer-to-signal map, and deletion/retention metadata.",
            },
        ],
        "enterprise_security_questionnaire": [
            {
                "question": "Can TACO prove which evidence file a reviewer inspected?",
                "current_answer": "The packet verifier and manifest provide local SHA-256 chain-of-custody evidence.",
                "next_proof": "Customer-facing audit log and signed packet export metadata.",
            },
            {
                "question": "Can customer model artifacts and activation traces be segregated?",
                "current_answer": "Artifact classes and required controls are defined; production workspace isolation is planned.",
                "next_proof": "Workspace RBAC implementation and customer-specific access-review record.",
            },
            {
                "question": "Is TACO SOC 2 ready?",
                "current_answer": "The plan maps to Trust Services categories, but no SOC 2 audit or attestation is claimed.",
                "next_proof": "Control owner matrix, policies, evidence inventory, and external readiness assessment.",
            },
            {
                "question": "What happens if evidence leaks or a reviewer loses access rights?",
                "current_answer": "Incident and revocation workflows are identified but not production-run.",
                "next_proof": "Incident response tabletop, access revocation test, and customer notification template.",
            },
        ],
        "seed_round_security_gates": [
            {
                "gate": "security_counsel_and_customer_disclaimer_review",
                "proof_required": "Counsel and design partners approve data-room disclaimers, export permissions, and confidentiality wording.",
            },
            {
                "gate": "workspace_rbac_and_audit_log",
                "proof_required": "External reviewer access is role-scoped, time-boxed, logged, and revocable.",
            },
            {
                "gate": "activation_trace_retention_policy",
                "proof_required": "Customer-specific retention, deletion, and export policy covers activation traces and DreamAudit artifacts.",
            },
            {
                "gate": "soc2_readiness_assessment",
                "proof_required": "Independent readiness assessment maps implemented controls to Trust Services categories.",
            },
        ],
        "links_to_existing_artifacts": {
            "data_room_manifest": data_room_manifest.get("manifest_id", "manifest.json"),
            "capacity_roadmap": capacity_roadmap.get("roadmap_id", "commercial/capacity_roadmap.json"),
            "dreamaudit_summary": dreamaudit_summary.get("status", "dreamaudit/summary.json"),
        },
        "source_material": SECURITY_SOURCES,
        "open_security_risks": [
            "Current repository proves local packet verification, not production customer isolation.",
            "No SOC 2 audit, penetration test, security questionnaire approval, or customer security review is represented.",
            "Activation traces and source paths may expose partner IP unless redaction and retention controls are enforced.",
            "External reviewers need role-scoped, expiring access before real customer evidence is shared.",
            "Incident response and evidence revocation workflows need tabletop tests before paid enterprise pilots.",
        ],
    }


def security_data_class_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly sensitive data class rows."""

    return [
        {
            "Data Class": item["data_class"],
            "Description": item["description"],
            "Primary Risk": item["primary_risk"],
            "Classification": item["classification"],
            "Required Controls": "; ".join(item["required_controls"]),
        }
        for item in plan["sensitive_data_classes"]
    ]


def security_control_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly security control backlog rows."""

    return [
        {
            "Control": item["control_id"],
            "SOC2 Category": item["soc2_category"],
            "NIST CSF Function": item["nist_csf_function"],
            "Current Evidence": item["current_evidence"],
            "Status": item["status"],
            "Next Proof": item["next_proof"],
        }
        for item in plan["control_backlog"]
    ]


def security_workflow_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly data-room workflow rows."""

    return [
        {
            "Workflow": item["workflow"],
            "Owner": item["owner"],
            "Required Controls": "; ".join(item["required_controls"]),
            "Evidence Output": item["evidence_output"],
        }
        for item in plan["data_room_operating_model"]
    ]


def security_question_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly enterprise questionnaire rows."""

    return [
        {
            "Question": item["question"],
            "Current Answer": item["current_answer"],
            "Next Proof": item["next_proof"],
        }
        for item in plan["enterprise_security_questionnaire"]
    ]


def security_gate_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly seed security gates."""

    return [
        {
            "Gate": item["gate"],
            "Proof Required": item["proof_required"],
        }
        for item in plan["seed_round_security_gates"]
    ]


def _data_class(
    data_class: str,
    description: str,
    primary_risk: str,
    classification: str,
    required_controls: list[str],
) -> dict[str, Any]:
    return {
        "data_class": data_class,
        "description": description,
        "primary_risk": primary_risk,
        "classification": classification,
        "required_controls": required_controls,
    }


def _control(
    control_id: str,
    soc2_category: str,
    nist_csf_function: str,
    current_evidence: str,
    status: str,
    next_proof: str,
) -> dict[str, str]:
    return {
        "control_id": control_id,
        "soc2_category": soc2_category,
        "nist_csf_function": nist_csf_function,
        "current_evidence": current_evidence,
        "status": status,
        "next_proof": next_proof,
    }
