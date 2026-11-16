# DevOps Resource Monitor

A lightweight Streamlit dashboard for live resource readings and session history. It is designed for local development and deployment with Docker or Kubernetes.

## Features

- CPU, memory, and root filesystem utilization.
- Available memory and free disk space.
- System platform, logical CPU count, and uptime.
- Interactive Plotly history chart, retained for the active Streamlit session (up to 1,200 samples).
- Manual refresh and automatic refresh at 10, 30, or 60 seconds.
- Graceful “Unavailable” states when a platform cannot provide an individual metric.
- Explicit metric scope labels: CPU usage is system-wide as reported by the OS; memory and `/` filesystem values are those visible to the process and may be affected by container/runtime behavior.

## Technology stack

Python 3.11, Streamlit, psutil, Plotly, and Pandas. Tests use Python's standard `unittest` framework. There is no database, authentication, or external API.

## Architecture

The app samples local OS APIs through psutil. Streamlit stores history in the active browser session, so it resets when the session ends. A Docker image runs the same app as a non-root user. Kubernetes runs two replicas behind a NodePort Service; each replica has its own sessions and history. See [docs/architecture.md](docs/architecture.md).

## Repository structure

```text
app.py                    Streamlit dashboard and metric collection
requirements.txt          Runtime dependencies
Dockerfile                Non-root container build
.dockerignore             Docker build context exclusions
.gitignore                Local and generated-file exclusions
.streamlit/config.toml    Streamlit network configuration
kubernetes/               Namespace, Deployment, and Service manifests
tests/                    Standard-library unit tests
docs/architecture.md      Deployment design
screenshots/              Genuine assignment evidence (initially empty)
PROGRESS.md               Execution record and outstanding verification
```

## Local setup

Requires Python 3.11 and pip.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Open <http://localhost:8501>. Run the unit tests using `python -m unittest discover -s tests -v`.

## Docker build and run

```bash
docker build -t devops-resource-monitor:latest .
docker run -d --name devops-resource-monitor -p 8501:8501 devops-resource-monitor:latest
docker ps
curl --fail http://localhost:8501/_stcore/health
curl --fail http://localhost:8501/
docker logs devops-resource-monitor
```

Open <http://localhost:8501> in a browser. Stop and remove the container with `docker rm -f devops-resource-monitor`.

## Kubernetes deployment

Use a working local cluster (Docker Desktop Kubernetes, Minikube, or Kind) and `kubectl`. Build the image, then load it into the cluster image store. Use the matching command:

```bash
# Docker Desktop: build in the Docker Desktop daemon; no image load is needed.
# Minikube:
minikube image load devops-resource-monitor:latest
# Kind (replace the cluster name if needed):
kind load docker-image devops-resource-monitor:latest
```

Apply manifests in dependency order and wait for readiness:

```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/deployment.yaml -f kubernetes/service.yaml
kubectl -n devops-monitor rollout status deployment/devops-resource-monitor
```

## Kubernetes verification

```bash
kubectl -n devops-monitor get pods -o wide
kubectl -n devops-monitor get deployment devops-resource-monitor
kubectl -n devops-monitor get service devops-resource-monitor-service
kubectl -n devops-monitor get endpoints devops-resource-monitor-service
kubectl -n devops-monitor logs deployment/devops-resource-monitor --all-pods=true
```

Test through a local port-forward:

```bash
kubectl -n devops-monitor port-forward service/devops-resource-monitor-service 8501:8501
# In another terminal:
curl --fail http://localhost:8501/_stcore/health
```

The NodePort is fixed at 30501; access `http://<node-address>:30501` when the cluster network exposes node ports. On Minikube, `minikube service devops-resource-monitor-service -n devops-monitor --url` can provide a reachable address.

## Scaling

Scale to three replicas and back to two:

```bash
kubectl -n devops-monitor scale deployment/devops-resource-monitor --replicas=3
kubectl -n devops-monitor rollout status deployment/devops-resource-monitor
kubectl -n devops-monitor get pods
kubectl -n devops-monitor scale deployment/devops-resource-monitor --replicas=2
kubectl -n devops-monitor rollout status deployment/devops-resource-monitor
```

## Troubleshooting

- **Docker daemon unavailable:** Start Docker Desktop and enable integration for this WSL distribution, then verify `docker version` shows both client and server.
- **ImagePullBackOff:** Ensure the image was loaded into the same cluster selected by the active kube context. The manifests use `IfNotPresent` for local images.
- **Pods not ready:** Inspect `kubectl -n devops-monitor describe pod <pod>` and `kubectl -n devops-monitor logs <pod>`. The probes request `/_stcore/health`.
- **NodePort unreachable:** Check cluster networking/firewall rules; use `kubectl port-forward` to isolate service and application health.
- **Metrics differ from host tools:** Container CPU, memory, and filesystem visibility varies by platform. The dashboard describes the OS/process-visible scope and does not guarantee container-only figures.
- **Missing metric:** The application shows “Unavailable” when psutil cannot read that API.

## Screenshots

Place genuine captures in `screenshots/`. Capture the dashboard in a browser at `http://localhost:8501`, and capture terminal output directly for Docker build, running container, logs, Kubernetes pods, Deployment, Service, and browser/port-forward access. Keep terminal commands and output visible; do not edit or synthesize evidence. The current execution environment lacks working Docker, Kubernetes CLI/cluster, and browser automation, so no runtime screenshots are included yet. See `PROGRESS.md` for exact commands and environment findings.

## Cloud-native concepts demonstrated

Container image construction, non-root execution, health checks, Kubernetes declarative resources, namespaces, Deployments and replica management, resource requests/limits, probes, labels and selectors, ClusterIP/NodePort service routing, image distribution to local clusters, and operational verification with logs and endpoints.
