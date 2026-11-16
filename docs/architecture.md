# Deployment architecture

The Streamlit application runs as a single Python process and samples operating-system metrics through `psutil`. CPU usage is the system-wide value reported by the operating system. Memory metrics and the root filesystem usage describe what the process can see; container memory accounting depends on the OS and runtime. Readings are held in the active Streamlit session only and are not persisted.

## Local and container flow

```text
Browser ── HTTP :8501 ──> Streamlit process ──> psutil ──> operating system
```

Docker builds from `python:3.11-slim`, installs pinned-major-range dependencies, copies only the application, and runs as UID/GID 10001. Docker publishes the app at `localhost:8501`. Its health check requests Streamlit's built-in `/_stcore/health` endpoint.

## Kubernetes flow

```text
Browser / kubectl port-forward
          │
          ▼
NodePort Service :30501 (service port :8501)
          │ label selector app.kubernetes.io/name=devops-resource-monitor
          ▼
Deployment (2 replicas; scalable)
          │
          ▼
Pods :8501 ──> Streamlit ──> psutil / pod-visible operating system metrics
```

The resources are isolated in namespace `devops-monitor`. The Deployment sets resource requests and limits, a non-root pod security context, dropped Linux capabilities, and startup, readiness, and liveness HTTP probes. `IfNotPresent` allows a locally loaded image to run without a registry. Load the image into the selected local cluster's image store before applying the Deployment.

## Limitations

Each pod has independent in-memory session history. The application does not aggregate readings across pods. Operating-system metrics may describe the node rather than the container, especially CPU utilization; the dashboard labels that behavior and does not claim container-level readings.
