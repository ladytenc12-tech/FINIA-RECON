# FINIA-RECON

Plataforma de conciliación financiera que compara dos fuentes, aplica reglas determinísticas de negocio, registra casos y utiliza un modelo de IA para explicar hallazgos y sugerir acciones al operador.

## Arquitectura

- **FastAPI:** API REST y recepción de archivos.
- **Motor de reglas:** RB01–RB08; la lógica determinística es la fuente de verdad.
- **OpenAI Responses API:** explicaciones y recomendaciones contextuales. El modelo no modifica transacciones ni autoriza ajustes.
- **SQLite:** historial de ejecuciones y gestión de casos para el MVP.
- **HTML, CSS y JavaScript:** dashboard TCS-inspired con identidad visual propia.

## Requisitos

- Python 3.10 o superior.
- Una API key de OpenAI para habilitar el análisis generativo (opcional para ejecutar el motor de reglas).

## Instalación local

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux / macOS / Codespaces
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Abre `.env` y configura tu clave:

```env
OPENAI_API_KEY=tu_clave_real
OPENAI_MODEL=gpt-5.5
```

No compartas la clave, no la subas a GitHub y no la escribas directamente en el código. El archivo `.env` está excluido de Git.

Inicia el servidor:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Abre `http://localhost:8000`. La documentación interactiva de la API está en `http://localhost:8000/docs`.

## Uso

1. Entra en **Centro de conciliación**.
2. Carga un archivo para el sistema interno y otro para el procesador, o deja ambos vacíos para utilizar los datos sintéticos de demostración.
3. Los archivos pueden ser JSON (lista de objetos), CSV o Excel.
4. Cada registro debe contener `transaction_id`, `amount`, `date` (`YYYY-MM-DD`) y `status` (`COMPLETED`, `PENDING`, `FAILED` o `CANCELLED`).
5. Ejecuta la conciliación y revisa los KPI, las evidencias, el análisis IA y los casos generados.
6. Actualiza el estado de cada caso desde **Gestión de casos**.

## Endpoints principales

- `GET /api/health`: estado del servicio y configuración de IA.
- `POST /api/reconcile`: procesa los dos archivos multipart; si no se adjuntan, usa datos de demostración.
- `GET /api/latest`: última ejecución guardada.
- `GET /api/cases`: casos registrados; admite `?status=OPEN`.
- `PATCH /api/cases/{case_id}`: cambia estado (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `DISMISSED`).
- `GET /api/history`: historial de ejecuciones.

## Seguridad y limitaciones del MVP

- Utiliza exclusivamente datos sintéticos o datos autorizados y previamente anonimizados. No envíes datos personales, números de cuenta, tarjetas ni información confidencial a un proveedor externo de IA.
- La API key se mantiene en el servidor mediante variable de entorno.
- La IA solo recibe un resumen acotado de hallazgos; las reglas de negocio determinan el estado y la severidad.
- Toda recomendación requiere validación del operador. No hay movimientos de fondos ni ajustes automáticos.
- SQLite es adecuado para desarrollo y demostración. Para producción, añade autenticación, autorización por roles, auditoría inmutable, cifrado, gestión de secretos, límites de carga, controles de retención y una base de datos administrada como PostgreSQL.
- La tasa de conciliación del MVP es `operaciones MATCHED / resultados generados`. Debe revisarse junto con el total de registros de ambas fuentes, especialmente cuando hay duplicados o filas inválidas.

## Pruebas

```bash
python -m pytest -q
```
