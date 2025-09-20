# Legal OS - Foundation Layer

Minimal scaffold for the Legal Document Processing Pipeline API.

## Quick start

1) Install Poetry (if you don't have it): https://python-poetry.org/

2) Install dependencies:

```bash
poetry install
```

3) Run tests:

```bash
poetry run pytest
```

4) Launch the API locally:

```bash
poetry run uvicorn legal_os.main:app --reload
```

Health check at `http://127.0.0.1:8000/health`.

### Run with Docker

Build and run the app with Postgres using Docker Compose:

```bash
docker compose --env-file .env.compose up -d --build postgres app
```

App will be available at `http://127.0.0.1:8000`.

Health endpoints:

- Liveness: `http://127.0.0.1:8000/health/live`
- Readiness: `http://127.0.0.1:8000/health/ready`
- Legacy: `http://127.0.0.1:8000/health` and `http://127.0.0.1:8000/readiness`

## Postgres with Docker Compose (optional)

Run a local Postgres 16 via Docker Compose:

```bash
docker compose --env-file .env.compose up -d postgres
```

Set your `.env` to point to Postgres (or copy from `.env.compose`):

```bash
cp .env.compose .env
```

Apply database migrations:

```bash
source .venv/bin/activate
alembic upgrade head
```

To generate new migrations after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Kubernetes (optional)

Apply manifests (requires kubectl context pointing to a cluster):

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap-app.yaml
# Review and customize secrets before applying example secrets:
kubectl apply -f k8s/secret-app-example.yaml
kubectl apply -f k8s/secret-postgres-example.yaml
kubectl apply -f k8s/postgres-service.yaml
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/minio-pvc.yaml
kubectl apply -f k8s/minio-deployment.yaml
kubectl apply -f k8s/minio-service.yaml
kubectl apply -f k8s/deployment-app.yaml
kubectl apply -f k8s/service-app.yaml
kubectl apply -f k8s/hpa-app.yaml
kubectl apply -f k8s/resourcequota-limitrange.yaml
```

Build and push your image to a registry accessible by the cluster (example for Docker Hub):

```bash
docker build -t <your-dockerhub-username>/legal-os:latest .
docker push <your-dockerhub-username>/legal-os:latest
# Edit k8s/deployment-app.yaml image: to use that registry path
```

Once deployed, port-forward to test locally:

```bash
kubectl -n legalos port-forward svc/legalos-app 8000:80
curl -s http://127.0.0.1:8000/health/live | jq
```

### Istio service mesh (optional)

Prerequisite: Install Istio and enable the ingress gateway in your cluster.

Apply Istio manifests:

```bash
kubectl apply -f k8s/istio-gateway.yaml
kubectl apply -f k8s/istio-virtualservice.yaml
kubectl apply -f k8s/istio-destinationrule.yaml
kubectl apply -f k8s/istio-peerauthentication.yaml
kubectl apply -f k8s/istio-authorizationpolicy.yaml
kubectl apply -f k8s/networkpolicy-db.yaml
```

Find your ingress IP/host and test:

```bash
kubectl -n istio-system get svc istio-ingressgateway
curl -s http://<INGRESS_IP>/health/live | jq
```

## Dev tools
- Black, isort, flake8, mypy
- pytest with httpx TestClient
- pre-commit hooks: `poetry run pre-commit install`

## Notes
This is Phase 0.1.x scaffolding. DB foundation (SQLAlchemy + Alembic) is included; optional Postgres via Compose.
