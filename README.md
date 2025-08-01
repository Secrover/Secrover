<p align="center">
    <img src="https://github.com/Huluti/Secrover/blob/main/assets/secrover.png" height="40" alt="Secrover" />
</p>

Secrover is a free and open-source tool that generates security audit reports for your projects.
We believe that security should not be locked behind paywalls or costly SaaS solutions — everyone deserves access to quality security insights and clear, good reporting.

# Secrover

![GitHub last commit](https://img.shields.io/github/last-commit/huluti/secrover)
![Docker Pulls](https://img.shields.io/docker/pulls/huluti/secrover)
![Docker Stars](https://img.shields.io/docker/stars/huluti/secrover)


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
| 📦 Dependencies | Vulnerability check                                    | PHP, JavaScript and Python |
| 📝 Code         | Static check                                           | All languages supported by opengrep |
| 🌐 Domains      | SSL certificate, HTTP→HTTPS Redirect, HSTS header, TLS versions, Open Ports, Security Headers | -     |

## 🖼️ Screenshots

| Dependencies Audit | Code Audit | Domains Audit |
| --- | --- | --- |
| <a href="https://github.com/Huluti/Secrover/blob/main/assets/dependencies.png"> <img src="https://github.com/Huluti/Secrover/blob/main/assets/dependencies.png" height="200" alt="Dependencies Audit" /> </a> | <a href="https://github.com/Huluti/Secrover/blob/main/assets/code.png"> <img src="https://github.com/Huluti/Secrover/blob/main/assets/code.png" height="200" alt="Code Audit" /> </a> | <a href="https://github.com/Huluti/Secrover/blob/main/assets/domains.png"> <img src="https://github.com/Huluti/Secrover/blob/main/assets/domains.png" height="200" alt="Domains Audit" /> </a> |

## 📁 Configuration

Create a new folder/repo with a `config.yaml` file inside where you will list your repositories and domains to scan.

### Example:

```yaml
domains:
  - my-domain.com
  - subdomain.my-domain.com
repos:
  - url: git@github.com:your-org/your-repo
    description: "Short description of the project"
    branch: "main"

  - url: https://github.com/your-org/another-repo
    description: "Another awesome project"
```

## 🐳 Install with Docker

You can run Secrover easily using Docker without installing any local dependencies.
From your external project directory (the one containing `config.yaml`), run:

```bash
docker run --rm \
  -v "$(pwd)/config.yaml:/app/config.yaml" \
  -v "$(pwd)/output:/output" \
  -e CONFIG_FILE=config.yaml \
  huluti/secrover
```

This will:

* Read the list of repositories and domains from your `config.yaml`
* Clone repositories, scan them, as well as your domains
* Generate a full **HTML security report** into the `output/` folder

## 🫶 Thanks and Acknowledgments

This project benefits from the fantastic work of several open-source projects:

- Python & pip-audit
- PHP & Composer
- Node.js & npm
- uv
- opengrep

A big thanks to all the maintainers and contributors behind these amazing projects, without whom this project wouldn't be possible!

## 📄 License

Secrover is released under the **GNU General Public License v3.0 (GPL-3.0)**.

👉 [Read the full license here](https://www.gnu.org/licenses/gpl-3.0.en.html)
