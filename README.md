# Azure AI Services (Pulumi)

Pulumi project that provisions a backend Azure AI services footprint for RAG-style workloads:

- Azure OpenAI account and model deployment
- Azure AI Search service
- Storage account and blob container for indexed content
- Log Analytics workspace
- RBAC assignments between the managed identities and service resources

Resources are created in a resource group derived from `rg_prefix`.

---

## Run with Docker

You need [Docker](https://docs.docker.com/get-docker/), a [Pulumi access token](https://www.pulumi.com/docs/pulumi-cloud/access-tokens/) (or `PULUMI_ENV_FILE` with `PULUMI_ACCESS_TOKEN=...`), and this repo’s **`Pulumi.yaml`**, **`Dockerfile`**, and **`requirements.txt`**. Do **not** set `virtualenv: venv` in **`Pulumi.yaml`** — the helper scripts refuse to run if it is set.

**Set the token on the host before** you run **`docker_pulumi_shell.sh`** or **`win_docker_pulumi_shell.bat`**, so the shell script can pass **`PULUMI_ACCESS_TOKEN`** into the container. Replace the placeholder with your real token.

PowerShell:

```powershell
$env:PULUMI_ACCESS_TOKEN = "pul-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Bash (Linux, macOS, WSL):

```bash
export PULUMI_ACCESS_TOKEN=pul-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**`docker_pulumi_shell.sh`** passes **`HOST_UID`** / **`HOST_GID`** from your Linux or macOS user into the container so **`stack_menu.py`** can **`chown`** new **`Pulumi.<stack>.yaml`** files on the bind-mounted repo to you (and set mode **`0644`**). On Windows **cmd**, set `set HOST_UID=...` and `set HOST_GID=...` before **`win_docker_pulumi_shell.bat`** if your stack files end up owned by root, or fix ownership once with **`sudo chown`** on WSL.

**Linux / macOS / WSL** — build the image and open a shell in `/app`:

```bash
cd /path/to/azure-pa-hub-network
chmod +x docker_pulumi_shell.sh    # once
export PULUMI_ACCESS_TOKEN="pul-xxxx"
./docker_pulumi_shell.sh
```

**Examples:** build only — `./docker_pulumi_shell.sh --build-only`. Token in a file — `export PULUMI_ENV_FILE="$HOME/.pulumi-env"` then run the script. All flags — `./docker_pulumi_shell.sh --help`.

The image is tagged **`pulumi/azure-ai-services`**.

**Windows (PowerShell)** — from the repo directory with Docker Desktop running:

```bat
$env:PULUMI_ACCESS_TOKEN = "pul-xxxx"
win_docker_pulumi_shell.bat
```

For WSL, Git, and line endings on Windows drives, see **`Windows-Integration.md`**. To run without Docker: `pip install -r requirements.txt` on the host.

---

## Create a new stack

From the repo root, initialize and select a stack with the Pulumi CLI, then configure `Pulumi.<stack>.yaml`.

Recommended path is `python stack_menu.py`: for `azure-ai-services` it asks only for:

- `azure-native:location`
- `azure-ai-services:rg_prefix`

It also applies `azure:subscriptionId` and `azure:tenantId` from `az account show` when available.

### Menu seeding (this project)

| Project (`Pulumi.yaml` `name`) | `stack_menu.py` checklist / seed |
|--------------------------------|-----------------------------------|
| `azure-ai-services` (this repo) | `Pulumi.sample.yaml` (committed full shape) and `default_vars.yaml` (required/optional key sketch). |

### What `stack_menu.py` does here (this project)

- Keeps this repo on a minimal menu: create stack and backup stack.
- Uses a guided create flow for `location` and `rg_prefix`.
- Writes new stack files from `Pulumi.sample.yaml`.

### Configure the stack

- Recommended: `python stack_menu.py`.
- Manual: copy `Pulumi.sample.yaml` to `Pulumi.<stack>.yaml`, then replace placeholders.

Required keys for deployment:

- `azure:subscriptionId`
- `azure:tenantId`
- `azure-native:location`
- `azure-ai-services:rg_prefix`

Example:

```bash
az login
pulumi stack init prod-eip
pulumi stack select prod-eip
python stack_menu.py
pulumi preview && pulumi up
```

---

## Deploy and destroy

```bash
pulumi preview
pulumi up
pulumi destroy
```

---

## Maintaining versions

When you refresh this project's tooling, update these together so previews and deploys stay consistent:

- `Dockerfile`: bump the `pulumi/pulumi-python` image tag (currently `pulumi/pulumi-python:3.231.0`) to a current release from [Docker Hub - `pulumi/pulumi-python`](https://hub.docker.com/r/pulumi/pulumi-python/tags).
- `requirements.txt`: review pinned `pulumi`, `pulumi-azure-native`, and Azure SDK packages so they remain compatible; then rebuild the image.

If you run Pulumi on the host instead of Docker, keep CLI and `pip install -r requirements.txt` aligned where practical.

---

## Project layout (quick reference)

| Path | Role |
|------|------|
| `__main__.py` | Provisions AI resources and RBAC; reads config from Pulumi stack keys. |
| `stack_menu.py` | Stack checklist plus minimal create/backup workflow for this repo. |
| `Pulumi.sample.yaml` | Full stack template for this repo. |
| `default_vars.yaml` | Required/optional config sketch aligned to `__main__.py`. |

---

## Notes

- Keep stack config keys namespaced (`azure-ai-services:*`) for consistency with other repos.
- Resource names are derived from `rg_prefix` and normalized to lowercase where required by Azure services.

---

## Developed By

Andrew Tamagni (see file headers for history).

---

## AI Assistance Disclosure

Portions of this repository and documentation were developed with assistance from Cursor AI and have been reviewed by humans.