"""Create local settings without putting real secrets in Git."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parent.parent
target = root / ".env"
if target.exists():
    print(".env already exists. No changes made.")
else:
    content = (root / ".env.example").read_text()
    content = content.replace("replace-with-a-random-secret-at-least-32-characters", secrets.token_hex(32))
    content = content.replace("replace-with-a-local-database-password", secrets.token_hex(16))
    target.write_text(content)
    print("Created .env with local secrets.")
