"""Compatibility entrypoint for local runs.

The active application is the PostgreSQL-backed Flask package under `app/`.
"""

from run import app


if __name__ == "__main__":
    app.run(debug=True)
