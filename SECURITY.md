# Security policy

## Reporting issues

- Use **[GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)** for **sensitive** reports (if enabled for this repo), or open a **public Issue** for non-sensitive bugs (e.g. documentation mistakes, non-exploitable script errors).

## Project hygiene

- Do **not** commit secrets (API keys, passwords, private URLs) or personal **`venv/`** artifacts.
- Prefer **`ABLETON_HOME`** and **`M4L_REFERENCE_AMXD`** environment variables over hard-coded paths in forks.

This tooling drives a **local** Ableton instance via documented TCP/OSC ports; treat unknown remote-control surfaces as untrusted.
