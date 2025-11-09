"""Convert a plaintext user list into bcrypt hashed secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import bcrypt

DEFAULT_INPUT = Path("secrets/users.txt")
DEFAULT_OUTPUT = Path("secrets/secrets.json")
DEFAULT_ROUNDS = 12


AccessEntry = Tuple[str, str]


def parse_users_file(path: Path) -> Dict[str, AccessEntry]:
    """Parse ``path`` and return a mapping of username -> (password, access)."""

    users: Dict[str, AccessEntry] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise SystemExit(f"Input file not found: {path}") from exc

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = [segment.strip() for segment in stripped.split(":", 2)]
        if len(parts) != 3:
            raise SystemExit(
                f"Invalid line in {path}: '{line}'. Expected format "
                "'username:password:access'."
            )
        username, password, access = parts
        if not username or not password or not access:
            raise SystemExit(
                f"Invalid line in {path}: '{line}'. Username, password, and access required."
            )
        if username in users:
            raise SystemExit(f"Duplicate username '{username}' in {path}.")
        lowered_access = access.lower()
        if lowered_access not in {"rd", "wr"}:
            raise SystemExit(
                f"Invalid access level '{access}' for user '{username}'. Use 'rd' or 'wr'."
            )
        users[username] = (password, lowered_access)
    return users


def hash_password(password: str, rounds: int) -> str:
    salt = bcrypt.gensalt(rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def build_payload(users: Dict[str, AccessEntry], rounds: int) -> Dict[str, Any]:
    return {
        "algorithm": "bcrypt",
        "rounds": rounds,
        "users": {
            username: {"hash": hash_password(password, rounds), "access": access}
            for username, (password, access) in users.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        nargs="?",
        default=str(DEFAULT_INPUT),
        help="Path to the plaintext users file (default: secrets/users.txt)",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=str(DEFAULT_OUTPUT),
        help="Where to write the JSON secrets file (default: secrets/secrets.json)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=DEFAULT_ROUNDS,
        help="Cost factor for bcrypt hashing (default: 12)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    users = parse_users_file(input_path)
    payload = build_payload(users, args.rounds)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(users)} user(s) to {output_path}")


if __name__ == "__main__":
    main()
