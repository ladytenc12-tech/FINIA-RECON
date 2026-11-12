
"""
FINIA-RECON
Módulo de conciliación financiera.

Coordina la carga de fuentes, ejecución de reglas
y generación de indicadores para el agente IA.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

from app.business_rules import evaluate_rules


# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_transactions(filename):
    """Carga y verifica un archivo JSON de transacciones."""

    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {filename}"
        )

    try:
        with file_path.open("r", encoding="utf-8") as file:
            records = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"El archivo {filename} contiene JSON inválido."
        ) from error

    if not isinstance(records, list):
        raise ValueError(
            f"El archivo {filename} debe contener una lista."
        )

    return records


def build_summary(results):
    """Genera indicadores del proceso de conciliación."""

    status_counts = Counter(
        result["status"] for result in results
    )

    severity_counts = Counter(
        result["severity"] for result in results
    )

    rule_counts = Counter(
        code
        for result in results
        for code in result.get("rule_codes", [])
    )

    total = len(results)

    matched = status_counts["MATCHED"]

    discrepancies = status_counts["DISCREPANCY"]

    missing = status_counts["MISSING"]

    ambiguous = status_counts["AMBIGUOUS"]

    invalid = status_counts["INVALID"]

    return {
        "total_analyzed": total,
        "matched": matched,
        "discrepancies": discrepancies,
        "missing": missing,
        "ambiguous": ambiguous,
        "invalid": invalid,
        "pending_review": (
            discrepancies + missing + ambiguous + invalid
        ),
        "reconciliation_rate": round(
            matched / total * 100, 2
        ) if total else 0,
        "severity": {
            "critical": severity_counts["CRITICAL"],
            "high": severity_counts["HIGH"],
            "medium": severity_counts["MEDIUM"],
            "info": severity_counts["INFO"]
        },
        "rules_triggered": dict(rule_counts)
    }


def run_reconciliation():
    """
    Ejecuta el proceso completo de conciliación.

    Devuelve resultados estructurados y un resumen
    sin almacenar información personal.
    """

    internal = load_transactions("internal.json")

    processor = load_transactions("processor.json")

    results = evaluate_rules(internal, processor)

    summary = build_summary(results)

    report = {
        "project": "FINIA-RECON",
        "process": "FINANCIAL_RECONCILIATION",
        "executed_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "sources": {
            "internal_records": len(internal),
            "processor_records": len(processor)
        },
        "summary": summary,
        "transactions": results
    }

    return report


def print_report(report):
    """Muestra un resumen del proceso en consola."""

    summary = report["summary"]

    print("\n" + "=" * 50)
    print(" FINIA-RECON | INFORME DE CONCILIACION")
    print("=" * 50)

    print(f"Total analizado: {summary['total_analyzed']}")
    print(f"Conciliadas: {summary['matched']}")
    print(f"Inconsistencias: {summary['discrepancies']}")
    print(f"Faltantes: {summary['missing']}")
    print(f"Ambiguas: {summary['ambiguous']}")
    print(f"Invalidas: {summary['invalid']}")

    print(
        f"Porcentaje de conciliacion: "
        f"{summary['reconciliation_rate']}%"
    )

    print("\nALERTAS POR SEVERIDAD")

    for severity, count in summary["severity"].items():
        print(f"{severity.upper()}: {count}")

    print("\nREGLAS ACTIVADAS")

    for rule, count in summary["rules_triggered"].items():
        print(f"{rule}: {count}")

    print("=" * 50)


if __name__ == "__main__":
    try:
        report = run_reconciliation()
        print_report(report)

    except (FileNotFoundError, ValueError) as error:
        print(f"Error de conciliacion: {error}")