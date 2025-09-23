# Legal Document Processing Pipeline - Implementation Tasks

**Version:** 2.0  
**Target System:** East African Legal OS Foundation Layer  
**Implementation Approach:** Test-Driven Development (TDD) + Spec-Driven Development  
**Purpose:** Phase-by-phase implementation roadmap for legal-pdf-pipeline-spec.md

---

## Implementation Guidelines

### Development Principles
1. **Test-Driven Development (TDD)**: Write tests first, then implement to pass tests
2. **Spec-Driven Development**: Every feature must have corresponding specification requirements
3. **Legal-Grade Quality**: 98%+ accuracy standards with comprehensive validation
4. **Immutable Architecture**: All changes create new versions, never modify existing data
5. **Complete Audit Trail**: Every operation must be fully traceable and legally defensible

### Quality Gates
- **Unit Tests**: 95%+ code coverage for all components
- **Integration Tests**: End-to-end pipeline validation with real legal documents
- **Performance Tests**: Processing speed and accuracy benchmarks
- **Security Tests**: Data protection and access control validation
- **Legal Compliance Tests**: Accuracy thresholds and audit trail verification

### Comprehensive Technology Stack

#### **Core Infrastructure**
- **Containerization**: Docker with multi-stage builds for all services
- **Orchestration**: Kubernetes for production deployment and scaling
- **Service Mesh**: Istio for service-to-service communication and security
- **Load Balancing**: NGINX Ingress Controller with SSL termination

#### **Backend & APIs**
- **Application Framework**: Python 3.12+ with FastAPI for high-performance APIs
- **Data Validation**: Pydantic v2 for type-safe data models and validation
- **Async Processing**: Celery with Redis for background task processing
- **API Gateway**: Kong or Ambassador for API management and rate limiting

#### **Database & Storage**
- **Primary Database**: PostgreSQL 15+ with high availability (master-replica)
- **Vector Database**: PostgreSQL with pgvector extension for embeddings
- **Document Storage**: MinIO (S3-compatible) for PDF files and large documents
- **Cache Layer**: Redis Cluster for session management and caching
- **Search Engine**: Elasticsearch for full-text search and analytics

#### **AI & ML Services**
- **Large Language Models**: Azure AI Foundry (GPT-5 or GPT-5-mini) for quality assurance
- **Document Processing**: Docling v2 for layout analysis and extraction
- **Legal Enhancement**: LangExtract (Gemini-powered) for legal terminology
- **Embeddings**: OpenAI text-embedding-3-large (3072 dimensions)
- **OCR Services**: Azure AI Vision + Tesseract + AWS Textract (fallback chain)

#### **Data Processing & Storage Formats**
- **Primary Storage**: PostgreSQL with JSONB for structured data
- **Document Storage**: MinIO/S3 for original PDFs and processed files
- **Dual Format Output**: JSON (development) + Akoma Ntoso XML (production)
- **Vector Storage**: pgvector with HNSW indexing for similarity search
- **Backup Storage**: Azure Blob Storage for long-term archival

#### **Monitoring & Observability**
- **Application Monitoring**: Prometheus + Grafana for metrics and dashboards
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) for centralized logging
- **Tracing**: Jaeger for distributed tracing and performance analysis
- **Error Tracking**: Sentry for error monitoring and alerting
- **Uptime Monitoring**: StatusPage + PagerDuty for incident response

#### **Security & Compliance**
- **Authentication**: OAuth 2.0 + JWT with Azure Active Directory integration
- **Secrets Management**: Azure Key Vault for secure credential storage
- **Certificate Management**: cert-manager for automated SSL certificate renewal
- **Network Security**: Kubernetes Network Policies + Istio security policies
- **Vulnerability Scanning**: Trivy for container and dependency scanning

#### **CI/CD & Development**
- **Source Control**: Git with GitHub for version control and collaboration
- **CI/CD Pipeline**: GitHub Actions with automated testing and deployment
- **Package Management**: Poetry for Python dependency management
- **Code Quality**: Black, isort, flake8, mypy for code formatting and analysis
- **Testing**: pytest with coverage reporting and performance benchmarks

#### **Development Tools**
- **API Documentation**: OpenAPI/Swagger with automated generation
- **Database Migrations**: Alembic for schema version control
- **Environment Management**: Docker Compose for local development
- **Testing**: pytest, pytest-asyncio, factory-boy, testcontainers
- **Performance Testing**: Locust for load testing and benchmarking

---

## Phase 0: System Architecture & Foundation

### 0.1 Project Structure & Environment Setup
- [x] **0.1.1** Create standardized Python project structure ✅ (completed 2025-09-20)
  - Set up `pyproject.toml` with all dependencies
  - Configure `pytest.ini` for testing standards
  - Set up `pre-commit` hooks for code quality
  - Create environment files (`.env.example`, `.env.test`)
  - **Spec Reference**: Design Principles - Foundation-First
  - **Tests**: Environment validation, dependency resolution
  - **Success Criteria**: Project installs cleanly, all imports work

- [x] **0.1.2** Database foundation ✅ (completed 2025-09-20)
  - Added SQLAlchemy setup (engine, session factory, declarative base)
  - Implemented initial models: `Document`, `DocumentVersion` with immutability-friendly versioning
  - Initialized Alembic and generated base migration
  - Added DB connectivity tests (SQLite) and passed quality gates (pytest, flake8, mypy)
  - Added optional Postgres via Docker Compose and `psycopg` driver; see README for quickstart and migration commands
  - Note: External services (PostgreSQL/pgvector, MinIO, Redis, Elasticsearch) deferred to later phases per spec
  - **Spec Reference**: Terminology & Data Model, Immutability principle
  - **Tests**: Basic schema creation and CRUD roundtrip on SQLite
  - **Success Criteria**: Schema bootstrapped with migrations; local DB ops verified

- [x] **0.1.3** Core data models implementation ✅ (completed 2025-09-20)
  - Added Pydantic schemas (`DocumentIn/Out`, `DocumentVersionIn/Out`, `Citation`, `Grounding`)
  - Implemented versioning service: create document, add version (auto-increment), temporal query (`get_version_as_of`)
  - Enforced immutability on `DocumentVersion` via SQLAlchemy event; updates now raise errors
  - Added tests for version increment, immutability violation, and temporal queries; all quality gates passing
  - **Spec Reference**: Document Type Support, Citation Grounding, Immutability principle
  - **Tests**: Schema validation and versioning behaviors (SQLite)
  - **Success Criteria**: Schemas and versioning operations validated end-to-end

### 0.2 Configuration & Security Framework
- [x] **0.2.1** Configuration management system ✅ (completed 2025-09-20)
  - Implemented environment-based configuration with `pydantic-settings` and nested models
  - Added feature flags (`FLAGS__*`) with `env_nested_delimiter="__"`
  - Enforced configuration validation at startup via `assert_valid()` (fail-fast for invalid prod setups)
  - Added tests for nested flag parsing and invariant checks; all quality gates green
  - Note: Azure Key Vault integration deferred to later security hardening phase
  - **Spec Reference**: Scalability, Legal Awareness
  - **Tests**: Configuration loading and validation
  - **Success Criteria**: Secure, environment-aware configuration

- [x] **0.2.2** Authentication & authorization framework ✅ (completed 2025-09-20)
  - Implemented JWT-based authentication with token issuance (`POST /auth/token`)
  - Added RBAC via dependency (`require_roles`) and protected route (`GET /admin`)
  - Added security headers middleware and in-memory rate limiting for `/auth/token`
  - Extended settings with `JWT_SECRET`, algorithm, expiry; updated `.env.example`
  - Added comprehensive tests: login success/failure, RBAC 403, headers present, rate limit 429
  - Note: Document-level permissions will be implemented when document endpoints are added
  - **Spec Reference**: Legal Professional Standards, Data Protection
  - **Tests**: Auth flows, permission enforcement, security headers
  - **Success Criteria**: Secure access control meeting legal standards

- [x] **0.2.3** Azure AD OAuth 2.0 integration ✅ (completed 2025-09-20)
  - Integrate with Azure AD for OAuth 2.0 flows; maintain JWT issuance for internal services
  - Add login endpoint and token exchange; refresh token handling where applicable
  - **Tests**: OAuth flow success/failure, token validation, RBAC enforcement
  - **Success Criteria**: Azure AD-backed auth working with least-privilege scopes

- [x] **0.2.4** Secrets management via Azure Key Vault ✅ (completed 2025-09-20)
  - Load sensitive settings (JWT secret, AI keys, DB creds) from Key Vault in non-dev envs
  - Ensure secret rotation without restarts where possible
  - **Tests**: Fallback to env for dev, Key Vault retrieval mocked in tests
  - **Success Criteria**: No secrets in code or images; secure retrieval paths validated

- [x] **0.2.5** Fine-grained document-level RBAC ✅ (completed 2025-09-20)
  - Define roles and permissions per document/collection; add policy checks on read/write endpoints
  - **Tests**: Permitted vs denied access, audit entries for denied actions
  - **Success Criteria**: Document access complies with least privilege and auditability

### 0.3 Logging & Monitoring Foundation
- [x] **0.3.1** Comprehensive logging system ✅ (completed 2025-09-20)
  - Implemented structured JSON logging with correlation IDs and per-request timing
  - Added legal-grade audit trail with SHA-256 hash chaining and tamper detection
  - Captured performance metrics and exception logs with full request/user context
  - Added unit tests for log format, request_id propagation, audit chain verification, and tamper detection; all quality gates green (pytest, flake8, mypy)
  - **Spec Reference**: Auditability, Complete provenance chain
  - **Success Criteria**: Legal-grade, verifiable audit integrity with structured observability

- [x] **0.3.2** Health checks and monitoring ✅ (completed 2025-09-20)
  - Added liveness endpoint (`GET /health/live`) with app name, version, env, start time, uptime, and request counter
  - Added readiness endpoint (`GET /health/ready`) with dependency status including DB ping; legacy `/health` and `/readiness` retained
  - Implemented lightweight DB connectivity check via `SELECT 1`
  - Added tests for liveness, readiness, and legacy endpoints; all quality gates green (pytest, flake8, mypy)
  - **Spec Reference**: Scalability, Quality assurance workflows
  - **Success Criteria**: Reliable health signals and dependency monitoring foundation

### 0.4 Containerization & Infrastructure Setup
- [x] **0.4.1** Docker containerization ✅ (completed 2025-09-20)
  - Added multi-stage `Dockerfile` with non-root user and runtime healthcheck
  - Added `.dockerignore` to keep images small and builds fast
  - Extended `docker-compose.yml` with `app` service, healthcheck, depends_on(Postgres), and resource limits
  - Updated `README.md` with Docker build/run commands and health endpoints
  - **Spec Reference**: Production deployment, Scalable infrastructure
  - **Success Criteria**: Reproducible containerized dev environment with health checks

- [x] **0.4.2** Kubernetes deployment manifests ✅ (completed 2025-09-20)
  - Added `k8s/` manifests: Namespace, ConfigMap/Secrets (examples), App Deployment/Service, HPA, ResourceQuota/LimitRange
  - Added Postgres StatefulSet + headless Service and PVC; added MinIO Deployment/Service with PVC
  - Probes wired to `/health/live` and `/health/ready`; resource requests/limits defined
  - Updated `README.md` with `kubectl apply` order and image build/push guidance
  - **Success Criteria**: Cluster-ready manifests enabling scalable deployment

- [x] **0.4.3** Service mesh and networking ✅ (completed 2025-09-20)
  - Added Istio manifests: `Gateway`, `VirtualService`, `DestinationRule` (ISTIO_MUTUAL), `PeerAuthentication` (mTLS STRICT), `AuthorizationPolicy` for ingress
  - Added restrictive `NetworkPolicy` allowing Postgres traffic only from app pods
  - Updated `README.md` with Istio install/apply steps and ingress testing commands
  - **Success Criteria**: Mesh-enabled routing with mTLS and network isolation

---

## Phase 1: Document Upload & Processing Pipeline

### 1.1 Document Upload Service Implementation
- [x] **1.1.1** Secure file upload API with MinIO integration ✅ (completed 2025-09-20)
  - Added `POST /upload` with content-type validation (PDF/DOCX/ODT), size limit, checksum-based keying, and virus-scan placeholder
  - Implemented storage abstraction: `LocalStorage` (default) and optional `MinioStorage`; DI-driven settings ensure testability
  - Extended settings with `MAX_UPLOAD_MB`, `UPLOADS_DIR`, and MinIO config with validation under `FLAGS__ENABLE_MINIO`
  - Added tests: success upload, reject large file, reject unsupported type, empty file; all quality gates green
  - README updated with example upload command
  - **Success Criteria**: Secure, validated upload flow with pluggable storage

- [x] **1.1.2** Metadata collection and validation ✅ (completed 2025-09-20)
  - Implemented `services/metadata.py` with `extract_metadata`, `validate_metadata`, and `is_duplicate(sha256, known_hashes)`
  - Added `POST /metadata/extract` endpoint returning extracted metadata plus validation issues
  - Extraction covers SHA-256 hash, size, MIME/type + extension, title guess, and simple classifier with confidence [0.0–1.0]
  - Validation rules enforce non-empty content, supported types, and reasonable size; duplicate helper flags repeats by hash
  - Added tests for extraction, classifier bounds, validation outcomes, and duplicate detection; all quality gates green (pytest, flake8, mypy)
  - README updated with usage snippet
  - **Success Criteria**: Baseline smart metadata extraction with validation and duplicate detection

- [x] **1.1.3** Processing session management ✅ (completed 2025-09-20)
  - Added `ProcessingSession` model with `status`, `progress`, `eta_seconds`, `checkpoints`, and `last_error`
  - Implemented service (`SessionService`) for create/get/update/complete/fail with safe bounds and timestamp updates
  - Added API: `POST /sessions`, `GET /sessions/{id}`, `PATCH /sessions/{id}`, and SSE stream at `GET /sessions/{id}/events
  - Tests cover create/get/update/complete flows; quality gates green (pytest, flake8, mypy)
  - **Success Criteria**: Sessions can be tracked with progress and live updates

### 1.2 AI-Powered Extraction Pipeline Implementation
- [x] **1.2.1** Document quality validation gates ✅ (completed 2025-09-20)
  - Implemented heuristic `assess_quality` service: score [0..1], issues, OCR suggestion, extractable text ratio, page count estimate
  - Added `POST /quality/validate` endpoint; returns `score`, `issues`, `needs_ocr`, `extractable_text_ratio`, `page_count`, `content_type`, and `size`
  - Tests cover empty rejection, text vs binary PDFs (OCR suggestion), and unsupported type issue flagging; all quality gates green
  - **Success Criteria**: Baseline pre-processing quality assessment with OCR guidance

- [x] **1.2.2** Docling v2 integration ✅ (completed 2025-09-20)
  - Added `DoclingClient` stub service returning layout blocks with confidence based on text ratio
  - Schemas added: `LayoutBox`, `LayoutText`, `LayoutBlock`, `PageLayout`, `DoclingResult` with confidence fields
  - API: `POST /docling/analyze` accepts `UploadFile` and returns structured layout result; empty uploads rejected (400)
  - Tests validate confidence bounds and behavior for text-rich vs binary PDFs; all quality gates green (pytest, flake8, mypy)
  - **Success Criteria**: Pluggable layout analysis interface ready for real Docling integration

- [x] **1.2.3** LangExtract legal enhancement ✅ (completed 2025-09-20)
  - Implemented `LangExtractClient` stub with regex heuristics for:
    - Legal term identification (definitions, entities, amounts, dates, section headings)
    - Cross-reference detection with source spans and target hints
    - Legal concept classification (penalty, tax_rate, amendment, commencement, jurisdiction)
  - Added schemas: `CharSpan`, `LegalTerm`, `CrossReference`, `LegalClassification`, `LangExtractResult`
  - API: `POST /langextract/analyze` accepts file and returns structured result; empty uploads rejected (400)
  - Tests: `tests/test_langextract.py` validate detection, spans, classification categories, and confidence bounds
  - Note: This is a pluggable stub aligned to spec; production integration to Gemini service is a later enhancement
  - **Spec Reference**: Core Processing Tools - LangExtract
  - **Success Criteria (stub)**: Deterministic heuristic extraction with valid spans and confidences; gateway for real model

- [x] **1.2.4** GPT-5/GPT-5-mini quality assurance integration ✅ (completed 2025-09-20)
  - Implemented `QAClient` stub: structure validation, reasoning verification, cross-ref validation, and compliance checks
  - Heuristic model selection between `gpt-5` and `gpt-5-mini` based on input size and text-likeness
  - Schemas added: `QAValidationMetrics`, `QAValidationResult`
  - API: `POST /qa/validate` accepts file and returns QA metrics and overall confidence; empty uploads rejected (400)
  - Tests: `tests/test_qa.py` cover empty input, metrics presence, confidence bounds, and model selection switch
  - Config: Added optional env placeholders in `.env.example`, `.env.compose`, `.env.test` for future real provider integration; added `FLAGS__ENABLE_GPTQA` flag and AI settings in `Settings`
  - **Spec Reference**: Core Processing Tools - GPT-5 family models
  - **Success Criteria (stub)**: Deterministic QA metrics with valid confidences; route ready for real model integration

- [x] **1.2.5** External AI provider clients & resiliency ✅ (completed 2025-09-20)
  - Implement provider client adapters for Docling, LangExtract (Gemini), and GPT QA behind feature flags
  - HTTP clients with timeouts, retries (exponential backoff), jitter; circuit breaker for consecutive failures
  - Typed request/response models; structured error mapping and redaction of sensitive fields
  - Endpoint-level rate limits for AI-backed endpoints
  - **Tests**: Retry/backoff behavior, timeout handling, circuit opening/closing, rate limit responses
  - **Success Criteria**: Resilient external integrations with safe failure modes

- [x] **1.2.6** AI integration configuration & secrets hardening ✅ (completed 2025-09-20)
  - Validate required settings when feature flags enabled (e.g., `FLAGS__ENABLE_GPTQA=true`)
  - Load API keys from environment/Key Vault; redact in logs and error messages
  - Update `.env.example`, `.env.compose`, `.env.test` docs for real integrations
  - **Tests**: Missing/invalid config raises clear errors; no secret leakage in logs
  - **Success Criteria**: Secure, validated configuration for live providers

### 1.3 Enhanced Quality Assurance Implementation
- [x] **1.3.1** Multi-path extraction with fallbacks ✅ (completed 2025-09-20)
  - Added `LegalExtractionOrchestrator` with Docling+LangExtract primary path, OCR fallback simulation, and enhanced legal analysis boost
  - Introduced `CombinedExtractionResult` schema and `/extract/process` endpoint
  - Aggregates final confidence across Docling, LangExtract, and QA; flags fallback paths
  - Tests added for happy-path, empty-file rejection, and low-quality fallback triggering; quality gates green

- [x] **1.3.2** Legal compliance validation ✅ (completed 2025-09-20)
  - Implemented `LegalComplianceValidator` heuristic with `ComplianceChecks` and `ComplianceReport`
  - New endpoint `POST /compliance/validate` returns per-check confidences and overall score
  - Heuristics cover citation accuracy, cross-refs, numbering, amendments, definitions, hierarchy, mandatory sections
  - Tests validate empty rejection and positive detection; quality gates green

- [x] **1.3.3** Human-in-the-loop review system ✅ (completed 2025-09-20)
  - Implemented in-memory `ReviewQueue` and `CriticalReviewOrchestrator` with expert routing and priority logic
  - Endpoints: `POST /review/assess-route`, `GET /review/tasks`, start/complete task actions
  - Routing triggers on confidence thresholds and content flags (constitutional/tax/commercial/definitions/complex refs)
  - Tests verify task creation on low confidence, task listing, progression, and no-task for high confidence

### 1.4 Groundedness & Citation Verification
- [x] **1.4.1** Enhanced groundedness verification ✅ (completed 2025-09-21)
  - Implemented `GroundednessValidator` with character-level alignment, contextual boundary checks, and numeric/date/ref integrity
  - New endpoint `POST /groundedness/verify` returns per-check confidences, failed checks, and overall score
  - Tests validate exact match ≥99.5%, numbers/dates precision, and cross-reference detection; quality gates green

- [x] **1.4.2** Legal-grade citation system ✅ (completed 2025-09-21)
  - Implemented CitationService in src/legal_os/services/citation.py with regex-based extraction for legal citations (sections, acts, cases), 99.5% accuracy validation using difflib similarity, character-level grounding with mock PDF coordinates (TODO: pdfplumber integration), Bluebook-compliant formatting adapted for Kenyan law (e.g., Income Tax Act), and audit trail logging with redaction and structured JSON output.
  - Added POST /api/v1/citations/verify endpoint in src/legal_os/routers/citation.py with Pydantic models, RBAC placeholder, and integration with service; wired into main.py.
  - Created tests/test_citation.py with unit tests for extraction, validation threshold, grounding precision, format compliance, audit logging (using caplog), and integration test for endpoint (with httpx logging suppressed).
  - All quality gates passed: flake8, mypy, pytest (13/13 tests).
  - Post-implementation refinements (2025-09-22):
    - Eliminated tautological validation by comparing extracted citation text to the actual source slice at char_offset to enforce the 99.5% threshold correctly; confidence now tied to similarity.
    - Added clickable pdf_link fragments (page and char range) to endpoint responses to align with “clickable coordinates” requirement.
    - Removed redundant grounding call in the router; grounding remains in the service when pdf_path is provided.
    - Expanded regex coverage for common East African styles (s./ss., Act/Code variants, eKLR/EA/KLR case forms) and improved case formatting to avoid misusing section fields.
    - Re-validated quality gates: flake8 + mypy on src and full pytest suite passing (2025-09-22).

- [x] **1.4.3** Error recovery system ✅ (completed 2025-09-22)
  - Implemented heuristic LegalErrorRecoverySystem with failure analysis for poor scans, complex tables, legal formatting issues, and corrupted PDFs; strategies include enhanced OCR preprocessing, specialized table extraction, legal templates, and PDF repair.
  - Added POST /error-recovery/attempt API to trigger recovery on uploads; returns structured RecoveryReport with applied strategies and confidence delta.
  - Tests cover OCR fallback trigger, table extraction trigger, endpoint behavior (200 and 400), and schema validation; logging noise from httpx suppressed for stable tests.
  - Quality gates: flake8 clean, mypy clean (src), pytest passing.

---

## Phase 2: Dual Storage Architecture Implementation

### 2.1 PostgreSQL JSON Storage System
- [x] **2.1.1** Raw JSON storage implementation with JSONB ✅ (completed 2025-09-22)
  - Implemented `RawJsonStorage` SQLAlchemy model with unique `(document_id, version_id)` and indexes on `overall_confidence` and `created_at` for query performance.
  - Added service `src/legal_os/services/json_storage.py` with `RawJsonStorageService.store/get`, confidence validation in [0,1], and deterministic JSON size calculation (`raw_json_size_kb`).
  - Created tests `tests/test_json_storage.py` covering store/get roundtrip, size ≥ 1KB, and invalid confidence bounds (raises ValueError).
  - Quality gates: flake8 clean, mypy clean (src), pytest passing (2025-09-22).
  - Success Criteria: Complete JSON storage with fast query capabilities via indexes and validated metadata persisted.

- [x] **2.1.2** MinIO document storage integration ✅ (completed 2025-09-22)
  - Storage abstraction enhanced with `MinioStorage` supporting presigned GET URLs and versioned key helpers:
    - `documents/{document_id}/{version_id}/original.pdf`
    - `documents/{document_id}/{version_id}/artifacts/{name}`
  - Settings updated with `minio_url_expires_seconds` and validation in `Settings.assert_valid()` when `FLAGS__ENABLE_MINIO=true`.
  - New API endpoints in `src/legal_os/routers/documents.py` (wired in `main.py`):
    - `GET /api/v1/documents/{document_id}/versions/{version_id}/download` ⇒ presigned URL for original
    - `GET /api/v1/documents/{document_id}/versions/{version_id}/artifacts/{name}` ⇒ presigned URL for artifact
  - Security: private bucket assumed; no public ACLs; secrets redacted from logs; presigned URL expiry configurable.
  - LocalStorage behavior unchanged (returns 404 for presign endpoints as URLs are not available locally).
  - Tests:
    - `tests/test_documents.py`: Local mode presign endpoints return 404 as expected.
    - `tests/test_documents_minio.py`: MinIO enabled via DI + monkeypatch, endpoints return 200 with URL-like strings. Fixed FeatureFlags construction in test to resolve type mismatch.
  - Quality gates: flake8 clean, mypy clean (src), pytest suite updated to cover endpoints.
  - Success Criteria: Functional presigned URL endpoints with secure, versioned keys and configurable expiry.

- [x] **2.1.3** Storage validation and integrity ✅ (completed 2025-09-22)
  - Added `jsonschema` dependency and `storage_integrity` module with:
    - JSON Schema (Draft 2020-12) and `validate_payload(payload)` helper
    - Deterministic SHA-256 checksum `compute_checksum` and `verify_checksum`
    - Version consistency helper `verify_keys_match_version`
    - Simple JSON backup/restore helpers for local archival
  - Extended `RawJsonStorage` model with `content_checksum` column (SHA-256 of stored JSON)
  - Enhanced `RawJsonStorageService.store(...)` to optionally validate schema and persist checksum
  - Tests `tests/test_storage_integrity.py` cover schema validation error path, checksum verification, key/version consistency, and backup/restore roundtrip
  - Quality gates: flake8 clean, mypy clean, full pytest passing
  - Success Criteria: Reliable storage with verified integrity and validation hooks

### 2.2 Akoma Ntoso XML Implementation
- [x] **2.2.1** XML transformation engine (in progress; core implemented 2025-09-22)
  - JSON to Akoma Ntoso XML conversion
  - International legal document standard compliance
  - Semantic structure preservation
  - Metadata mapping and validation
  - Implemented minimal AKN service and API endpoint `POST /api/v1/akn/transform`; XML well-formedness validation via lxml
  - Added tests `tests/test_akn.py` and `tests/test_akn_requests.py` covering success, empty payload, and invalid XML error path
  - **Spec Reference**: Akoma Ntoso XML Storage, Standards Compliance
  - **Tests**: XML validation, standard compliance, transformation accuracy
  - **Success Criteria**: Valid Akoma Ntoso XML with preserved semantics

- [x] **2.2.2** XML query optimization ✅ (completed 2025-09-22)
  - Added `AKNQueryEngine` in `src/legal_os/services/akn_query.py` with namespace-aware XPath evaluation, section lookup by eId, and neighbor navigation
  - New endpoints in `src/legal_os/routers/akn_query.py`:
    - `POST /api/v1/akn/xpath` → run XPath and return stringified results
    - `POST /api/v1/akn/section` → fetch section by `eId` with heading and serialized XML
    - `POST /api/v1/akn/nav` → previous/next navigation for a given `eId`
  - Wired router into app in `src/legal_os/main.py`
  - Tests `tests/test_akn_query.py` cover XPath text results, section lookup, and neighbor navigation; all pass
  - **Spec Reference**: Optimized queries, Semantic queries
  - **Tests**: Query performance, accuracy, semantic capabilities
  - **Success Criteria**: Fast, accurate XML queries with semantic understanding

### 2.3 Storage Synchronization
- [x] **2.3.1** Dual storage consistency ✅ (completed 2025-09-22)
  - Implemented `DualStorageCoordinator` to coordinate atomic-like writes of JSON (DB) and XML (object storage)
  - Extended `Storage` protocol with `delete_object` and `exists` and implemented for Local/MinIO
  - On XML storage failure, DB insert is rolled back by transaction scope; on success, both stores remain consistent
  - Tests `tests/test_dual_storage.py` cover success path and XML failure rollback behavior (transaction-scoped)
  - **Success Criteria**: Consistency across JSONB and XML artifact with rollback on failures

- [x] **2.3.2** Consistency checks and validation ✅ (completed 2025-09-22)
  - Added `ConsistencyChecker` with presence check and naive reconcile (regenerate missing XML)
  - Added endpoints: `POST /api/v1/consistency/check` and `POST /api/v1/consistency/reconcile` (admin-protected)
  - Extended `Storage` with `get_object` for potential deep validation in later steps
  - Tests `tests/test_consistency.py` cover check path and service-level reconcile creating missing XML
  - **Success Criteria**: Detect drifts and restore missing artifacts

- [x] **2.3.3** Conflict resolution and rollback ✅ (completed 2025-09-22)
  - Added pre-existence check for JSON record and idempotent `store_json_and_xml_idempotent` using `ProcessingSession.source_key`
  - Added compensation: attempt to delete partially written XML on failure
  - Ensured idempotent no-op if the same idempotency key is retried after completion
  - Tests `tests/test_dual_storage_idempotent.py` validate idempotency and artifact persistence
  - **Success Criteria**: Idempotent, compensating operations with clear failure states

---

## Phase 3: Document Structure Parser Implementation

### 3.1 Hierarchical Analysis Engine
- [x] **3.1.1** Legal document structure parser ✅ (core implemented 2025-09-22)
  - Implemented StructureParser with regex-based jurisdiction-style heading classification (Part/Chapter/Section/Article) and hierarchical parent inference.
  - Added API endpoints: POST /api/v1/structure/parse/json and POST /api/v1/structure/parse/xml, wired into main app.
  - Confidence scoring based on recognized headings; supports Akoma Ntoso XML parsing of sections.
  - Tests added in tests/test_structure.py validating hierarchy inference, levels, parents, and confidence.
  - Pending: Expanded numbering schemes (Kenya, Uganda, TZ variants), cross-reference mapping, AI-enhanced verification, and performance validation per spec.
  - **Spec Reference**: Legal Document Structure Parser, AI-Enhanced Analysis
  - **Tests**: Structure recognition accuracy, validation performance
  - **Success Criteria**: 98%+ structure parsing accuracy with comprehensive validation

- [x] **3.1.2** Structure validation framework ✅ (core implemented 2025-09-22)
  - Implemented LegalStructureValidator with metrics: pattern_recognition, numbering_consistency, mandatory_sections, amendment_tracking, and overall_score.
  - Endpoints: POST /api/v1/structure/validate/json and /validate/xml; Pydantic output models with metrics and issues.
  - Mandatory section detection supports case-insensitive phrase matching within headings.
  - Tests in tests/test_structure_validation.py covering score bounds, mandatory heading presence, and XML inputs.
  - Pending: Jurisdiction-aware mandatory sets, deeper amendment/change validation, multi-dimensional quality metrics, and AI-assisted scoring.
  - **Spec Reference**: LegalStructureValidator, Structure Validation
  - **Success Criteria**: Comprehensive structure validation with legal compliance

### 3.2 Cross-Reference Resolution
- [x] **3.2.1** Internal reference linking ✅ (core implemented 2025-09-22)
  - Implemented CrossRefResolver with detection for section/sec./s., article/art., regulation/reg., rule/r.; resolves kind+number to eId using parsed structure index.
  - Endpoints: POST /api/v1/structure/crossref/resolve/json and /resolve/xml.
  - Metrics: total_refs, resolved_refs, resolution_rate; issues reported for unresolved refs.
  - Tests: tests/test_crossref_internal.py covering JSON/XML detection and resolution rate.
  - Pending: Subsection-level target resolution, disambiguation heuristics, and cross-block scope rules.
  - **Spec Reference**: Cross-Reference Mapping, Internal links
  - **Success Criteria**: 99%+ internal reference resolution accuracy

- [x] **3.2.2** External reference resolution ✅ (core implemented 2025-09-22)
  - Implemented ExternalRefResolver to extract citations via CitationService and resolve external references (statutes, cases, articles) with authority/jurisdiction inference and canonical URI mapping.
  - Added router src/legal_os/routers/external_ref.py with endpoints: POST /api/v1/structure/external/resolve/json and /resolve/xml; wired into main app.
  - Simple canonical registry for Kenyan statutes (e.g., Income Tax Act) and placeholder canonical URIs for cases.
  - Metrics: total, resolved, resolution_rate; issues include unresolved references.
  - Tests: tests/test_external_ref.py validating JSON and XML flows, detection of case and statute refs, and metrics bounds.
  - Pending: Expand canonical registry, integrate authoritative databases, enhance jurisdiction detection, and improve confidence calibration.
  - **Spec Reference**: External references, Citation network
  - **Success Criteria**: Robust external reference resolution with validation

---

## Phase 4: RAG System & Vector Database Implementation

### 4.1 PostgreSQL Vector Database Implementation (pgvector)
- [x] **4.1.1** Vector embedding pipeline with text-embedding-3-large ✅ (completed 2025-09-23)
  - Implemented `EmbeddingPipeline` with JSON and Akoma Ntoso XML chunkers (skip headings/num), configurable chunk size and overlap, and unit-norm vectors.
  - Added production-grade provider switching at runtime via settings and per-request override header/body. Supported providers:
    - OpenAI (`text-embedding-3-*`)
    - Azure OpenAI (deployment-based embeddings API)
    - Google Gemini (`gemini-embedding-001`)
    - Mistral (`mistral-embed` family)
    - Ollama (handles legacy single-vector and batched shapes)
    - Deterministic stub fallback when external AI is disabled or config is incomplete
  - Real HTTP clients with timeouts and retry/backoff for 429/503; normalized response shapes across providers; robust error messages without leaking secrets.
  - Endpoint validation blocks orchestration/chat models in embedding routes (e.g., GPT-5/mini) and enforces positive dimensions; per-request provider/model allowed.
  - API router `src/legal_os/routers/embeddings.py` exposes:
    - `POST /api/v1/embeddings/json`
    - `POST /api/v1/embeddings/xml`
  - Configuration: Feature flags and provider settings in `Settings`; documented in `.env.example`, `.env.compose`, `.env.test`. Azure API versioning supported; Google SDK optional (`google-genai`).
  - Tests: Embedding dimensionality, unit-norm, XML flow, provider override, and resiliency paths. Project quality gates green (flake8, mypy on src, full pytest). Lint/type configs adjusted to avoid test-only noise.
  - **Spec Reference**: Vector Database Integration, Embedding Generation
  - **Success Criteria**: Provider-agnostic, runtime-switchable, resilient embedding pipeline with clear validation and errors — achieved.

- [ ] **4.1.2** pgvector database optimization
  - PostgreSQL pgvector extension setup with HNSW indexing
  - Efficient vector storage and similarity search optimization
  - Query performance tuning for legal content similarity
  - Vector database maintenance and index optimization
  - **Spec Reference**: pgvector integration, Vector storage performance
  - **Tests**: Search performance, indexing efficiency, maintenance procedures
  - **Success Criteria**: Fast, accurate vector search with legal optimization

### 4.2 Legal RAG Implementation
- [ ] **4.2.1** Legal query analysis and routing
  - Legal-specific query understanding and classification
  - Temporal query handling for current vs. historical law
  - Multi-jurisdiction query routing
  - Query complexity assessment and optimization
  - **Spec Reference**: LegalQueryAnalyzer, Temporal awareness
  - **Tests**: Query classification accuracy, routing effectiveness
  - **Success Criteria**: Intelligent legal query handling with temporal awareness

- [ ] **4.2.2** Hybrid retrieval system
  - Vector similarity search with legal semantic understanding
  - Keyword-based search for precise legal terms
  - Hierarchical search respecting document structure
  - Result ranking with legal relevance scoring
  - **Spec Reference**: LegalRAGRetrieval, Hybrid search
  - **Tests**: Retrieval accuracy, ranking quality, performance
  - **Success Criteria**: Superior legal document retrieval with hybrid approach

- [ ] **4.2.3** Context augmentation engine
  - Legal context enhancement for retrieved content
  - Amendment and supersession awareness in results
  - Cross-reference enrichment
  - Confidence scoring for retrieved content
  - **Spec Reference**: LegalContextAugmenter, Context enhancement
  - **Tests**: Context quality, enrichment accuracy, confidence scoring
  - **Success Criteria**: Rich, legally-aware context for accurate responses

---

## Phase 5: Quality Assurance & Monitoring Implementation

### 5.1 Comprehensive Quality Framework
- [ ] **5.1.1** Legal quality standards enforcement
  - 98%+ overall extraction accuracy monitoring
  - 99.5%+ citation linking precision validation
  - 99%+ groundedness verification enforcement
  - 98%+ legal admissibility score maintenance
  - **Spec Reference**: LegalQualityStandards, Accuracy Requirements
  - **Tests**: Quality threshold enforcement, monitoring accuracy
  - **Success Criteria**: Consistent quality standards meeting legal requirements

- [ ] **5.1.2** Continuous monitoring system
  - Real-time accuracy tracking and alerting
  - Performance trend analysis and reporting
  - Error pattern identification and resolution
  - Quality degradation detection and response
  - **Spec Reference**: AccuracyMonitoringSystem, Continuous monitoring
  - **Tests**: Monitoring accuracy, alert reliability, trend analysis
  - **Success Criteria**: Proactive quality monitoring with rapid issue detection

- [ ] **5.1.3** Prometheus metrics & tracing baseline
  - Expose `/metrics` with Prometheus counters/histograms for critical endpoints (quality, docling, langextract, QA)
  - Add OpenTelemetry tracing spans; export to Jaeger/OTel collector; propagate request IDs
  - **Tests**: Metrics endpoint returns data; basic span creation verified via unit/integration harness
  - **Success Criteria**: Actionable metrics and traces for performance and error analysis

- [ ] **5.1.4** Sentry error tracking integration
  - Initialize Sentry SDK with environment and release tags; scrub PII and secrets
  - Capture unhandled exceptions and attach request correlation IDs
  - **Tests**: Mock transport asserts events emitted on errors
  - **Success Criteria**: Reliable error telemetry without sensitive data leakage

### 5.2 Legal Compliance Framework
- [ ] **5.2.1** Compliance validation system
  - ISO 27001 data security compliance verification
  - SOC 2 Type II processing controls validation
  - GDPR data protection compliance checking
  - Legal professional standards enforcement
  - **Spec Reference**: LegalComplianceFramework, Compliance standards
  - **Tests**: Compliance validation accuracy, standard adherence
  - **Success Criteria**: Full compliance with legal industry standards

- [ ] **5.2.2** Audit system implementation
  - Complete chain of custody documentation
  - Processing integrity verification with tamper detection
  - Expert validation recording and tracking
  - Court admissibility assessment and scoring
  - **Spec Reference**: LegalAuditSystem, Legal defensibility
  - **Tests**: Audit trail completeness, integrity verification
  - **Success Criteria**: Legal-grade audit capability with court readiness

---

## Phase 6: Version Management & Temporal Queries

### 6.1 Immutable Versioning System
- [ ] **6.1.1** Document version management
  - Immutable document versioning with complete history
  - Supersession chain tracking and validation
  - Amendment correlation and impact analysis
  - Version integrity verification
  - **Spec Reference**: Immutable versioning, Supersession chains
  - **Tests**: Version integrity, supersession accuracy, impact tracking
  - **Success Criteria**: Reliable version management with complete legal history

- [ ] **6.1.2** Temporal query engine
  - Point-in-time legal status queries
  - Historical law retrieval and analysis
  - Amendment timeline reconstruction
  - Current law determination with confidence
  - **Spec Reference**: Temporal queries, Time-aware search
  - **Tests**: Temporal accuracy, historical retrieval, current law determination
  - **Success Criteria**: Accurate temporal legal queries with historical awareness

### 6.2 Amendment Tracking
- [ ] **6.2.1** Legal change detection
  - Automated amendment identification and classification
  - Impact analysis for legal changes
  - Dependency tracking for affected documents
  - Change notification and alerting system
  - **Spec Reference**: Amendment tracking, Change tracking
  - **Tests**: Change detection accuracy, impact analysis, notifications
  - **Success Criteria**: Comprehensive legal change tracking with impact awareness

---

## Phase 7: Performance Optimization & Scalability

### 7.1 Performance Optimization
- [ ] **7.1.1** Processing pipeline optimization
  - Parallel processing for multiple documents
  - Memory optimization for large document handling
  - Database query optimization and indexing
  - Caching strategies for frequently accessed content
  - **Spec Reference**: Scalability, Process thousands efficiently
  - **Tests**: Performance benchmarks, memory usage, query speed
  - **Success Criteria**: Efficient processing meeting scalability requirements

- [ ] **7.1.2** API performance optimization
  - Response time optimization for all endpoints
  - Pagination and filtering for large result sets
  - Connection pooling and resource management
  - Load balancing and horizontal scaling preparation
  - **Spec Reference**: Scalable architecture, API performance
  - **Tests**: API response times, throughput, resource usage
  - **Success Criteria**: Fast, scalable API meeting performance targets

### 7.2 Infrastructure Scaling
- [ ] **7.2.1** Database scaling strategy
  - Read replica configuration for query scaling
  - Partitioning strategy for large document collections
  - Backup and disaster recovery procedures
  - Performance monitoring and alerting
  - **Spec Reference**: Scalable database, Large collections
  - **Tests**: Scaling performance, backup/recovery, monitoring
  - **Success Criteria**: Scalable database infrastructure with reliability

---

## Phase 8: Production Deployment & Operations

### 8.1 Production Deployment
- [ ] **8.1.1** Containerization and orchestration
  - Docker containerization with multi-stage builds
  - Kubernetes deployment manifests and configurations
  - Health checks and readiness probes
  - Resource limits and auto-scaling configuration
  - **Spec Reference**: Production deployment, Scalable infrastructure
  - **Tests**: Container functionality, orchestration, scaling
  - **Success Criteria**: Production-ready containerized deployment

- [ ] **8.1.2** CI/CD pipeline implementation
  - Automated testing pipeline with quality gates
  - Security scanning and vulnerability assessment
  - Deployment automation with rollback capability
  - Environment promotion with validation
  - **Spec Reference**: Quality assurance, Production readiness
  - **Tests**: Pipeline reliability, security scanning, deployments
  - **Success Criteria**: Robust CI/CD with automated quality validation

### 8.2 Operations & Maintenance
- [ ] **8.2.1** Monitoring and alerting system
  - Application performance monitoring (APM)
  - Business metrics tracking and alerting
  - Error tracking and incident response
  - Capacity planning and resource monitoring
  - **Spec Reference**: Monitoring system, Performance tracking
  - **Tests**: Monitoring accuracy, alert reliability, incident response
  - **Success Criteria**: Comprehensive operational monitoring with proactive alerting

- [ ] **8.2.2** Backup and disaster recovery
  - Automated backup procedures with verification
  - Disaster recovery testing and procedures
  - Data retention policies and compliance
  - Business continuity planning
  - **Spec Reference**: Data protection, Business continuity
  - **Tests**: Backup integrity, recovery procedures, compliance
  - **Success Criteria**: Reliable backup and recovery meeting legal requirements

---

## Development Conventions & Standards

### Code Quality Standards
- **Python Style**: Black formatting, isort imports, flake8 linting
- **Type Hints**: Full type annotations with mypy validation
- **Documentation**: Comprehensive docstrings with examples
- **Error Handling**: Structured exception handling with logging
- **Security**: Input validation, sanitization, and security headers

### Testing Standards
- **Unit Tests**: 95%+ coverage with meaningful assertions
- **Integration Tests**: End-to-end scenarios with real data
- **Performance Tests**: Benchmarks with acceptable thresholds
- **Security Tests**: Vulnerability scanning and penetration testing
- **Legal Compliance Tests**: Accuracy and audit trail validation

### API Standards
- **OpenAPI Specification**: Complete API documentation
- **RESTful Design**: Consistent resource naming and HTTP methods
- **Error Responses**: Structured error formats with helpful messages
- **Rate Limiting**: Appropriate limits with clear error messages
- **Versioning**: API versioning strategy for backward compatibility

### Database Standards
- **Schema Migrations**: All changes through versioned migrations
- **Data Validation**: Constraints and checks at database level
- **Performance**: Proper indexing and query optimization
- **Security**: Row-level security and access controls
- **Backup**: Regular backups with tested recovery procedures

---

## Success Metrics & Acceptance Criteria

### Technical Metrics
- **Processing Accuracy**: 98%+ overall extraction accuracy
- **Citation Precision**: 99.5%+ citation linking accuracy
- **Groundedness**: 99%+ text-to-source matching accuracy
- **Performance**: <2 minutes processing time for typical legal documents
- **Availability**: 99.9% uptime with <1 second API response times

### Legal Compliance Metrics
- **Audit Trail**: 100% complete provenance tracking
- **Legal Admissibility**: 98%+ court-ready documentation scoring
- **Expert Validation**: <5% requiring human review after optimization
- **Compliance**: 100% adherence to ISO 27001, SOC 2, GDPR standards
- **Security**: Zero data breaches or unauthorized access incidents

### Business Impact Metrics
- **Document Processing Volume**: Support for 10,000+ documents
- **User Adoption**: 95%+ user satisfaction with accuracy and speed
- **Legal Professional Acceptance**: 90%+ expert validation agreement
- **System Reliability**: 99.9% successful processing rate
- **Cost Efficiency**: 80% reduction in manual document processing time

---

## Risk Mitigation & Contingency Plans

### Technical Risks
- **AI Service Unavailability**: Fallback to alternative AI providers
- **Performance Degradation**: Auto-scaling and load balancing
- **Data Corruption**: Immutable storage with verification checksums
- **Security Breaches**: Encryption, access controls, and monitoring

### Legal & Compliance Risks
- **Accuracy Issues**: Human review escalation and expert validation
- **Audit Trail Gaps**: Comprehensive logging with tamper detection
- **Compliance Violations**: Regular audits and compliance monitoring
- **Legal Challenges**: Court-ready documentation and expert testimony

### Operational Risks
- **Team Knowledge Loss**: Comprehensive documentation and training
- **Vendor Dependencies**: Multiple provider options and contracts
- **Scaling Challenges**: Modular architecture and performance testing
- **Budget Overruns**: Phased implementation with cost monitoring

---

## Implementation Timeline

### Phase 0-1 (Foundation & Upload): 8-10 weeks
- System architecture and core infrastructure
- Document upload and processing pipeline
- Basic quality assurance and validation

### Phase 2-3 (Storage & Structure): 6-8 weeks  
- Dual storage implementation
- Document structure parsing and validation
- Cross-reference resolution

### Phase 4 (RAG & Vector): 6-8 weeks
- Vector database and embedding generation
- Legal RAG system implementation
- Query processing and retrieval

### Phase 5-6 (Quality & Versioning): 4-6 weeks
- Quality assurance and monitoring
- Version management and temporal queries
- Legal compliance validation

### Phase 7-8 (Optimization & Deployment): 4-6 weeks
- Performance optimization and scaling
- Production deployment and operations
- Monitoring and maintenance systems

**Total Estimated Timeline: 28-38 weeks (7-9 months)**

---

## Infrastructure Architecture Summary

### **Storage Layer**
- **PostgreSQL 15+** with pgvector for structured data + vector embeddings
- **MinIO (S3-compatible)** for PDF documents and file storage
- **Redis Cluster** for caching, sessions, and Celery task queue
- **Elasticsearch** for full-text search and analytics

### **Application Layer**
- **FastAPI + Python 3.12+** for high-performance APIs
- **Celery + Redis** for asynchronous background processing
- **NGINX** for load balancing and SSL termination

### **AI/ML Services**
- **Azure AI Foundry (GPT-5 or GPT-5-mini)** for quality assurance
- **OpenAI text-embedding-3-large** for vector embeddings
- **Docling v2** for document layout analysis
- **LangExtract** for legal terminology extraction

### **Container & Orchestration**
- **Docker** with multi-stage builds for all services
- **Kubernetes** for production orchestration and scaling
- **Istio** service mesh for security and observability

### **Monitoring & Security**
- **Prometheus + Grafana** for metrics and monitoring
- **ELK Stack** for centralized logging and search
- **Azure Key Vault** for secrets management
- **OAuth 2.0 + JWT** for authentication

This architecture provides:
- **Legal-grade accuracy** with 98%+ processing standards
- **High availability** with redundant storage and auto-scaling
- **Security compliance** with encryption, audit trails, and access controls
- **Performance optimization** with caching, indexing, and vector search
- **Operational excellence** with comprehensive monitoring and logging

---

## Next Steps

1. **Environment Setup**: Begin with Phase 0.1 project structure and environment
2. **Team Assembly**: Assign technical leads for each phase
3. **Stakeholder Alignment**: Review tasks with legal experts and product owners
4. **Risk Assessment**: Detailed analysis of technical and legal risks
5. **Resource Planning**: Allocate development resources and timelines
6. **Quality Assurance**: Establish testing infrastructure and standards

**Priority**: Start with Phase 0 foundational tasks to establish solid architecture before proceeding to complex AI and legal processing components.