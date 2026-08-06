#!/usr/bin/env python3
"""Encrypt the team-only announcements for the Team Hub.

Usage:
    python3 encrypt_internal.py announcements.json "the-team-passcode"

Reads a JSON list of announcement objects ({date, tag, title, body}),
encrypts it with AES-256-GCM using a key derived from the passcode
(PBKDF2-SHA256, 310k iterations), and prints the blob to paste into
index.html as the value of INTERNAL_BLOB.

The plaintext JSON must never be committed to the repository, it is
public. Keep it locally, or just tell Claude the new updates and the
passcode and it will regenerate the blob.
"""
import base64
import json
import os
import sys

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITERATIONS = 310_000


def encrypt(plaintext: bytes, passcode: str) -> dict:
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    key = kdf.derive(passcode.encode())
    ct = AESGCM(key).encrypt(iv, plaintext, None)
    b64 = lambda b: base64.b64encode(b).decode()
    return {"v": 1, "iter": ITERATIONS, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = json.load(open(sys.argv[1]))
    blob = encrypt(json.dumps(data).encode(), sys.argv[2])
    print(json.dumps(blob))


if __name__ == "__main__":
    main()
