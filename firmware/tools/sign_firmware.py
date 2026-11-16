#!/usr/bin/env python3
"""Sign and verify heartsync firmware releases (ECDSA P-256 over SHA-256).

See docs/adr/0005-ota-dual-slot-signed.md.

  keygen  --out-dir DIR                      create private.pem and public.pem
  sign    --key private.pem --version X.Y.Z [--env ENV] firmware.bin
  verify  --pubkey public.pem RELEASE_DIR

`sign` writes firmware/release/<version>/ containing firmware.bin,
firmware.bin.sig (DER signature) and manifest.json.

Keep the private key OUTSIDE the repository. Never print or commit it.
Requires: pip install cryptography
"""
import argparse
import base64
import hashlib
import json
import shutil
import sys
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

ALG = "ecdsa-p256-sha256"
DEFAULT_RELEASE_ROOT = Path(__file__).resolve().parent.parent / "release"


def cmd_keygen(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    private_path = out_dir / "private.pem"
    public_path = out_dir / "public.pem"
    if private_path.exists():
        print(f"refusing to overwrite {private_path}", file=sys.stderr)
        return 1
    key = ec.generate_private_key(ec.SECP256R1())
    private_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    print(f"wrote {private_path} (keep secret, outside the repo)")
    print(f"wrote {public_path} (embed in firmware in Phase 2b)")
    return 0


def cmd_sign(args: argparse.Namespace) -> int:
    binary_path = Path(args.binary)
    data = binary_path.read_bytes()
    key = serialization.load_pem_private_key(Path(args.key).read_bytes(), password=None)
    if not isinstance(key, ec.EllipticCurvePrivateKey) or key.curve.name != "secp256r1":
        print("key must be an ECDSA P-256 private key", file=sys.stderr)
        return 1
    signature = key.sign(data, ec.ECDSA(hashes.SHA256()))

    out_dir = Path(args.out_root) / args.version
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(binary_path, out_dir / "firmware.bin")
    (out_dir / "firmware.bin.sig").write_bytes(signature)
    manifest = {
        "version": args.version,
        "env": args.env,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "signature": base64.b64encode(signature).decode("ascii"),
        "alg": ALG,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"signed {binary_path.name} v{args.version} ({len(data)} bytes) -> {out_dir}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    release_dir = Path(args.release_dir)
    manifest = json.loads((release_dir / "manifest.json").read_text())
    data = (release_dir / "firmware.bin").read_bytes()
    public_key = serialization.load_pem_public_key(Path(args.pubkey).read_bytes())

    if manifest.get("alg") != ALG:
        print(f"FAIL: unexpected alg {manifest.get('alg')!r}", file=sys.stderr)
        return 1
    if manifest.get("size") != len(data):
        print("FAIL: size mismatch", file=sys.stderr)
        return 1
    if manifest.get("sha256") != hashlib.sha256(data).hexdigest():
        print("FAIL: sha256 mismatch", file=sys.stderr)
        return 1
    try:
        public_key.verify(
            base64.b64decode(manifest["signature"]), data, ec.ECDSA(hashes.SHA256())
        )
    except InvalidSignature:
        print("FAIL: bad signature", file=sys.stderr)
        return 1
    print(f"OK: v{manifest['version']} signature valid")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("keygen", help="create a signing key pair")
    p.add_argument("--out-dir", required=True)
    p.set_defaults(func=cmd_keygen)

    p = sub.add_parser("sign", help="sign a firmware binary")
    p.add_argument("--key", required=True, help="path to private.pem")
    p.add_argument("--version", required=True)
    p.add_argument("--env", default="esp32-s3-devkitc-1")
    p.add_argument("--out-root", default=str(DEFAULT_RELEASE_ROOT))
    p.add_argument("binary")
    p.set_defaults(func=cmd_sign)

    p = sub.add_parser("verify", help="verify a release directory")
    p.add_argument("--pubkey", required=True, help="path to public.pem")
    p.add_argument("release_dir")
    p.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
