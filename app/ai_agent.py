"""Agente FINIA: el motor de reglas es la fuente de verdad; el LLM explica."""
import json
import os
from typing import Any


class FinancialReconciliationAgent:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.5")

    def analyze(self, report: dict[str, Any]) -> dict[str, Any]:
        deterministic = self._rule_based_analysis(report)
        if not self.api_key:
            deterministic["agent_type"] = "RULE_BASED_FALLBACK"
            deterministic["ai_status"] = "NOT_CONFIGURED"
            deterministic["notice"] = (
                "Configura OPENAI_API_KEY para activar las explicaciones generadas por IA. "
                "Las reglas de negocio sí se ejecutaron correctamente."
            )
            return deterministic
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            safe_payload = {
                "summary": report.get("summary", {}),
                "findings": [
                    {
                        "transaction_id": item.get("transaction_id"),
                        "status": item.get("status"),
                        "severity": item.get("severity"),
                        "rule_codes": item.get("rule_codes", []),
                        "evidence": item.get("evidence", []),
                        "message": item.get("message", ""),
                    }
                    for item in report.get("transactions", [])
                    if item.get("status") != "MATCHED"
                ][:80],
            }
            response = client.responses.create(
                model=self.model,
                instructions=(
                    "Eres FINIA, analista de conciliación financiera. "
                    "Explica únicamente los hechos presentes en el JSON. "
                    "Distingue hechos de hipótesis, no inventes causas ni datos, "
                    "no indiques que una operación fue fraudulenta sin evidencia. "
                    "No ordenes ejecutar ajustes ni modificar saldos. "
                    "Devuelve exclusivamente JSON válido con las claves: "
                    "executive_analysis (string), risk_level (LOW|MEDIUM|HIGH|CRITICAL), "
                    "key_findings (array de strings), recommendations (array de objetos "
                    "con priority y action), operator_guidance (string)."
                ),
                input=json.dumps(safe_payload, ensure_ascii=False),
            )
            parsed = json.loads(response.output_text)
            return {
                **deterministic,
                **parsed,
                "agent": "FINIA-RECON AI",
                "agent_type": "OPENAI_RESPONSES_API",
                "ai_status": "ACTIVE",
                "model": self.model,
                "human_approval_required": True,
                "execution_authorized": False,
            }
        except Exception as exc:
            deterministic["agent_type"] = "RULE_BASED_FALLBACK"
            deterministic["ai_status"] = "ERROR"
            deterministic["notice"] = f"No se pudo consultar el modelo IA. Se conserva el análisis por reglas. Detalle: {type(exc).__name__}"
            return deterministic

    def _rule_based_analysis(self, report: dict[str, Any]) -> dict[str, Any]:
        summary = report.get("summary", {})
        alerts = []
        for tx in report.get("transactions", []):
            if tx.get("status") == "MATCHED":
                continue
            alerts.append({
                "transaction_id": tx.get("transaction_id"),
                "status": tx.get("status"),
                "severity": tx.get("severity", "INFO"),
                "rule_codes": tx.get("rule_codes", []),
                "explanation": tx.get("message", "Requiere revisión."),
                "evidence": tx.get("evidence", []),
                "recommendation": tx.get("recommendation", "Revisar evidencia de origen."),
            })
        sev = summary.get("severity", {})
        risk = "CRITICAL" if sev.get("critical", 0) else "HIGH" if sev.get("high", 0) else "MEDIUM" if sev.get("medium", 0) else "LOW"
        recommendations = []
        for key, priority, action in [
            ("ambiguous", "CRITICAL", "Investigar duplicados y coincidencias ambiguas antes de aprobar operaciones."),
            ("missing", "CRITICAL", "Solicitar evidencia a la fuente donde no aparece la transacción."),
            ("discrepancies", "HIGH", "Comparar comprobantes y registros de origen para resolver diferencias."),
            ("invalid", "HIGH", "Corregir el formato o completar los campos requeridos en el archivo de origen."),
        ]:
            if summary.get(key, 0):
                recommendations.append({"priority": priority, "action": action})
        if not recommendations:
            recommendations.append({"priority": "INFO", "action": "Mantener el monitoreo periódico; no se detectaron inconsistencias."})
        return {
            "agent": "FINIA-RECON AI", "agent_type": "RULE_BASED_FALLBACK",
            "ai_status": "NOT_CONFIGURED", "executive_analysis": (
                f"Se analizaron {summary.get('total_analyzed', 0)} operaciones: "
                f"{summary.get('matched', 0)} conciliadas y {summary.get('pending_review', 0)} pendientes. "
                f"La tasa de conciliación es {summary.get('reconciliation_rate', 0)}%."
            ),
            "risk_level": risk, "alerts": alerts, "recommendations": recommendations,
            "human_approval_required": True, "execution_authorized": False,
        }
