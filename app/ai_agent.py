
from decimal import Decimal, InvalidOperation


class FinancialReconciliationAgent:

    PRIORITY = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "INFO": 4
    }

    def analyze(self, report):
        transactions = report.get("transactions", [])
        summary = report.get("summary", {})

        alerts = self._analyze_alerts(transactions)

        alerts.sort(
            key=lambda alert: self.PRIORITY.get(
                alert["severity"], 5
            )
        )

        return {
            "agent": "FINIA-RECON AI AGENT",
            "agent_type": "RULE_BASED_FINANCIAL_ANALYSIS",
            "executive_analysis": self._executive_analysis(summary),
            "risk_level": self._calculate_risk(summary),
            "alerts": alerts,
            "recommendations": self._generate_recommendations(summary),
            "human_approval_required": True,
            "execution_authorized": False
        }

    def _analyze_alerts(self, transactions):
        alerts = []

        for transaction in transactions:
            status = transaction.get("status")
            severity = transaction.get("severity", "INFO")

            if status == "MATCHED":
                continue

            rule_codes = transaction.get("rule_codes", [])
            evidence = transaction.get("evidence", [])

            alerts.append({
                "transaction_id": transaction.get("transaction_id"),
                "status": status,
                "severity": severity,
                "rule_codes": rule_codes,
                "explanation": self._explain(
                    rule_codes, evidence, transaction
                ),
                "evidence": evidence,
                "recommendation": transaction.get("recommendation")
            })

        return alerts

    def _explain(self, rule_codes, evidence, transaction):
        explanations = []

        for rule in rule_codes:

            if rule == "RB02":
                for item in evidence:
                    if isinstance(item, dict) and item.get("field") == "amount":
                        bank = item.get("bank")
                        processor = item.get("processor")

                        try:
                            difference = abs(
                                Decimal(str(bank)) -
                                Decimal(str(processor))
                            )
                            explanations.append(
                                f"Diferencia de monto: BANK registra "
                                f"{bank} y PROCESSOR registra {processor}. "
                                f"La diferencia es {difference}."
                            )
                        except (InvalidOperation, TypeError):
                            explanations.append(
                                "Se detectó una diferencia entre los montos "
                                "de BANK y PROCESSOR."
                            )

            elif rule == "RB03":
                missing_source = None

                for item in evidence:
                    if isinstance(item, dict):
                        missing_source = item.get("missing_source")

                if missing_source:
                    explanations.append(
                        f"La transacción no existe en la fuente "
                        f"{missing_source}."
                    )
                else:
                    explanations.append(
                        "La transacción está registrada en una fuente, "
                        "pero no se encontró en la otra."
                    )

            elif rule == "RB04" or rule == "RB07":
                for item in evidence:
                    if isinstance(item, dict):
                        duplicated_sources = item.get(
                            "duplicated_sources", []
                        )
                        if duplicated_sources:
                            explanations.append(
                                "Se detectaron registros duplicados en: "
                                + ", ".join(duplicated_sources) + "."
                            )
                            break

                if not explanations:
                    explanations.append(
                        "Se detectó una posible duplicidad de registros."
                    )

            elif rule == "RB05":
                for item in evidence:
                    if isinstance(item, dict) and item.get("field") == "date":
                        explanations.append(
                            f"Diferencia de fecha: BANK registra "
                            f"{item.get('bank')} y PROCESSOR registra "
                            f"{item.get('processor')}."
                        )

            elif rule == "RB06":
                for item in evidence:
                    if isinstance(item, dict) and item.get("field") == "status":
                        explanations.append(
                            f"Diferencia de estado: BANK registra "
                            f"{item.get('bank')} y PROCESSOR registra "
                            f"{item.get('processor')}."
                        )

            elif rule == "RB08":
                explanations.append(
                    "El registro presenta errores de validación: "
                    + self._format_validation_evidence(evidence)
                )

        if not explanations:
            explanations.append(
                transaction.get(
                    "message",
                    "La transacción requiere revisión."
                )
            )

        return " ".join(explanations)

    def _format_validation_evidence(self, evidence):
        if not evidence:
            return "no se proporcionó detalle."

        messages = []

        for item in evidence:
            if isinstance(item, str):
                messages.append(item)
            elif isinstance(item, dict):
                messages.append(str(item))

        return "; ".join(messages) if messages else "detalle no disponible."

    def _executive_analysis(self, summary):
        total = summary.get("total_analyzed", 0)
        matched = summary.get("matched", 0)
        pending = summary.get("pending_review", 0)
        rate = summary.get("reconciliation_rate", 0)

        if pending == 0:
            return (
                f"Se analizaron {total} registros y todos fueron "
                f"conciliados correctamente. Tasa de conciliación: {rate}%."
            )

        return (
            f"Se analizaron {total} registros financieros. "
            f"{matched} fueron conciliados correctamente y "
            f"{pending} requieren revisión. "
            f"La tasa de conciliación es {rate}%. "
            "Se recomienda priorizar las alertas críticas y altas."
        )

    def _calculate_risk(self, summary):
        severity = summary.get("severity", {})

        critical = severity.get("critical", 0)
        high = severity.get("high", 0)
        medium = severity.get("medium", 0)

        if critical > 0:
            return "CRITICAL"

        if high > 0:
            return "HIGH"

        if medium > 0:
            return "MEDIUM"

        return "LOW"

    def _generate_recommendations(self, summary):
        recommendations = []

        if summary.get("ambiguous", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "action": (
                    "Investigar los registros duplicados antes de "
                    "autorizar cualquier conciliación."
                )
            })

        if summary.get("missing", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "action": (
                    "Verificar los registros faltantes con las fuentes "
                    "de origen y los reportes del procesador."
                )
            })

        if summary.get("discrepancies", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "action": (
                    "Revisar las diferencias de monto, fecha y estado "
                    "entre los sistemas."
                )
            })

        if summary.get("invalid", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "action": (
                    "Corregir o investigar los registros que no superaron "
                    "las validaciones de datos."
                )
            })

        if not recommendations:
            recommendations.append({
                "priority": "INFO",
                "action": (
                    "No se detectaron inconsistencias. Mantener el "
                    "monitoreo periódico del proceso."
                )
            })

        return recommendations
