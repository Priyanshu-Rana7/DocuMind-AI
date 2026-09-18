# DocuMind AI

DocuMind AI is a modular document-intelligence MVP for extracting structured data from invoices. It combines OCR, an LLM provider, validation, persistence, and a React review interface.

## Current scope

The current production workflow supports:

- PDF, PNG, JPG, and JPEG invoice uploads
- OCR text extraction through EasyOCR
- Structured invoice extraction through OpenRouter
- Explicit mock providers for deterministic development and tests
- Confidence scores and arithmetic validation warnings
- User corrections to extracted fields
- Retry and recovery for failed processing
- Invoice history with server-side search and status filters
- CSV, Excel, and JSON export
- Permanent deletion of an invoice and its stored source file
- Health and configuration visibility in the Settings page

Future document types can be added through the `BaseDocumentProcessor` interface without changing the shared upload, OCR, persistence, or API orchestration.

## Architecture

```text
React + TypeScript frontend
          |
       REST API
          |
       FastAPI
          |
    InvoiceService
     /    |     \
 Storage  OCR   Document processor
    |      |          |
 Local   EasyOCR   LLM provider
 storage             |
          Repository + SQLAlchemy
                    |
             SQLite or PostgreSQL
```

The backend uses dependency injection and provider abstractions for storage, OCR, LLM, and document processors. Alembic is the schema migration authority.

## Requirements

### Local development

- Python 3.12 or newer
- Node.js 22 or newer
- npm
- Poppler for PDF OCR
- An OpenRouter API key for real extraction

EasyOCR may download model files the first time it starts. The local launcher expects a backend virtual environment at `backend/venv`.

### Docker deployment

- Docker Desktop with Docker Compose
- A configured `.env` file

Docker is optional for local development, but it runs the production-style PostgreSQL, FastAPI, and Nginx stack.

## Configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

For local development, configure at least:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=google/gemini-2.5-flash
POPPLER_PATH=C:\path\to\poppler\Library\bin
```

Use explicit mock mode only for deterministic local tests:

```env
LLM_PROVIDER=mock
OCR_PROVIDER=mock
```

When `LLM_PROVIDER=openrouter` is selected without an API key, the backend returns a configuration error. It does not silently fabricate invoice data.

Never commit `.env`, API keys, database passwords, or other secrets.

## Run locally on Windows

From the project root:

```powershell
.\start-documind.bat
```

The launcher:

1. Applies Alembic migrations.
2. Starts FastAPI on `http://localhost:8000`.
3. Starts Vite on `http://localhost:5173`.
4. Opens the frontend in the browser.

To run the services manually:

```powershell
Set-Location backend
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
Set-Location frontend
npm install
npm run dev
```

Useful local URLs:

- Frontend: `http://localhost:5173`
- API health: `http://localhost:8000/api/v1/health`
- API documentation: `http://localhost:8000/docs`

## Run with Docker Compose

Create `.env`, then validate and start the stack:

```powershell
docker compose config
docker compose up --build
```

The application is served at `http://localhost` by Nginx. Compose starts:

- PostgreSQL 16 with a persistent database volume
- FastAPI with Alembic migrations
- React static assets through Nginx
- `/api` reverse proxy from Nginx to FastAPI
- Persistent upload storage volume

Useful commands:

```powershell
docker compose ps
docker compose logs backend
docker compose logs frontend
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to delete the database and uploaded-file volumes.

## Free showcase deployment

The recommended low-traffic showcase setup is:

```text
Vercel        -> React frontend
Render        -> FastAPI Docker web service
Neon/Supabase -> PostgreSQL
OpenRouter    -> LLM extraction
```

The repository includes [render.yaml](./render.yaml) as a starting point for a Render Docker service. In Render, set:

- `DATABASE_URL` to the managed PostgreSQL connection string.
- `OPENROUTER_API_KEY` to the backend-only OpenRouter key.
- `CORS_ORIGINS` to a JSON array containing the Vercel deployment origin.
- `OCR_PROVIDER=easyocr`.
- `WEB_CONCURRENCY=1` for the free instance.

For Vercel:

1. Set the project root directory to `frontend`.
2. Use `npm run build` with output directory `dist`.
3. Set `VITE_API_BASE_URL` to the Render backend origin followed by `/api/v1`, for example `https://documind-api.onrender.com/api/v1`.

Do not expose `OPENROUTER_API_KEY` or database credentials in Vercel variables or `VITE_*` variables.

The default Render filesystem is ephemeral. The current MVP uses local storage, so a free showcase deployment may lose uploaded source files after a restart or redeploy. Treat storage as demo-grade until an S3-compatible storage provider is configured.

Free Render instances can sleep and EasyOCR can take time to initialize. The first request after inactivity may be slow.

### Showcase guardrails

The backend includes lightweight single-instance protections:

- Upload and processing requests are rate-limited per client IP.
- Processing requests have a stricter limit to protect OpenRouter usage.
- OCR/LLM processing is concurrency-capped for low-memory instances.
- PDFs are capped at five pages.
- Upload size is bounded by `MAX_UPLOAD_SIZE_MB`.

These limits are intended for a low-volume showcase. They are not a distributed rate limiter and should be replaced with provider-level rate limiting before public or multi-instance use.

## API workflow

### Upload

```http
POST /api/v1/invoices/upload
```

Uploads and stores an invoice without extraction.

### Process immediately

```http
POST /api/v1/invoices/process
```

Uploads, runs OCR, extracts structured data, validates arithmetic, and returns the invoice.

### Extract an uploaded invoice

```http
POST /api/v1/invoices/{invoice_id}/extract
```

### Retry a failed invoice

```http
POST /api/v1/invoices/{invoice_id}/retry
```

### Correct extracted fields

```http
PUT /api/v1/invoices/{invoice_id}/extracted-data
```

The payload uses the `ExtractedInvoiceData` schema. The backend recomputes validation warnings and preserves the original AI confidence score.

### Search and list

```http
GET /api/v1/invoices?skip=0&limit=20&status=EXTRACTED&search=samsung
```

Search covers filename, OCR text, and serialized extracted metadata before pagination.

### Export

```http
GET /api/v1/invoices/{invoice_id}/export?format=csv
GET /api/v1/invoices/{invoice_id}/export?format=xlsx
```

Only successfully extracted invoices can be exported.

### Delete

```http
DELETE /api/v1/invoices/{invoice_id}
```

Permanently removes the invoice record and its stored source file.

## Testing and verification

Run the backend suite:

```powershell
Set-Location backend
.\venv\Scripts\python.exe -m pytest -q
```

Run frontend tests:

```powershell
Set-Location frontend
npm test
```

Build the frontend:

```powershell
npm run build
```

The backend tests use isolated SQLite fixtures and explicit mock providers, so they do not require an API key or network access. Regression fixtures cover sanitized Samsung and Acme invoice samples.

## Error handling and observability

API errors use a consistent envelope:

```json
{
  "error_code": "LLM_TIMEOUT",
  "message": "The AI provider request timed out.",
  "extra": {},
  "request_id": "..."
}
```

Every request receives or preserves an `X-Request-ID` response header. The same identifier is included in structured logs and error responses.

Transient OCR and LLM extraction failures retry with bounded exponential backoff. Provider configuration errors are surfaced immediately and are not retried.

## Project structure

```text
backend/
  app/
    api/             FastAPI routes and dependencies
    core/            settings, logging, prompts, exceptions
    db/              SQLAlchemy session and metadata
    models/          database models
    repositories/    persistence operations
    schemas/         request and response schemas
    services/
      processors/    document processor interfaces and implementations
      ocr/          OCR providers
      llm/          LLM providers
      storage/      storage providers
    validators/      upload and extraction validation
  alembic/           database migrations
  tests/             API, service, provider, repository, and regression tests

frontend/
  src/
    api/             typed API client
    components/      reusable UI components
    context/         theme and toast providers
    hooks/           React Query hooks
    pages/           upload, viewer, history, settings, and landing pages
    types/           shared frontend types
  tests/             Vitest API-client tests
```

## MVP limitations

- Authentication is prepared but not enabled.
- Local storage is the active storage provider; cloud storage is not implemented.
- Docker Compose execution requires Docker Desktop and has to be validated on the target machine.
- Render's free filesystem is ephemeral; use this deployment only as a showcase unless a durable storage provider is configured.
- OCR readiness checks reflect configuration and provider selection; they are not a full model-load probe.
- Search uses pragmatic JSON text casting suitable for the MVP.
- User corrections replace the stored extracted JSON but do not create an audit-history record.
