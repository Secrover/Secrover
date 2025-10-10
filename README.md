<p align="center">
    <img src="https://github.com/Secrover/Secrover/blob/main/assets/secrover.png" height="40" alt="Secrover" />
</p>

Secrover is a free and open-source tool that generates clear, professional security audit reports — without paywalls or proprietary SaaS. Just useful insights you can trust and share.

# Secrover

![GitHub last commit](https://img.shields.io/github/last-commit/secrover/secrover)
![Docker Pulls](https://img.shields.io/docker/pulls/secrover/secrover)
![Docker Stars](https://img.shields.io/docker/stars/secrover/secrover)

## 🔍 Features

- 🔒 **Security Audits**: Scans your project dependencies and your domains to identify possible vulnerabilities.
- 📊 **Sharable Dashboards**: Generate dashboards you can easily share with clients, teams, or stakeholders — ideal for reporting and collaboration.
- 🧠 **Human-readable Reports**:  Clean, actionable, and easy-to-understand reports — even for non-technical audiences.
- ⚡ **Easy to Use**: Just a simple config file where you list your repositories and your domains to get started quickly.
- 💻 **Cross-platform**: Works seamlessly on Linux, macOS, and Windows.
- 🌟 **Actively Maintained**:  We’re constantly adding new features and improvements to help you stay ahead of threats.

### Audits

| Category        | Checks                                                 | Supported languages        |
| --------------- | ------------------------------------------------------ | -------------------------- |
| Dependencies | Vulnerability check                                    |  All languages supported by osv-scanner |
| Code         | Static check                                           | All languages supported by opengrep |
| Domains      | SSL certificate, HTTP→HTTPS Redirect, HSTS header, TLS versions, Open Ports, Security Headers | -     |

## Screenshots

| Dependencies Audit | Code Audit | Domains Audit |
| --- | --- | --- |
| <a href="https://github.com/Secrover/Secrover/blob/main/assets/dependencies.png"> <img src="https://github.com/Secrover/Secrover/blob/main/assets/dependencies.png" height="200" alt="Dependencies Audit" /> </a> | <a href="https://github.com/Secrover/Secrover/blob/main/assets/code.png"> <img src="https://github.com/Secrover/Secrover/blob/main/assets/code.png" height="200" alt="Code Audit" /> </a> | <a href="https://github.com/Secrover/Secrover/blob/main/assets/domains.png"> <img src="https://github.com/Secrover/Secrover/blob/main/assets/domains.png" height="200" alt="Domains Audit" /> </a> |

## Demo

You can see Secrover in action right now:

- 📂 Example GitHub repository: [secrover-demo](https://github.com/secrover/secrover-demo)  
- 📊 Live generated report: [demo.secrover.org](https://demo.secrover.org)

### How the demo works

The demo repository uses **GitHub Actions** to automatically:

1. Pull the latest version of Secrover (via Docker).
2. Run security scans on Secrover repositories and domains.
3. Generate an **HTML security report**.
4. Deploy the report to **GitHub Pages**, making it publicly accessible.

This setup makes it easy to run Secrover on a schedule (e.g. daily or weekly), so your reports are always up-to-date and shareable with your team or community.

➡️ You can copy the workflow from the [demo repository’s `.github/workflows/secrover.yml`](https://github.com/secrover/secrover-demo/blob/main/.github/workflows/secrover.yml) to get started quickly.

## Getting Started

Secrover is designed to be simple: configure what you want to scan, then run it with Docker.  
Within minutes, you’ll have a professional **HTML security report** you can share.

Create a new folder/repo with a `config.yaml` file inside where you will list your repositories and domains to scan.

### Example:

```yaml
project:
  name: My project
domains:
  - my-domain.com
  - subdomain.my-domain.com
repos:
  - url: https://github.com/your-org/your-repo
    description: "Short description of the project"
    branch: "main"

  - url: https://github.com/your-org/another-repo
    description: "Another awesome project"
```

#### Accessing Private Repositories

Secrover supports cloning **private repositories via HTTPS** using a **GitHub Personal Access Token (PAT)**.

> We currently support **HTTPS only** (SSH is not yet supported).

##### 1. Create a GitHub Personal Access Token

* Go to [your GitHub account](https://github.com/settings/tokens)
* Click **"Generate new token"** (fine-grained)
* Give it a name like `Secrover`
* Choose "Only select repositories" and select the private repos Secrover needs to clone
  * Under **Repository permissions**, grant:
    * **Contents: Read-only**
* Generate and **copy** the token

##### 2. Create a `.env` file

In the same directory as your `config.yaml`, create a `.env` file:

```env
GITHUB_TOKEN=yourgeneratedtokenhere
```

> **⚠️ Do not share this file or commit it to version control.**
> Add `.env` to your `.gitignore` file to prevent accidental leaks.

## Install & run with Docker

You can run Secrover easily using Docker without installing any local dependencies.

### ▶️ One-Time Scan (on-demand)

From the folder where your `config.yaml` (and optionally `.env`) lives, run:

```bash
docker run -it --rm \
  --env-file .env \
  -v "$(pwd)/config.yaml:/app/config.yaml" \
  -v "$(pwd)/output:/output" \
  secrover/secrover
```

> 💡 If you’re only scanning public repositories or do not need to change default settings, the `--env-file .env` flag is optional.

**What happens:**

* Secrover read the list of repositories and domains from your `config.yaml`
* It clones repositories, scan them, as well as your domains
* It generates a full **HTML security report** into the `output/` folder

### ⏰ Automated Scans (Cron Mode)

Secrover also supports **automatic recurring scans** using an internal cron scheduler (via [Supercronic](https://github.com/aptible/supercronic)).

You can schedule scans to run periodically **inside the container** — ideal for servers, NAS setups, ...

### Example: Run every day at midnight

```bash
docker run -it --rm \
  -v "$(pwd)/config.yaml:/app/config.yaml" \
  -v "$(pwd)/output:/output" \
  -e CRON_SCHEDULE="0 0 * * *" \
  secrover/secrover
```

**What happens:**

* Secrover starts Supercronic in the background
* It executes a new scan based on the chosen schedule
* By default, results are written to `/output` and logs to `/output/secrover.log`

## Environment Variables Reference

| Variable        | Required                   | Default       | Description                                                                                             |
| --------------- | -------------------------- | ------------- | ------------------------------------------------------------------------------------------------------- |
| `GITHUB_TOKEN`  | ❌                          | `-`           | Used to clone private GitHub repositories over HTTPS.                                                   |
| `CONFIG_FILE`   | ✅                          | `config.yaml` | Path to your YAML configuration inside the container.                                                   |
| `OUTPUT_DIR`    | ✅                          | `/output`     | Directory where reports and logs are saved.                                                             |
| `CRON_SCHEDULE` | ❌                          | `-`           | Optional [cron expression](https://crontab.guru/) to schedule recurring scans                           |

All variables can be defined in your `.env` file **or** passed directly using `-e` flags when running the container.
For example:

```bash
-e CONFIG_FILE=config.yaml -e OUTPUT_DIR=/output
```

is equivalent to having them set in your `.env` file.

## Thanks and Acknowledgments

This project benefits from the fantastic work of several open-source projects:

- [Python](https://github.com/python)
- [uv](https://github.com/astral-sh/uv)
- [opengrep](https://github.com/opengrep/opengrep)
- [osv-scanner](https://github.com/google/osv-scanner)

A big thanks to all the maintainers and contributors behind these amazing projects, without whom this project wouldn't be possible!

## License

Secrover is released under the **GNU General Public License v3.0 (GPL-3.0)**.

👉 [Read the full license here](https://www.gnu.org/licenses/gpl-3.0.en.html)

## Stargazers over time
[![Stargazers over time](https://starchart.cc/Secrover/Secrover.svg?variant=adaptive)](https://starchart.cc/Secrover/Secrover)
