
const API_URL = "/api";

const reconcileBtn = document.getElementById("reconcileBtn");
const resultsContainer = document.getElementById("results");
const alertsContainer = document.getElementById("alerts");

// Evita insertar contenido HTML no confiable directamente.
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);
}

function statusLabel(status) {
    const labels = {
        MATCHED: "Conciliada",
        DISCREPANCY: "Inconsistencia",
        MISSING: "Faltante",
        AMBIGUOUS: "Ambigua",
        INVALID: "Inválida"
    };

    return labels[status] || status || "Sin estado";
}

function severityLabel(severity) {
    return severity || "INFO";
}

// Actualiza las tarjetas del dashboard.
function renderSummary(summary) {
    document.getElementById("total").textContent =
        summary.total_analyzed ?? 0;

    document.getElementById("matched").textContent =
        summary.matched ?? 0;

    document.getElementById("inconsistent").textContent =
        summary.discrepancies ?? 0;

    document.getElementById("missing").textContent =
        summary.missing ?? 0;

    document.getElementById("ambiguous").textContent =
        summary.ambiguous ?? 0;
}

// Presenta los resultados de cada transacción.
function renderResults(report) {
    const transactions = report.transactions || [];
    const summary = report.summary || {};

    if (transactions.length === 0) {
        resultsContainer.innerHTML =
            "<p>No existen transacciones para mostrar.</p>";
        return;
    }

    const rows = transactions.map(transaction => `
        <tr>
            <td>${escapeHTML(transaction.transaction_id)}</td>
            <td>${escapeHTML(statusLabel(transaction.status))}</td>
            <td>${escapeHTML(severityLabel(transaction.severity))}</td>
            <td>${escapeHTML(
                (transaction.rule_codes || []).join(", ") || "Ninguna"
            )}</td>
            <td>${escapeHTML(transaction.message || "Sin observaciones")}</td>
        </tr>
    `).join("");

    resultsContainer.innerHTML = `
        <div class="result-summary">
            <strong>Tasa de conciliación:</strong>
            ${escapeHTML(summary.reconciliation_rate ?? 0)}%
            <span> | </span>
            <strong>Pendientes de revisión:</strong>
            ${escapeHTML(summary.pending_review ?? 0)}
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>ID de transacción</th>
                        <th>Estado</th>
                        <th>Severidad</th>
                        <th>Reglas activadas</th>
                        <th>Observación</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>
    `;
}

// Presenta las alertas y el análisis del agente.
function renderAlerts(analysis) {
    const alerts = analysis.alerts || [];
    const recommendations = analysis.recommendations || [];

    const alertsHTML = alerts.length
        ? alerts.map(alert => `
            <article class="alert-card">
                <div class="alert-heading">
                    <strong>${escapeHTML(alert.transaction_id)}</strong>
                    <span class="severity ${escapeHTML(
                        String(alert.severity || "INFO").toLowerCase()
                    )}">
                        ${escapeHTML(severityLabel(alert.severity))}
                    </span>
                </div>

                <p><strong>Problema:</strong>
                    ${escapeHTML(alert.explanation || "Sin explicación")}
                </p>

                <p><strong>Recomendación:</strong>
                    ${escapeHTML(alert.recommendation || "Requiere revisión")}
                </p>

                <p><strong>Reglas:</strong>
                    ${escapeHTML((alert.rule_codes || []).join(", "))}
                </p>
            </article>
        `).join("")
        : "<p>No se identificaron alertas pendientes.</p>";

    const recommendationsHTML = recommendations.map(item => `
        <article class="recommendation-card">
            <strong>${escapeHTML(item.priority)}</strong>
            <p>${escapeHTML(item.action)}</p>
        </article>
    `).join("");

    alertsContainer.innerHTML = `
        <div class="risk-indicator">
            <strong>Nivel de riesgo:</strong>
            <span class="severity ${escapeHTML(
                String(analysis.risk_level || "LOW").toLowerCase()
            )}">
                ${escapeHTML(analysis.risk_level || "LOW")}
            </span>
        </div>

        <div class="executive-analysis">
            <h4>Análisis ejecutivo</h4>
            <p>${escapeHTML(analysis.executive_analysis || "Sin análisis")}</p>
        </div>

        <h4>Alertas priorizadas (${alerts.length})</h4>
        ${alertsHTML}

        <h4>Recomendaciones del agente</h4>
        ${recommendationsHTML}

        <div class="security-notice">
            <strong>Control de seguridad</strong>
            <p>Aprobación humana requerida:
                ${analysis.human_approval_required ? "SÍ" : "NO"}
            </p>
            <p>Ejecución automática autorizada:
                ${analysis.execution_authorized ? "SÍ" : "NO"}
            </p>
        </div>
    `;
}

// Ejecuta la conciliación mediante el backend.
async function executeReconciliation() {
    reconcileBtn.disabled = true;
    reconcileBtn.textContent = "Procesando conciliación...";

    resultsContainer.innerHTML =
        "<p>Analizando registros financieros...</p>";

    alertsContainer.innerHTML =
        "<p>El agente está evaluando las alertas y los riesgos...</p>";

    try {
        const response = await fetch(`${API_URL}/reconcile`, {
            method: "POST"
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(
                data.error || "No se pudo ejecutar la conciliación."
            );
        }

        const report = data.report;
        const analysis = data.analysis;

        renderSummary(report.summary || {});
        renderResults(report);
        renderAlerts(analysis);

        console.log("FINIA-RECON | Reporte:", report);
        console.log("FINIA-RECON | Análisis IA:", analysis);

    } catch (error) {
        resultsContainer.innerHTML = `
            <p class="error-message">
                Error: ${escapeHTML(error.message)}
            </p>
        `;

        alertsContainer.innerHTML =
            "<p>No fue posible obtener el análisis del agente.</p>";

        console.error("FINIA-RECON:", error);

    } finally {
        reconcileBtn.disabled = false;
        reconcileBtn.textContent = "Ejecutar conciliación";
    }
}

// Comprueba el estado del servidor.
async function checkServer() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();

        const statusElement = document.querySelector(".status");

        if (response.ok && data.status === "ONLINE") {
            statusElement.innerHTML = `
                <span class="status-dot"></span>
                Sistema operativo
            `;
        } else {
            statusElement.textContent = "Servidor no disponible";
        }

    } catch {
        document.querySelector(".status").textContent =
            "Servidor desconectado";
    }
}

reconcileBtn.addEventListener("click", executeReconciliation);

checkServer();