"""
Tests for Layer 1: Rule-Based Deterministic Engine

Verifies that ALL mandatory clauses are detected, risk keywords are scanned,
and structural validation works correctly.
"""

import pytest
from src.analyzers.rule_based import RuleBasedAnalyzer, Severity, MANDATORY_CLAUSE_PATTERNS

SAMPLE_CONTRACT = """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into as of January 15, 2025 ("Effective Date")
by and between ABC Corporation ("Company") and XYZ Consulting LLC ("Provider").

1. DEFINITIONS
"Confidential Information" means any non-public information disclosed by either party.
"Deliverables" means the work product to be provided by Provider.

2. SCOPE OF WORK
Provider shall perform consulting services as described in Statement of Work (SOW).
Working hours shall be 9:00 AM to 5:00 PM, Monday through Friday.
Deliverables include monthly progress reports and final analysis document.

3. PAYMENT TERMS
Company shall pay Provider a fee of $10,000 USD per month.
Invoices are due within net 30 days of receipt.
Late payments accrue interest at 1.5% per month.

4. TERMINATION
Either party may terminate this Agreement upon 30 days' written notice.
Company may terminate immediately for material breach not cured within 15 days.
Upon termination, Provider shall deliver all completed work.

5. CONFIDENTIALITY
Each party shall maintain strict confidentiality of the other party's proprietary information.
This non-disclosure obligation survives termination for 3 years.

6. INTELLECTUAL PROPERTY
All IP created during the engagement shall be owned by Company.
Provider assigns all copyright and patent rights to Company.
Provider retains a license to pre-existing intellectual property.

7. LIABILITY AND INDEMNIFICATION
Total liability shall not exceed fees paid in the preceding 12 months.
Neither party shall be liable for indirect or consequential damages.
Provider shall indemnify Company against third-party claims.

8. FORCE MAJEURE
Neither party shall be liable for delays caused by events beyond reasonable control,
including acts of God, natural disasters, pandemic, or government actions.

9. DISPUTE RESOLUTION
Disputes shall be resolved through binding arbitration in New York, NY,
under the rules of the American Arbitration Association.

9A. GOVERNING LAW
This Agreement shall be governed by and construed in accordance with the
laws of the State of New York, without regard to its conflict of laws provisions.
The parties submit to the exclusive jurisdiction of the courts of New York.

10. DATA PROTECTION
Both parties shall comply with applicable data protection laws including GDPR.
Provider shall implement appropriate security measures for personal data processing.
Data breach notification must occur within 72 hours.

11. NON-COMPETE
Provider agrees not to compete with Company's core business for 12 months
after termination in the continental United States.

12. TAX OBLIGATIONS
Provider is responsible for all applicable taxes on compensation received.
Company shall withhold taxes as required by law.

13. INSURANCE
Provider shall maintain professional liability insurance with minimum $1,000,000 coverage.

14. AMENDMENTS
This Agreement may only be amended by written consent of both parties.

15. NOTICE
All notices shall be delivered in writing to the addresses specified herein.
Written notice shall be deemed received upon delivery or 3 business days after mailing.

16. SEVERABILITY
If any provision is held invalid, the remaining provisions shall remain in full force and effect.

17. ENTIRE AGREEMENT
This Agreement constitutes the entire agreement and supersedes all prior agreements.

18. ASSIGNMENT
Neither party may assign or delegate this Agreement without prior written consent.

19. WARRANTIES
Provider represents and warrants that services will be performed in a professional manner.
Provider warrants deliverables will conform to specifications.

20. AUTO-RENEWAL
This Agreement shall automatically renew for successive one-year terms
unless either party provides 60 days' written notice of non-renewal.

IN WITNESS WHEREOF, the parties have executed this Agreement.

ABC Corporation
Signature: _________________
Name: John Smith, CEO

XYZ Consulting LLC
Signature: _________________
Name: Jane Doe, Managing Partner
"""


@pytest.fixture
def analyzer():
    return RuleBasedAnalyzer()


class TestMandatoryClauseDetection:
    """Test that ALL mandatory clauses are detected in a complete contract."""

    def test_all_mandatory_clauses_detected(self, analyzer):
        """Every single mandatory clause should be detected."""
        result = analyzer.analyze(SAMPLE_CONTRACT)
        missing = result["missing_clauses"]
        assert missing == [], f"Should detect all clauses, but missing: {missing}"

    def test_governing_law_detected(self, analyzer):
        text = "This agreement shall be governed by the laws of the State of New York."
        findings = analyzer._check_mandatory_clauses(text, "en")
        gov_law = [f for f in findings if f.clause_type == "governing_law"]
        assert len(gov_law) == 1
        assert gov_law[0].detected is True

    def test_termination_detected(self, analyzer):
        text = "Either party may terminate this agreement upon 30 days written notice."
        findings = analyzer._check_mandatory_clauses(text, "en")
        term = [f for f in findings if f.clause_type == "termination"]
        assert len(term) == 1
        assert term[0].detected is True

    def test_payment_terms_detected(self, analyzer):
        text = "The client shall pay a fee of $5,000 per month. Payment terms are net 30."
        findings = analyzer._check_mandatory_clauses(text, "en")
        pay = [f for f in findings if f.clause_type == "payment_terms"]
        assert len(pay) == 1
        assert pay[0].detected is True

    def test_confidentiality_detected(self, analyzer):
        text = "Both parties shall maintain the confidentiality of all proprietary information."
        findings = analyzer._check_mandatory_clauses(text, "en")
        conf = [f for f in findings if f.clause_type == "confidentiality"]
        assert len(conf) == 1
        assert conf[0].detected is True

    def test_ip_ownership_detected(self, analyzer):
        text = "All intellectual property created during the engagement shall be owned by the Company."
        findings = analyzer._check_mandatory_clauses(text, "en")
        ip = [f for f in findings if f.clause_type == "ip_ownership"]
        assert len(ip) == 1
        assert ip[0].detected is True

    def test_liability_detected(self, analyzer):
        text = "Limitation of liability: total liability shall not exceed fees paid."
        findings = analyzer._check_mandatory_clauses(text, "en")
        liab = [f for f in findings if f.clause_type == "liability"]
        assert len(liab) == 1
        assert liab[0].detected is True

    def test_force_majeure_detected(self, analyzer):
        text = "Neither party shall be liable for force majeure events beyond reasonable control."
        findings = analyzer._check_mandatory_clauses(text, "en")
        fm = [f for f in findings if f.clause_type == "force_majeure"]
        assert len(fm) == 1
        assert fm[0].detected is True

    def test_dispute_resolution_detected(self, analyzer):
        text = "All disputes shall be resolved through binding arbitration."
        findings = analyzer._check_mandatory_clauses(text, "en")
        disp = [f for f in findings if f.clause_type == "dispute_resolution"]
        assert len(disp) == 1
        assert disp[0].detected is True

    def test_data_protection_detected(self, analyzer):
        text = "Both parties shall comply with applicable data protection and privacy laws."
        findings = analyzer._check_mandatory_clauses(text, "en")
        dp = [f for f in findings if f.clause_type == "data_protection"]
        assert len(dp) == 1
        assert dp[0].detected is True

    def test_non_compete_detected(self, analyzer):
        text = "Provider agrees to a non-compete restriction for 12 months."
        findings = analyzer._check_mandatory_clauses(text, "en")
        nc = [f for f in findings if f.clause_type == "non_compete"]
        assert len(nc) == 1
        assert nc[0].detected is True

    def test_working_hours_detected(self, analyzer):
        text = "The scope of work includes deliverables and working hours of 9-5."
        findings = analyzer._check_mandatory_clauses(text, "en")
        wh = [f for f in findings if f.clause_type == "working_hours"]
        assert len(wh) == 1
        assert wh[0].detected is True

    def test_tax_obligations_detected(self, analyzer):
        text = "Provider is responsible for all tax obligations and withholding."
        findings = analyzer._check_mandatory_clauses(text, "en")
        tax = [f for f in findings if f.clause_type == "tax_obligations"]
        assert len(tax) == 1
        assert tax[0].detected is True

    def test_insurance_detected(self, analyzer):
        text = "Provider shall maintain professional liability insurance."
        findings = analyzer._check_mandatory_clauses(text, "en")
        ins = [f for f in findings if f.clause_type == "insurance"]
        assert len(ins) == 1
        assert ins[0].detected is True

    def test_amendments_detected(self, analyzer):
        text = "This agreement may only be amended by written consent of both parties."
        findings = analyzer._check_mandatory_clauses(text, "en")
        amend = [f for f in findings if f.clause_type == "amendments"]
        assert len(amend) == 1
        assert amend[0].detected is True

    def test_notice_detected(self, analyzer):
        text = "All notices must be given in writing and shall be delivered to the parties."
        findings = analyzer._check_mandatory_clauses(text, "en")
        notice = [f for f in findings if f.clause_type == "notice"]
        assert len(notice) == 1
        assert notice[0].detected is True

    def test_severability_detected(self, analyzer):
        text = "If any provision is found invalid, the severability clause ensures remaining provisions stay in effect."
        findings = analyzer._check_mandatory_clauses(text, "en")
        sev = [f for f in findings if f.clause_type == "severability"]
        assert len(sev) == 1
        assert sev[0].detected is True

    def test_entire_agreement_detected(self, analyzer):
        text = "This constitutes the entire agreement and supersedes all prior agreements."
        findings = analyzer._check_mandatory_clauses(text, "en")
        ea = [f for f in findings if f.clause_type == "entire_agreement"]
        assert len(ea) == 1
        assert ea[0].detected is True

    def test_assignment_detected(self, analyzer):
        text = "Neither party may assign or delegate this agreement without prior written consent. The assignment of any rights is prohibited."
        findings = analyzer._check_mandatory_clauses(text, "en")
        assign = [f for f in findings if f.clause_type == "assignment"]
        assert len(assign) == 1
        assert assign[0].detected is True

    def test_warranties_detected(self, analyzer):
        text = "Provider represents and warrants that services will be performed professionally."
        findings = analyzer._check_mandatory_clauses(text, "en")
        warr = [f for f in findings if f.clause_type == "warranties"]
        assert len(warr) == 1
        assert warr[0].detected is True

    def test_auto_renewal_detected(self, analyzer):
        text = "This agreement shall auto-renew for successive one-year renewal terms."
        findings = analyzer._check_mandatory_clauses(text, "en")
        ar = [f for f in findings if f.clause_type == "auto_renewal"]
        assert len(ar) == 1
        assert ar[0].detected is True


class TestMissingClauseDetection:
    """Test that missing clauses are correctly flagged."""

    def test_empty_contract_flags_all_missing(self, analyzer):
        result = analyzer.analyze("This is a very short text with nothing useful.")
        missing = result["missing_clauses"]
        assert len(missing) == len(MANDATORY_CLAUSE_PATTERNS)

    def test_missing_clause_severity(self, analyzer):
        result = analyzer.analyze("This is a contract with nothing.")
        findings = result["mandatory_clauses"]
        for f in findings:
            if not f.detected:
                assert f.severity != Severity.INFO
                assert f.confidence == 100.0
                assert "MISSING" in f.explanation

    def test_partial_contract_flags_correct_missing(self, analyzer):
        text = "This agreement shall be governed by the laws of California. Payment terms: fee of $5000 is payable monthly."
        result = analyzer.analyze(text)
        missing = result["missing_clauses"]
        assert "governing_law" not in missing
        assert "payment_terms" not in missing
        assert "termination" in missing
        assert "confidentiality" in missing


class TestRiskKeywordScanning:
    """Test detection of risky keywords and phrases."""

    def test_penalty_detected(self, analyzer):
        text = "A penalty of $10,000 shall apply for late delivery."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_penalty" for f in findings)

    def test_unlimited_liability_detected(self, analyzer):
        text = "The provider shall bear unlimited liability for damages."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_unlimited_liability" for f in findings)
        ul = [f for f in findings if f.clause_type == "risk_keyword_unlimited_liability"]
        assert ul[0].severity == Severity.CRITICAL

    def test_unilateral_detected(self, analyzer):
        text = "Company may unilaterally modify the terms of this agreement."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_unilateral" for f in findings)

    def test_sole_discretion_detected(self, analyzer):
        text = "At its sole discretion, Company may reject any deliverable."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_sole_discretion" for f in findings)

    def test_irrevocable_detected(self, analyzer):
        text = "Provider irrevocably grants all rights to the Company."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_irrevocable" for f in findings)

    def test_perpetual_detected(self, analyzer):
        text = "The license granted is perpetual and worldwide."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_perpetual" for f in findings)

    def test_waiver_detected(self, analyzer):
        text = "Provider hereby waives all claims against the Company."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_waive" for f in findings)

    def test_forfeit_detected(self, analyzer):
        text = "Failure to deliver shall result in forfeiture of all fees."
        findings = analyzer._scan_risk_keywords(text)
        assert any(f.clause_type == "risk_keyword_forfeit" for f in findings)

    def test_clean_contract_no_risk_keywords(self, analyzer):
        text = "This is a standard service agreement with balanced terms."
        findings = analyzer._scan_risk_keywords(text)
        assert len(findings) == 0


class TestStructuralValidation:
    """Test structural element validation."""

    def test_parties_detected(self, analyzer):
        text = "This agreement is between ABC Corp and XYZ LLC."
        findings = analyzer._validate_structure(text, "en")
        parties = [f for f in findings if f.clause_type == "structure_parties"]
        assert len(parties) == 1
        assert parties[0].detected is True

    def test_dates_detected(self, analyzer):
        text = "This agreement has an effective date of January 15, 2025."
        findings = analyzer._validate_structure(text, "en")
        dates = [f for f in findings if f.clause_type == "structure_dates"]
        assert len(dates) == 1
        assert dates[0].detected is True

    def test_signatures_detected(self, analyzer):
        text = "IN WITNESS WHEREOF the parties have executed this agreement."
        findings = analyzer._validate_structure(text, "en")
        sigs = [f for f in findings if f.clause_type == "structure_signatures"]
        assert len(sigs) == 1
        assert sigs[0].detected is True

    def test_definitions_detected(self, analyzer):
        text = '1. DEFINITIONS\n"Confidential Information" means any non-public information disclosed.'
        findings = analyzer._validate_structure(text, "en")
        defs = [f for f in findings if f.clause_type == "structure_definitions"]
        assert len(defs) == 1
        assert defs[0].detected is True

    def test_missing_structure_flagged(self, analyzer):
        text = "This is just plain text without any contract structure."
        findings = analyzer._validate_structure(text, "en")
        missing = [f for f in findings if not f.detected]
        assert len(missing) > 0
        for f in missing:
            assert f.severity == Severity.CRITICAL


class TestJapaneseSupport:
    """Test Japanese contract analysis."""

    def test_japanese_governing_law(self, analyzer):
        text = "本契約は日本法を準拠法とし、東京地方裁判所を専属的合意管轄裁判所とする。"
        findings = analyzer._check_mandatory_clauses(text, "ja")
        gl = [f for f in findings if f.clause_type == "governing_law"]
        assert gl[0].detected is True

    def test_japanese_termination(self, analyzer):
        text = "甲又は乙は、30日前の書面による通知により本契約を解除することができる。"
        findings = analyzer._check_mandatory_clauses(text, "ja")
        term = [f for f in findings if f.clause_type == "termination"]
        assert term[0].detected is True

    def test_japanese_payment(self, analyzer):
        text = "乙は甲に対し、月額100万円の報酬を支払うものとする。"
        findings = analyzer._check_mandatory_clauses(text, "ja")
        pay = [f for f in findings if f.clause_type == "payment_terms"]
        assert pay[0].detected is True

    def test_japanese_confidentiality(self, analyzer):
        text = "甲及び乙は、相手方の秘密情報を厳格に秘密保持するものとする。"
        findings = analyzer._check_mandatory_clauses(text, "ja")
        conf = [f for f in findings if f.clause_type == "confidentiality"]
        assert conf[0].detected is True

    def test_japanese_force_majeure(self, analyzer):
        text = "天災、戦争その他の不可抗力により本契約の履行が困難となった場合。"
        findings = analyzer._check_mandatory_clauses(text, "ja")
        fm = [f for f in findings if f.clause_type == "force_majeure"]
        assert fm[0].detected is True


class TestGetAllFindings:
    """Test the combined findings output."""

    def test_complete_contract_returns_findings(self, analyzer):
        findings = analyzer.get_all_findings(SAMPLE_CONTRACT)
        assert len(findings) > 0

    def test_findings_have_required_fields(self, analyzer):
        findings = analyzer.get_all_findings(SAMPLE_CONTRACT)
        for f in findings:
            assert f.clause_type
            assert isinstance(f.detected, bool)
            assert isinstance(f.severity, Severity)
            assert isinstance(f.confidence, float)
            assert f.explanation
            assert f.detecting_layer == "rule_based"

    def test_all_20_mandatory_clauses_checked(self, analyzer):
        findings = analyzer.get_all_findings("Short text.")
        mandatory_findings = [f for f in findings if not f.clause_type.startswith("structure_") and not f.clause_type.startswith("risk_keyword_")]
        assert len(mandatory_findings) == len(MANDATORY_CLAUSE_PATTERNS)
