
"""
FINIA-RECON
Motor de reglas de negocio para conciliación financiera.

Este módulo no utiliza IA. Sus resultados son determinísticos
y constituyen la fuente de verdad para el agente inteligente.
"""

from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from datetime import datetime


REQUIRED_FIELDS = (
    "transaction_id",
    "amount",
    "date",
    "status"
)

VALID_STATUSES = {
    "COMPLETED",
    "PENDING",
    "FAILED",
    "CANCELLED"
}


def validate_transactions(records, source):
    """Valida los registros y separa los datos incorrectos."""
    valid = []
    issues = []

    for index, record in enumerate(records):
        errors = []

        if not isinstance(record, dict):
            issues.append({
                "transaction_id": f"INVALID-{source}-{index}",
                "rule_codes": ["RB08"],
                "severity": "HIGH",
                "status": "INVALID",
                "message": "El registro no tiene un formato válido.",
                "source": source
            })
            continue

        for field in REQUIRED_FIELDS:
            if field not in record or record[field] is None:
                errors.append(f"Falta el campo {field}")

        tx_id = record.get("transaction_id")

        if not isinstance(tx_id, str) or not tx_id.strip():
            errors.append("Identificador de transacción inválido")

        try:
            amount = Decimal(str(record.get("amount")))
            if not amount.is_finite() or amount < 0:
                errors.append("Monto inválido")
        except (InvalidOperation, TypeError, ValueError):
            errors.append("Monto inválido")

        try:
            datetime.strptime(record.get("date", ""), "%Y-%m-%d")
        except (ValueError, TypeError):
            errors.append("Fecha inválida")

        status = record.get("status")
        if not isinstance(status, str) or status.upper() not in VALID_STATUSES:
            errors.append("Estado inválido")

        if errors:
            issues.append({
                "transaction_id": (
                    tx_id if isinstance(tx_id, str) and tx_id.strip()
                    else f"INVALID-{source}-{index}"
                ),
                "rule_codes": ["RB08"],
                "severity": "HIGH",
                "status": "INVALID",
                "message": "Información insuficiente o inválida.",
                "evidence": errors,
                "source": source
            })
        else:
            valid.append({
                **record,
                "transaction_id": tx_id.strip(),
                "amount": str(Decimal(str(record["amount"]))),
                "date": record["date"],
                "status": status.upper()
            })

    return valid, issues


def evaluate_rules(internal, processor):
    """
    Evalúa las ocho reglas de negocio.

    RB01: Coincidencia.
    RB02: Diferencia de montos.
    RB03: Transacción faltante.
    RB04: Duplicidad.
    RB05: Diferencia de fechas.
    RB06: Diferencia de estados.
    RB07: Ambigüedad.
    RB08: Información insuficiente.
    """

    bank, bank_issues = validate_transactions(internal, "BANK")
    payment, payment_issues = validate_transactions(
        processor, "PROCESSOR"
    )

    results = bank_issues + payment_issues

    bank_groups = defaultdict(list)
    payment_groups = defaultdict(list)

    for record in bank:
        bank_groups[record["transaction_id"]].append(record)

    for record in payment:
        payment_groups[record["transaction_id"]].append(record)

    all_ids = sorted(set(bank_groups) | set(payment_groups))

    for tx_id in all_ids:
        bank_records = bank_groups.get(tx_id, [])
        payment_records = payment_groups.get(tx_id, [])

        bank_count = len(bank_records)
        payment_count = len(payment_records)

        # RB04: Duplicidad
        if bank_count > 1 or payment_count > 1:
            duplicated_sources = []

            if bank_count > 1:
                duplicated_sources.append("BANK")

            if payment_count > 1:
                duplicated_sources.append("PROCESSOR")

            results.append({
                "transaction_id": tx_id,
                "rule_codes": ["RB04", "RB07"],
                "severity": "CRITICAL",
                "status": "AMBIGUOUS",
                "message": "Se detectó una transacción duplicada.",
                "evidence": {
                    "bank_records": bank_count,
                    "processor_records": payment_count,
                    "duplicated_sources": duplicated_sources
                },
                "recommendation": (
                    "Revisar los registros duplicados antes "
                    "de realizar cualquier conciliación."
                )
            })
            continue

        # RB03: Transacción faltante
        if bank_count == 0 or payment_count == 0:
            missing_source = "BANK" if bank_count == 0 else "PROCESSOR"

            results.append({
                "transaction_id": tx_id,
                "rule_codes": ["RB03"],
                "severity": "CRITICAL",
                "status": "MISSING",
                "message": "La transacción no existe en una de las fuentes.",
                "evidence": {
                    "missing_source": missing_source
                },
                "recommendation": (
                    "Verificar el origen de la operación y "
                    "confirmar su registro."
                )
            })
            continue

        bank_tx = bank_records[0]
        payment_tx = payment_records[0]

        rule_codes = []
        evidence = []
        severity = "INFO"

        # RB02: Diferencia de montos
        if Decimal(bank_tx["amount"]) != Decimal(payment_tx["amount"]):
            rule_codes.append("RB02")
            evidence.append({
                "field": "amount",
                "bank": bank_tx["amount"],
                "processor": payment_tx["amount"]
            })
            severity = "HIGH"

        # RB05: Diferencia de fechas
        if bank_tx["date"] != payment_tx["date"]:
            rule_codes.append("RB05")
            evidence.append({
                "field": "date",
                "bank": bank_tx["date"],
                "processor": payment_tx["date"]
            })

            if severity != "HIGH":
                severity = "MEDIUM"

        # RB06: Diferencia de estados
        if bank_tx["status"] != payment_tx["status"]:
            rule_codes.append("RB06")
            evidence.append({
                "field": "status",
                "bank": bank_tx["status"],
                "processor": payment_tx["status"]
            })
            severity = "HIGH"

        # RB01: Coincidencia completa
        if not rule_codes:
            rule_codes.append("RB01")

        results.append({
            "transaction_id": tx_id,
            "rule_codes": rule_codes,
            "severity": severity,
            "status": "MATCHED" if rule_codes == ["RB01"] else "DISCREPANCY",
            "message": (
                "Transacción conciliada correctamente."
                if rule_codes == ["RB01"]
                else "Se detectaron diferencias entre las fuentes."
            ),
            "evidence": evidence,
            "recommendation": (
                "No requiere intervención."
                if rule_codes == ["RB01"]
                else "Solicitar revisión del operador financiero."
            )
        })

    return results