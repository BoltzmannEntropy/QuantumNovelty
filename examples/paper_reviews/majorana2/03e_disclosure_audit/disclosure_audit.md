# DISCLOSURE AUDIT REPORT

## Compliance status by category
| Code | Category | Status | Evidence (section or "absent") | Required for venue? |
|------|----------|--------|--------------------------------|---------------------|
| A1 | Funding statement | ABSENT | absent | Yes |
| A2 | Competing interests / COI | ABSENT | absent | Yes |
| A3 | Author contributions | ABSENT | absent | Yes |
| A4 | Data availability | ABSENT | absent | Yes |
| A5 | Code availability | ABSENT | absent | Yes |
| A6 | Ethics / IRB approval | NOT-APPLICABLE | Pure device/experimental physics paper with no human/animal subjects | No |
| A7 | Preprint / prior-publication status | PRESENT-COMPLETE | "arXiv:2606.03884v1 [cond-mat.mes-hall] 2 Jun 2026" on page 1 | Yes |
| A8 | Materials availability | ABSENT | absent | Yes |
| B1 | AI-assisted text drafting | ABSENT | absent | Yes (if applicable) |
| B2 | AI-generated images/figures | ABSENT | absent | Yes (if applicable) |
| B3 | AI-assisted data analysis or coding | ABSENT | absent | Yes (if applicable) |
| B4 | AI-assisted pre-submission review | ABSENT | absent | Yes (if applicable) |
| C1 | Prior-publication warranty | ABSENT | absent | Yes |
| C2 | Government / institutional / export-control approval | ABSENT | absent | Yes (quantum hardware work) |
| C3 | Third-party rights | ABSENT | absent | Yes (if applicable) |
| C4 | Free-online-version conflict | PRESENT-INCOMPLETE | arXiv preprint exists; PRX Quantum permits arXiv but manuscript lacks explicit statement of compliance | Yes |

## Missing disclosures and warranty gaps

### Submission-blocking
- **A1 (Funding statement)**: No funding sources or grant numbers disclosed. Microsoft Quantum authorship implies corporate funding but explicit statement required.
- **A2 (Competing interests)**: No COI declaration. All authors affiliated with Microsoft Quantum, which has commercial interest in quantum computing; financial/employment conflicts must be declared.
- **A3 (Author contributions)**: Group authorship "Microsoft Quantum†" with footnote listing 150+ contributors but no CRediT-style role assignments.
- **A4 (Data availability)**: No statement regarding experimental data, processed datasets, or access procedures.
- **A5 (Code availability)**: References to simulations and analysis code (e.g., TGP protocol, fitting procedures) but no repository, license, or availability statement.
- **C1 (Prior-publication warranty)**: No explicit statement that manuscript is not under consideration elsewhere.

### Revise-before-acceptance
- **A8 (Materials availability)**: Device fabrication involves proprietary InAs–Pb heterostructures, GaSb substrates, and specific epitaxial growth. No MTA information or availability statement provided.
- **C2 (Government/institutional/export-control approval)**: Quantum computing hardware may be subject to export controls; no pre-publication clearance statement.
- **B1–B4 (AI disclosures)**: PRX Quantum increasingly requires disclosure of AI assistance. Authors must confirm whether AI tools were used and provide explicit negative statement if not.

### Editorial-discretion
- **C3 (Third-party rights)**: All figures appear original. Confirm no reuse requiring permission.
- **C4 (Free-online-version conflict)**: arXiv posting compatible with PRX Quantum policy but explicit acknowledgment recommended.

## Submission-ready checklist
| Code | Status | Fix Required |
|------|--------|--------------|
| A1 | FAIL | Add funding statement with grant numbers or "This work was funded internally by Microsoft Corporation with no external grant support." |
| A2 | FAIL | Add competing interests declaration: all authors are employees of Microsoft Corporation which is developing commercial quantum computing technology. |
| A3 | FAIL | Add CRediT-style author contributions for the 150+ listed contributors or designate writing committee with specific roles. |
| A4 | FAIL | Add data availability statement specifying repository/access or "Data available from corresponding author upon reasonable request." |
| A5 | FAIL | Add code availability statement with repository URL and license, or explicit "Code available upon reasonable request" with justification. |
| A6 | PASS | Not applicable for device physics paper. |
| A7 | PASS | arXiv ID present: 2606.03884v1. |
| A8 | FAIL | Add materials availability statement addressing InAs–Pb heterostructure availability, fabrication protocols, and MTA requirements. |
| B1 | FAIL | Add explicit statement: "AI tools were [not] used for text drafting" with model/scope if applicable. |
| B2 | FAIL | Add explicit statement: "All figures were created without AI assistance" or disclose tools used. |
| B3 | FAIL | Add explicit statement regarding AI use in data analysis/coding or confirm none used. |
| B4 | FAIL | Add explicit statement regarding AI-assisted review or confirm none used. |
| C1 | FAIL | Add warranty: "This manuscript has not been published previously and is not under consideration at another journal." |
| C2 | FAIL | Add statement confirming institutional/export-control pre-publication approval for quantum hardware disclosure. |
| C3 | PASS | Requires author confirmation that all figures are original; no obvious third-party content identified. |
| C4 | PASS | arXiv preprint policy compatible with PRX Quantum; recommend adding explicit statement. |

```json
{"items": [{"code": "A1", "status": "ABSENT", "severity": "submission-blocking"}, {"code": "A2", "status": "ABSENT", "severity": "submission-blocking"}, {"code": "A3", "status": "ABSENT", "severity": "submission-blocking"}, {"code": "A4", "status": "ABSENT", "severity": "submission-blocking"}, {"code": "A5", "status": "ABSENT", "severity": "submission-blocking"}, {"code": "A6", "status": "NOT-APPLICABLE", "severity": "none"}, {"code": "A7", "status": "PRESENT-COMPLETE", "severity": "none"}, {"code": "A8", "status": "ABSENT", "severity": "revise-before-acceptance"}, {"code": "B1", "status": "ABSENT", "severity": "revise-before-acceptance"}, {"code": "B2", "status": "ABSENT", "severity": "revise-before-acceptance"}, {"code": "B3", "status": "ABSENT", "severity": "revise-before-acceptance"}, {"code": "B4", "status": "ABSENT", "severity": "revise-before-acceptance"}, {"code": "C1", "status": "ABSENT", "severity": "submission-blocking"}, {"code": "C2", "status": "ABSENT", "severity": "revise-before-acceptance"}, {"code": "C3", "status": "ABSENT", "severity": "editorial-discretion"}, {"code": "C4", "status": "PRESENT-INCOMPLETE", "severity": "editorial-discretion"}], "blocking": 6, "incomplete": 1, "not_applicable": 1}
```