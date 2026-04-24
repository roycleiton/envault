# envault

> A CLI tool to securely manage and sync environment variables across local and remote environments.

---

## Installation

```bash
pip install envault
```

Or with pipx for isolated installs:

```bash
pipx install envault
```

---

## Usage

Initialize a new vault in your project directory:

```bash
envault init
```

Add and retrieve environment variables:

```bash
# Add a variable
envault set DATABASE_URL "postgres://user:pass@localhost/db"

# Get a variable
envault get DATABASE_URL

# List all variables
envault list
```

Sync variables to a remote environment:

```bash
envault push --env production
envault pull --env staging
```

Export variables to a `.env` file:

```bash
envault export > .env
```

---

## Configuration

Envault stores encrypted variables in a local `.envault` file. Remote sync requires a configured backend (S3, Vault, or envault cloud). Run `envault config --help` for setup options.

---

## License

This project is licensed under the [MIT License](LICENSE).