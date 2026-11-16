# Assignment progress

## Completed

- Audited the initially empty workspace and created the application, Docker configuration, Kubernetes manifests, tests, README, and architecture notes.
- Added a Streamlit dashboard using psutil readings, with process-visible metric scope, session history, manual/automatic refresh, Plotly history, and graceful missing-metric display.
- Added Docker configuration using Python 3.11 slim, a matching non-root UID/GID 10001, minimal application copy, and the Streamlit HTTP health endpoint.
- Added namespace, two-replica Deployment, NodePort Service, resource settings, security context, and HTTP probes.
- Added `.gitignore`, `.dockerignore`, and an empty screenshots evidence directory.

## Environment audit and commands

- `pwd`, `ls -la`, `rg --files`: workspace was empty except for environment-provided directories.
- `git status --short --branch`, `git remote -v`: failed because `.git` existed as an empty directory and contained no repository metadata.
- `python3 --version`: Python 3.12.3 (assignment target Python 3.11 is specified in the Docker base image).
- `python3 -m pip show ...`: system Python has no pip module.
- `python3 -c 'import streamlit,psutil,plotly,pandas'`: failed with `ModuleNotFoundError: streamlit`; application dependencies are not installed in the environment.
- `docker version`, `docker context ls`: Docker CLI reports Docker is unavailable in this WSL 2 distro and recommends enabling Docker Desktop WSL integration. No Docker build/run/HTTP/log evidence can be collected here.
- `command -v kubectl minikube kind gh`: none found. No cluster can be queried; no Kubernetes resources were applied.
- `command -v chromium` / `google-chrome`: no browser binary found. No genuine browser screenshots can be captured here.
- `git --version`: Git 2.43.0. No configured user name or email was reported. No `gh` CLI exists, authentication and publication are unavailable.

## Verification status

- `python3 -m unittest discover -s tests -v`: passed, 3 tests (live API-shaped values via mocks, unavailable metric handling, and display formatting).
- `python3 -m py_compile app.py tests/test_app.py`: passed.
- `git init`: attempted but failed because the pre-existing `.git` directory is read-only (`fatal: cannot copy .../.git/description ... Read-only file system`). Git commands therefore cannot report a branch or status, and commits/remotes cannot be created in this environment.
- Python 3.11 application import/dependency installation: pending.
- Docker build, container start, HTTP response, health, and logs: pending Docker Desktop WSL integration.
- Kubernetes YAML/API validation, deployment rollout, service/endpoints, port-forward, logs, and scaling: pending `kubectl` and a running cluster.
- GitHub repository creation/push: pending authenticated `gh` and user-approved visibility. No remote is configured.
- Evidence screenshots: pending runtime access; capture instructions are in README.

## Next steps

1. Enable Docker Desktop integration for this WSL distro; build and run using the README commands, then save unaltered terminal/browser captures under `screenshots/`.
2. Install/configure `kubectl` and start/select Docker Desktop Kubernetes, Minikube, or Kind. Load the image if required, apply manifests, verify readiness/service access, and perform the 3-to-2 replica scale cycle.
3. Run tests in a Python environment with the dependencies installed; validate Kubernetes YAML with the cluster API or a YAML parser.
4. Configure Git identity, review the staged files, and create meaningful commits. Install/authenticate `gh`; ask for confirmation of public visibility before creating a public repository.

## Streamlit frontend MIME incident (2026-11-15)

### Diagnosis

- No Streamlit process is running (`pgrep -af '[s]treamlit run'` returned no process) and `ss -ltnp` showed no listener on port 8501.
- Direct `curl` probes for `/`, `/_stcore/health`, and `/hybridaction/static/js/index.CAj-7vWz.js` all failed to connect (`HTTP 000`; no response Content-Type). Therefore the reported HTML response cannot be reproduced against this checkout's current server state.
- Python available is 3.12.3. There is no project `.venv`, no globally importable Streamlit, and no installed package metadata to inspect. The expected requested frontend bundle consequently cannot be located yet.
- `requirements.txt` currently has `streamlit>=1.37,<2.0`, `psutil>=5.9,<8.0`, `plotly>=5.22,<7.0`, and `pandas>=2.0,<4.0`. The Streamlit minimum supports the app's fragment refresh API; no observed version conflict justifies changing these constraints.
- `.streamlit/config.toml` sets headless mode, `0.0.0.0`, port 8501, and disables usage statistics. It does not set `server.baseUrlPath`, static serving, or proxy options. No Streamlit or proxy environment variables were present.
- No stale/conflicting Streamlit process or listener was found.
- A local `.venv` creation attempt failed because system `ensurepip` is absent (`python3.12-venv` is not installed). External bootstrap/PyPI DNS requests also failed. Installing the missing OS package would modify a global system component, so it was not done.

### Conclusion and status

The MIME incident's root cause is **not established** from this environment: no running Streamlit server is available to determine whether the named path is a missing bundle, stale browser asset reference, or an upstream base-path/proxy fallback. No application or dependency changes were made without that evidence. The unsuccessful partial `.venv` was removed. The three existing unit tests and `py_compile` both passed again. This issue remains pending a usable project virtual environment and server/network access; when available, compare the actual `/` asset references with the installed frontend bundle and inspect the named asset response before applying a targeted fix.
