# FINIA-RECON — instrucciones de desarrollo

## Objetivo
Construir una plataforma de conciliación financiera con dos fuentes de datos, reglas determinísticas, explicaciones mediante un modelo de IA, gestión de casos e historial.

## Arquitectura actual
- Python 3.10+ y FastAPI para la API REST.
- `app/business_rules.py`: reglas determinísticas RB01–RB08; única fuente de verdad para estados y severidad.
- `app/reconciliation.py`: métricas y coordinación del motor.
- `app/ai_agent.py`: integración con OpenAI Responses API y fallback transparente basado en reglas.
- `app/storage.py`: SQLite para ejecuciones y casos del MVP.
- `static/`: interfaz HTML, CSS y JavaScript.
- `data/`: datos sintéticos de demostración y base local ignorada por Git.

## Reglas de negocio
- RB01: coincidencia.
- RB02: diferencia de monto.
- RB03: transacción faltante.
- RB04: duplicidad.
- RB05: diferencia de fecha.
- RB06: diferencia de estado.
- RB07: ambigüedad.
- RB08: datos inválidos o insuficientes.

## Agente IA
- Consumir únicamente evidencia mínima, necesaria y anonimizada.
- La IA explica y recomienda; nunca determina ni cambia el resultado de las reglas.
- Distinguir hechos comprobados de hipótesis; no inventar causas.
- Nunca aprobar, modificar saldos ni ejecutar operaciones financieras.
- Mantener aprobación humana obligatoria.
- Leer `OPENAI_API_KEY` y `OPENAI_MODEL` desde variables de entorno; nunca incluir secretos en el repositorio.

## Seguridad y privacidad
- Usar datos sintéticos en desarrollo. No enviar PII, números de cuenta, tarjetas ni información confidencial al proveedor de IA.
- Validar archivos, tamaño, formato y campos antes del procesamiento.
- No exponer API keys en frontend, logs ni respuestas HTTP.
- Antes de producción implementar autenticación, autorización, auditoría, cifrado, retención, rate limiting y PostgreSQL administrado.

## Calidad
- Mantener módulos pequeños, tipados y documentados.
- Agregar pruebas para nuevas reglas y endpoints.
- Ejecutar `python -m pytest -q` y `node --check static/app.js` antes de entregar cambios.
