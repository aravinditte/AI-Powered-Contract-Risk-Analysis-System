"""
Layer 1: Rule-Based Deterministic Engine

This layer uses regex pattern matching and keyword scanning to deterministically
detect mandatory clauses, risk keywords, and structural elements in contracts.
It NEVER misses a mandatory clause - it's the safety net of the hybrid system.

Supports both English and Japanese contracts.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class RuleFinding:
    clause_type: str
    detected: bool
    severity: Severity
    confidence: float
    clause_text: str
    explanation: str
    suggested_fix: str
    detecting_layer: str = "rule_based"


MANDATORY_CLAUSE_PATTERNS: dict[str, dict] = {
    "governing_law": {
        "patterns_en": [
            r"(?i)\bgoverning\s+law\b",
            r"(?i)\bgoverned\s+by\b",
            r"(?i)\bjurisdiction\b",
            r"(?i)\bapplicable\s+law\b",
            r"(?i)\blaws\s+of\s+(the\s+)?state\b",
            r"(?i)\bchoice\s+of\s+law\b",
        ],
        "patterns_ja": [
            r"準拠法",
            r"管轄",
            r"裁判管轄",
            r"適用法",
            r"法律に準拠",
        ],
        "severity": Severity.CRITICAL,
        "description": "Governing law / jurisdiction clause",
        "suggested_fix": "Add a governing law clause specifying the applicable jurisdiction, e.g., 'This Agreement shall be governed by the laws of [State/Country].'",
    },
    "termination": {
        "patterns_en": [
            r"(?i)\btermination\b",
            r"(?i)\bterminate\b",
            r"(?i)\bexit\s+clause\b",
            r"(?i)\bcancellation\b",
            r"(?i)\bright\s+to\s+terminate\b",
            r"(?i)\bupon\s+termination\b",
        ],
        "patterns_ja": [
            r"解除",
            r"解約",
            r"終了",
            r"契約解除",
            r"中途解約",
        ],
        "severity": Severity.CRITICAL,
        "description": "Termination / exit clause",
        "suggested_fix": "Add a termination clause specifying conditions under which either party may terminate the agreement, notice period, and consequences of termination.",
    },
    "payment_terms": {
        "patterns_en": [
            r"(?i)\bpayment\s+terms?\b",
            r"(?i)\bcompensation\b",
            r"(?i)\bfee[s]?\b",
            r"(?i)\binvoic(e|ing)\b",
            r"(?i)\bpayable\b",
            r"(?i)\bremuneration\b",
            r"(?i)\b(net\s+)?\d+\s+days?\b",
            r"(?i)\bpayment\s+schedule\b",
        ],
        "patterns_ja": [
            r"支払",
            r"報酬",
            r"対価",
            r"料金",
            r"請求",
            r"手数料",
        ],
        "severity": Severity.CRITICAL,
        "description": "Payment terms (amount, currency, schedule)",
        "suggested_fix": "Add payment terms specifying amount, currency, payment schedule, and late payment penalties.",
    },
    "confidentiality": {
        "patterns_en": [
            r"(?i)\bconfidential(ity)?\b",
            r"(?i)\bnon[\-\s]?disclosure\b",
            r"(?i)\bNDA\b",
            r"(?i)\bproprietary\s+information\b",
            r"(?i)\btrade\s+secret[s]?\b",
            r"(?i)\bconfidential\s+information\b",
        ],
        "patterns_ja": [
            r"秘密",
            r"機密",
            r"守秘義務",
            r"秘密保持",
            r"機密情報",
        ],
        "severity": Severity.HIGH,
        "description": "Confidentiality / NDA provisions",
        "suggested_fix": "Add a confidentiality clause defining what constitutes confidential information, obligations of the receiving party, and duration of confidentiality obligations.",
    },
    "ip_ownership": {
        "patterns_en": [
            r"(?i)\bintellectual\s+property\b",
            r"(?i)\bIP\s+(rights?|ownership)\b",
            r"(?i)\bcopyright\b",
            r"(?i)\bpatent\b",
            r"(?i)\btrademark\b",
            r"(?i)\bwork[\-\s]?(for[\-\s]?hire|product)\b",
            r"(?i)\bownership\s+of\s+(work|deliverables?|materials?)\b",
            r"(?i)\bassignment\s+of\s+(rights?|IP|intellectual)\b",
        ],
        "patterns_ja": [
            r"知的財産",
            r"著作権",
            r"特許",
            r"商標",
            r"知財",
            r"成果物の帰属",
        ],
        "severity": Severity.HIGH,
        "description": "IP ownership / assignment",
        "suggested_fix": "Add an IP ownership clause specifying who owns intellectual property created during the engagement and any licensing terms.",
    },
    "liability": {
        "patterns_en": [
            r"(?i)\bliabilit(y|ies)\b",
            r"(?i)\blimitation\s+of\s+liability\b",
            r"(?i)\bindemnif(y|ication)\b",
            r"(?i)\bhold\s+harmless\b",
            r"(?i)\bdamages?\b(?!.*\bproperty\s+damage)",
            r"(?i)\bliable\b",
        ],
        "patterns_ja": [
            r"責任",
            r"損害賠償",
            r"免責",
            r"賠償責任",
            r"責任制限",
        ],
        "severity": Severity.CRITICAL,
        "description": "Liability limitation / indemnification",
        "suggested_fix": "Add a liability limitation clause capping total liability and specifying indemnification terms for both parties.",
    },
    "force_majeure": {
        "patterns_en": [
            r"(?i)\bforce\s+majeure\b",
            r"(?i)\bact[s]?\s+of\s+god\b",
            r"(?i)\bunforeseen\s+(event|circumstance)s?\b",
            r"(?i)\bbeyond\s+(the\s+)?control\b",
            r"(?i)\bnatural\s+disaster\b",
            r"(?i)\bpandemic\b",
        ],
        "patterns_ja": [
            r"不可抗力",
            r"天災",
            r"自然災害",
        ],
        "severity": Severity.HIGH,
        "description": "Force majeure",
        "suggested_fix": "Add a force majeure clause specifying what events qualify, notification requirements, and consequences for non-performance.",
    },
    "dispute_resolution": {
        "patterns_en": [
            r"(?i)\bdispute\s+resolution\b",
            r"(?i)\barbitration\b",
            r"(?i)\bmediation\b",
            r"(?i)\blitigation\b",
            r"(?i)\bsettle\s+disputes?\b",
            r"(?i)\bdispute[s]?\s+(shall|will|must)\s+be\b",
        ],
        "patterns_ja": [
            r"紛争解決",
            r"仲裁",
            r"調停",
            r"訴訟",
        ],
        "severity": Severity.HIGH,
        "description": "Dispute resolution mechanism",
        "suggested_fix": "Add a dispute resolution clause specifying the mechanism (arbitration, mediation, litigation), venue, and applicable rules.",
    },
    "data_protection": {
        "patterns_en": [
            r"(?i)\bdata\s+protection\b",
            r"(?i)\bprivacy\b",
            r"(?i)\bpersonal\s+(data|information)\b",
            r"(?i)\bGDPR\b",
            r"(?i)\bdata\s+processing\b",
            r"(?i)\bdata\s+security\b",
            r"(?i)\bdata\s+breach\b",
        ],
        "patterns_ja": [
            r"個人情報",
            r"データ保護",
            r"プライバシー",
            r"個人データ",
        ],
        "severity": Severity.HIGH,
        "description": "Data protection / privacy",
        "suggested_fix": "Add a data protection clause specifying data handling obligations, compliance requirements (GDPR, etc.), breach notification, and data subject rights.",
    },
    "non_compete": {
        "patterns_en": [
            r"(?i)\bnon[\-\s]?compet(e|ition|itive)\b",
            r"(?i)\bnon[\-\s]?solicitation\b",
            r"(?i)\brestrict(ed|ive)\s+covenant\b",
            r"(?i)\bnon[\-\s]?compete\s+(clause|agreement|covenant)\b",
        ],
        "patterns_ja": [
            r"競業避止",
            r"競業禁止",
            r"勧誘禁止",
        ],
        "severity": Severity.MEDIUM,
        "description": "Non-compete / non-solicitation",
        "suggested_fix": "Add a non-compete/non-solicitation clause with reasonable scope, duration, and geographic limitations.",
    },
    "working_hours": {
        "patterns_en": [
            r"(?i)\bworking\s+hours?\b",
            r"(?i)\bscope\s+of\s+(work|services)\b",
            r"(?i)\bdeliverables?\b",
            r"(?i)\bstatement\s+of\s+work\b",
            r"(?i)\bSOW\b",
            r"(?i)\bservice\s+level\b",
            r"(?i)\bwork\s+schedule\b",
        ],
        "patterns_ja": [
            r"業務範囲",
            r"勤務時間",
            r"作業範囲",
            r"成果物",
            r"業務内容",
        ],
        "severity": Severity.MEDIUM,
        "description": "Working hours / scope definition",
        "suggested_fix": "Add a scope of work clause defining deliverables, working hours, milestones, and acceptance criteria.",
    },
    "tax_obligations": {
        "patterns_en": [
            r"(?i)\btax(es|ation)?\b",
            r"(?i)\bwithholding\b",
            r"(?i)\bVAT\b",
            r"(?i)\bsales\s+tax\b",
            r"(?i)\btax\s+obligations?\b",
        ],
        "patterns_ja": [
            r"税",
            r"源泉徴収",
            r"消費税",
            r"課税",
        ],
        "severity": Severity.MEDIUM,
        "description": "Tax obligations / withholding",
        "suggested_fix": "Add a tax clause specifying which party is responsible for taxes, withholding obligations, and tax indemnification.",
    },
    "insurance": {
        "patterns_en": [
            r"(?i)\binsurance\b",
            r"(?i)\bprofessional\s+liability\b",
            r"(?i)\berrors?\s+and\s+omissions?\b",
            r"(?i)\bE&O\b",
            r"(?i)\bworkers?\s+comp(ensation)?\b",
            r"(?i)\bcoverage\b(?=.*\b(insurance|policy|liability)\b)",
        ],
        "patterns_ja": [
            r"保険",
            r"損害保険",
            r"賠償責任保険",
        ],
        "severity": Severity.MEDIUM,
        "description": "Insurance requirements",
        "suggested_fix": "Add an insurance clause specifying required coverage types, minimum amounts, and certificate requirements.",
    },
    "amendments": {
        "patterns_en": [
            r"(?i)\bamendment[s]?\b",
            r"(?i)\bmodification[s]?\b",
            r"(?i)\b(may|shall|can)\s+(only\s+)?be\s+(amended|modified)\b",
            r"(?i)\bwritten\s+(consent|agreement|amendment)\b",
            r"(?i)\bsupplement[s]?\b",
        ],
        "patterns_ja": [
            r"変更",
            r"修正",
            r"改定",
            r"書面による合意",
        ],
        "severity": Severity.MEDIUM,
        "description": "Amendment / modification process",
        "suggested_fix": "Add an amendment clause requiring written consent of both parties for any modifications to the agreement.",
    },
    "notice": {
        "patterns_en": [
            r"(?i)\bnotice[s]?\b(?=.*\b(shall|will|must|given|sent|delivered|writing)\b)",
            r"(?i)\bwritten\s+notice\b",
            r"(?i)\bnotification[s]?\b",
            r"(?i)\bnotice\s+period\b",
            r"(?i)\b(give|provide|deliver)\s+notice\b",
        ],
        "patterns_ja": [
            r"通知",
            r"催告",
            r"書面による通知",
        ],
        "severity": Severity.LOW,
        "description": "Notice provisions",
        "suggested_fix": "Add a notice clause specifying how notices must be delivered, addresses for each party, and when notice is deemed received.",
    },
    "severability": {
        "patterns_en": [
            r"(?i)\bseverab(ility|le)\b",
            r"(?i)\binvalid(ity)?\s+(of\s+any\s+)?provision\b",
            r"(?i)\bunenforceab(le|ility)\b",
            r"(?i)\bremaining\s+provisions?\s+(shall\s+)?remain\b",
        ],
        "patterns_ja": [
            r"分離可能性",
            r"可分性",
            r"無効な条項",
        ],
        "severity": Severity.LOW,
        "description": "Severability clause",
        "suggested_fix": "Add a severability clause stating that if any provision is found invalid, the remaining provisions continue in full force and effect.",
    },
    "entire_agreement": {
        "patterns_en": [
            r"(?i)\bentire\s+agreement\b",
            r"(?i)\bwhole\s+agreement\b",
            r"(?i)\bsupersedes?\s+(all\s+)?(prior|previous)\b",
            r"(?i)\bintegration\s+clause\b",
            r"(?i)\bmerger\s+clause\b",
        ],
        "patterns_ja": [
            r"完全合意",
            r"完全なる合意",
            r"従前の合意",
        ],
        "severity": Severity.LOW,
        "description": "Entire agreement clause",
        "suggested_fix": "Add an entire agreement clause stating this agreement constitutes the complete understanding between the parties and supersedes all prior agreements.",
    },
    "assignment": {
        "patterns_en": [
            r"(?i)\bassign(ment|ed|s|ing)?\b",
            r"(?i)\bdelegat(e|ion)\b",
            r"(?i)\btransfer(ability)?\s+of\s+(this\s+)?agreement\b",
            r"(?i)\bsuccessors?\s+and\s+assigns?\b",
        ],
        "patterns_ja": [
            r"譲渡",
            r"委託",
            r"譲渡禁止",
            r"権利義務の移転",
        ],
        "severity": Severity.MEDIUM,
        "description": "Assignment / delegation restrictions",
        "suggested_fix": "Add an assignment clause specifying whether and under what conditions either party may assign their rights or obligations under this agreement.",
    },
    "warranties": {
        "patterns_en": [
            r"(?i)\bwarrant(y|ies|s)\b",
            r"(?i)\brepresentation[s]?\b",
            r"(?i)\brepresents?\s+and\s+warrants?\b",
            r"(?i)\b(as[\-\s]?is|without\s+warranty)\b",
            r"(?i)\bdisclaimer\s+of\s+warranties?\b",
        ],
        "patterns_ja": [
            r"保証",
            r"表明保証",
            r"瑕疵担保",
        ],
        "severity": Severity.MEDIUM,
        "description": "Warranty / representations",
        "suggested_fix": "Add a warranties clause specifying representations made by each party and any warranty disclaimers.",
    },
    "auto_renewal": {
        "patterns_en": [
            r"(?i)\bauto(matic)?[\-\s]?renew(al|ed|ing)?\b",
            r"(?i)\brenew(al|ed|s)?\s+(automatically|unless)\b",
            r"(?i)\bever(green)?\s+clause\b",
            r"(?i)\brenew(al)?\s+term\b",
            r"(?i)\bopt[\-\s]?out\s+period\b",
        ],
        "patterns_ja": [
            r"自動更新",
            r"自動延長",
            r"更新",
        ],
        "severity": Severity.MEDIUM,
        "description": "Auto-renewal terms and notice periods",
        "suggested_fix": "Add auto-renewal terms specifying renewal period, opt-out notice requirements, and any changes upon renewal.",
    },
}

RISK_KEYWORDS: dict[str, dict] = {
    "penalty": {
        "patterns": [r"(?i)\bpenalt(y|ies)\b"],
        "severity": Severity.HIGH,
        "explanation": "Contract contains penalty clauses which may impose financial burden.",
    },
    "unlimited_liability": {
        "patterns": [r"(?i)\bunlimited\s+liability\b"],
        "severity": Severity.CRITICAL,
        "explanation": "Unlimited liability exposure detected. This could result in uncapped financial risk.",
    },
    "unilateral": {
        "patterns": [r"(?i)\bunilateral(ly)?\b"],
        "severity": Severity.HIGH,
        "explanation": "Unilateral provisions detected. One party can make changes without the other's consent.",
    },
    "waive": {
        "patterns": [r"(?i)\bwaive[s]?\b", r"(?i)\bwaiver\b"],
        "severity": Severity.MEDIUM,
        "explanation": "Waiver provisions detected. Rights may be given up.",
    },
    "forfeit": {
        "patterns": [r"(?i)\bforfeit(ure|s|ed)?\b"],
        "severity": Severity.HIGH,
        "explanation": "Forfeiture provisions detected. Assets or rights may be lost.",
    },
    "sole_discretion": {
        "patterns": [r"(?i)\b(at\s+)?(sole|absolute)\s+discretion\b", r"(?i)\bin\s+its\s+sole\s+judgment\b"],
        "severity": Severity.HIGH,
        "explanation": "Sole discretion clause detected. Gives one party unilateral decision-making power.",
    },
    "irrevocable": {
        "patterns": [r"(?i)\birrevocabl(e|y)\b"],
        "severity": Severity.HIGH,
        "explanation": "Irrevocable provisions detected. Commitments cannot be reversed.",
    },
    "perpetual": {
        "patterns": [r"(?i)\bperpetual(ly)?\b", r"(?i)\bin\s+perpetuity\b"],
        "severity": Severity.HIGH,
        "explanation": "Perpetual obligations detected. No time limit on commitments.",
    },
    "worldwide": {
        "patterns": [r"(?i)\bworldwide\b", r"(?i)\bglobal(ly)?\b(?=.*\b(license|right|grant)\b)"],
        "severity": Severity.MEDIUM,
        "explanation": "Worldwide scope detected. Obligations or rights extend globally.",
    },
    "non_exclusive": {
        "patterns": [r"(?i)\bnon[\-\s]?exclusive\b"],
        "severity": Severity.LOW,
        "explanation": "Non-exclusive terms detected. Other parties may receive similar rights.",
    },
}

STRUCTURAL_ELEMENTS = {
    "parties": {
        "patterns_en": [
            r"(?i)\b(between|by\s+and\s+between)\b",
            r"(?i)\b(party|parties)\b",
            r"(?i)\b(hereinafter|herein)\b",
            r"(?i)\b(the\s+)?(company|contractor|client|vendor|supplier|employer|employee)\b",
        ],
        "patterns_ja": [
            r"甲",
            r"乙",
            r"当事者",
            r"契約当事者",
        ],
        "description": "Contract parties identification",
    },
    "dates": {
        "patterns_en": [
            r"(?i)\beffective\s+date\b",
            r"(?i)\bdated?\s+(as\s+of\s+)?\w+\s+\d+",
            r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}",
            r"(?i)\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}",
            r"(?i)\bcommencement\s+date\b",
        ],
        "patterns_ja": [
            r"令和\d+年",
            r"平成\d+年",
            r"\d{4}年\d{1,2}月\d{1,2}日",
            r"効力発生日",
            r"契約日",
        ],
        "description": "Contract dates",
    },
    "signatures": {
        "patterns_en": [
            r"(?i)\bsignat(ure|ory|ories)\b",
            r"(?i)\bsigned\s+by\b",
            r"(?i)\bIN\s+WITNESS\s+WHEREOF\b",
            r"(?i)\bexecut(e|ed|ion)\b.*\b(agreement|contract)\b",
            r"(?i)\bauthorized\s+(representative|signatory)\b",
        ],
        "patterns_ja": [
            r"署名",
            r"記名押印",
            r"記名捺印",
            r"代表者",
        ],
        "description": "Signature block",
    },
    "definitions": {
        "patterns_en": [
            r"(?i)\bdefinition[s]?\b",
            r"""(?i)[""\u201c][A-Z][^""\u201d]+[""\u201d]\s+(means?|shall\s+mean|refers?\s+to)\b""",
            r"(?i)\bfor\s+the\s+purpose[s]?\s+of\s+this\b",
            r"(?i)\bas\s+defined\s+(herein|below|above)\b",
        ],
        "patterns_ja": [
            r"定義",
            r"とは",
            r"以下の意味",
        ],
        "description": "Definitions section",
    },
}


class RuleBasedAnalyzer:
    """Layer 1: Deterministic rule-based contract analysis engine."""

    def __init__(self):
        self.mandatory_patterns = MANDATORY_CLAUSE_PATTERNS
        self.risk_keywords = RISK_KEYWORDS
        self.structural_elements = STRUCTURAL_ELEMENTS

    def analyze(self, text: str, language: str = "en") -> dict:
        """Run complete rule-based analysis on contract text."""
        return {
            "mandatory_clauses": self._check_mandatory_clauses(text, language),
            "risk_keywords": self._scan_risk_keywords(text),
            "structural_validation": self._validate_structure(text, language),
            "missing_clauses": self._get_missing_clauses(text, language),
        }

    def _check_mandatory_clauses(self, text: str, language: str) -> list[RuleFinding]:
        """Check for presence of all mandatory clauses."""
        findings = []
        lang_key = "patterns_ja" if language.lower() in ("ja", "jp", "japanese") else "patterns_en"

        for clause_name, config in self.mandatory_patterns.items():
            patterns = config.get(lang_key, config.get("patterns_en", []))
            detected = False
            matched_text = ""

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    detected = True
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    matched_text = text[start:end].strip()
                    break

            if detected:
                findings.append(RuleFinding(
                    clause_type=clause_name,
                    detected=True,
                    severity=Severity.INFO,
                    confidence=95.0,
                    clause_text=matched_text,
                    explanation=f"{config['description']} detected in contract.",
                    suggested_fix="",
                ))
            else:
                findings.append(RuleFinding(
                    clause_type=clause_name,
                    detected=False,
                    severity=config["severity"],
                    confidence=100.0,
                    clause_text="",
                    explanation=f"MISSING: {config['description']} not found in contract.",
                    suggested_fix=config["suggested_fix"],
                ))

        return findings

    def _scan_risk_keywords(self, text: str) -> list[RuleFinding]:
        """Scan for risky keywords and phrases."""
        findings = []

        for keyword_name, config in self.risk_keywords.items():
            for pattern in config["patterns"]:
                matches = list(re.finditer(pattern, text))
                if matches:
                    for match in matches:
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 100)
                        context = text[start:end].strip()

                        findings.append(RuleFinding(
                            clause_type=f"risk_keyword_{keyword_name}",
                            detected=True,
                            severity=config["severity"],
                            confidence=90.0,
                            clause_text=context,
                            explanation=config["explanation"],
                            suggested_fix=f"Review and negotiate the '{keyword_name.replace('_', ' ')}' provision to ensure balanced terms.",
                        ))
                    break

        return findings

    def _validate_structure(self, text: str, language: str) -> list[RuleFinding]:
        """Validate contract structural elements."""
        findings = []
        lang_key = "patterns_ja" if language.lower() in ("ja", "jp", "japanese") else "patterns_en"

        for element_name, config in self.structural_elements.items():
            patterns = config.get(lang_key, config.get("patterns_en", []))
            detected = False
            matched_text = ""

            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    detected = True
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    matched_text = text[start:end].strip()
                    break

            severity = Severity.CRITICAL if not detected else Severity.INFO
            findings.append(RuleFinding(
                clause_type=f"structure_{element_name}",
                detected=detected,
                severity=severity,
                confidence=95.0 if detected else 100.0,
                clause_text=matched_text,
                explanation=f"{'Found' if detected else 'MISSING'}: {config['description']}",
                suggested_fix="" if detected else f"Add {config['description'].lower()} to the contract.",
            ))

        return findings

    def _get_missing_clauses(self, text: str, language: str) -> list[str]:
        """Return list of missing mandatory clause types."""
        findings = self._check_mandatory_clauses(text, language)
        return [f.clause_type for f in findings if not f.detected]

    def get_all_findings(self, text: str, language: str = "en") -> list[RuleFinding]:
        """Get flattened list of all findings for the pipeline."""
        result = self.analyze(text, language)
        all_findings = []
        all_findings.extend(result["mandatory_clauses"])
        all_findings.extend(result["risk_keywords"])
        all_findings.extend(result["structural_validation"])
        return all_findings
