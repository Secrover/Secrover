<p align="center">
    <img src="https://github.com/Huluti/Secrover/blob/main/assets/secrover.png" height="40" alt="Secrover" />
</p>

Secrover is a free and open-source tool that generates security audit reports for your projects.
We believe that security should not be locked behind paywalls or costly SaaS solutions — everyone deserves access to quality security insights and clear, good reporting.

# Secrover

## 🔍 Features

- 🔒 **Security Audits**: Scans your project dependencies and your domains to identify possible vulnerabilities.
- 📊 **Sharable Dashboards**: Generate dashboards you can easily share with clients, teams, or stakeholders — ideal for reporting and collaboration.
- 🧠 **Human-readable Reports**:  Clean, actionable, and easy-to-understand reports — even for non-technical audiences.
- ⚡ **Easy to Use**: Just a simple config file where you list your repositories and your domains to get started quickly.
- 💻 **Cross-platform**: Works seamlessly on Linux, macOS, and Windows.
- 🌟 **Actively Maintained**:  We’re constantly adding new features and improvements to help you stay ahead of threats.

### Audits
- **Vulnerabilities**
  - Dependency check

- **Domains**
  - SSL certificate
  - HSTS header
  - TLS versions

### Supported languages:
- PHP
- JavaScript
- Python

## 🖼️ Screenshot

<a href="https://github.com/Huluti/Secrover/blob/main/assets/screenshot.png">
  <img src="https://github.com/Huluti/Secrover/blob/main/assets/screenshot.png" height="400" alt="Secrover" />
</a>

## 📁 Configuration

Create a new repo with a `config.yaml` file inside where you will list the repositories to scan.

### Example:

```yaml
domains:
  - my-domain.com
repos:
  - url: git@github.com:your-org/your-repo
    description: "Short description of the project"
    branch: "main"

  - url: https://github.com/your-org/another-repo
    description: "Another awesome project"
```

## 🐳 Install with Docker

You can run Secrover easily using Docker without installing any local dependencies.

### 1. Clone the Secrover project

```bash
git clone https://github.com/Huluti/Secrover
cd Secrover
```

### 2. Build the Docker image

```bash
docker build -t secrover .
```

## ▶️ Usage

From your external project directory (the one containing `config.yaml`), run:

```bash
docker run --rm \
  -v "$(pwd)/config.yaml:/app/config.yaml" \
  -v "$(pwd)/output:/output" \
  -e CONFIG_FILE=config.yaml \
  secrover
```

This will:

* Read the list of repositories from your `config.yaml`
* Clone and analyze them
* Generate a full **HTML security report** into the `output/` folder

## 📄 License

Secrover is released under the **GNU General Public License v3.0 (GPL-3.0)**.

👉 [Read the full license here](https://www.gnu.org/licenses/gpl-3.0.en.html)
