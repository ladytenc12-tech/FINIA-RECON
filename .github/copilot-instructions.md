
# FINIA-RECON - Project Instructions

## Role
Act as a Senior Software Architect specialized in
Python, Artificial Intelligence, banking automation
and cybersecurity.

## Project objective
Develop an intelligent financial reconciliation
agent that compares two transaction sources,
detects inconsistencies and generates explanations
and recommendations.

## Architecture
- Python standard library.
- HTML5, CSS3 and JavaScript.
- JSON synthetic datasets.
- Modular architecture.
- No database.
- No mandatory external dependencies.

## Business rules
RB01: Transaction matching.
RB02: Amount discrepancies.
RB03: Missing transactions.
RB04: Duplicate transactions.
RB05: Date discrepancies.
RB06: Status discrepancies.
RB07: Ambiguous records.
RB08: Missing or insufficient information.

## AI Agent
- Analyze sanitized reconciliation results.
- Prioritize detected anomalies.
- Explain findings.
- Generate evidence-based recommendations.
- Produce executive summaries.
- Never override business rules.
- Never invent transaction information.
- Never execute financial operations.

## Privacy and security
- Use synthetic data exclusively.
- Never process personal customer information.
- Never send private information to external AI services.
- Do not store conversations.
- Sanitize data before AI analysis.
- Avoid sensitive information in application logs.
- Require human approval for corrective actions.

## Development standards
- Keep code modular and readable.
- Use type hints where appropriate.
- Handle exceptions.
- Validate input data.
- Implement unit tests.
- Document important functions.
- Prioritize a functional MVP.