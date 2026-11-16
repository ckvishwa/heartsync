#!/usr/bin/env python3
"""Pre-pair two people and their two devices as one couple, for gifting.

Creates (or reuses) two Firebase Auth users, then writes:
  users/{uid}                          displayName, coupleId
  couples/{coupleId}                   members, createdAt
  couples/{coupleId}/devices/{id}      owner, firmwareVersion, online, battery, lastSeen

Device ids are printed on each board's serial port at boot (hs-xxxxxxxxxxxx).

Emulator (default, safe):
  python tools/seed_couple.py --couple-id us \\
      --person a@example.com:Alice:hs-aabbccddeeff \\
      --person b@example.com:Bob:hs-112233445566

Real project (asks for confirmation; needs GOOGLE_APPLICATION_CREDENTIALS set
to a service-account file that lives OUTSIDE the repo):
  python tools/seed_couple.py --project <project-id> --production ...

New users get a random temporary password, printed once. Change it in the app.

Device custom tokens (so a device can sign in as its owner):
  --mint-tokens writes one custom token per device to tools/.device-tokens/<id>.token
  (git-ignored; tokens are never printed). Load each into its board over serial with
  tools/provision_device.py within one hour (custom tokens expire); the board then
  keeps a refresh token in NVS.

Requires: pip install firebase-admin
"""
import argparse
import os
import secrets
import sys


def parse_person(text: str) -> dict:
    parts = text.split(":")
    if len(parts) != 3 or not all(parts):
        raise argparse.ArgumentTypeError("expected email:DisplayName:device-id")
    email, name, device_id = parts
    if not device_id.startswith("hs-"):
        raise argparse.ArgumentTypeError(f"device id must start with hs-, got {device_id!r}")
    return {"email": email, "name": name, "device_id": device_id}


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-pair a couple and their devices")
    parser.add_argument("--project", default="demo-heartsync")
    parser.add_argument("--couple-id", required=True)
    parser.add_argument("--person", type=parse_person, action="append", required=True,
                        help="email:DisplayName:device-id (give exactly two)")
    parser.add_argument("--firmware-version", default="0.1.0")
    parser.add_argument("--mint-tokens", action="store_true",
                        help="write a custom token per device to --token-dir (never printed)")
    parser.add_argument("--token-dir", default=os.path.join(os.path.dirname(__file__), ".device-tokens"))
    parser.add_argument("--production", action="store_true",
                        help="write to the real project instead of the emulators")
    args = parser.parse_args()

    if len(args.person) != 2:
        parser.error("give --person exactly twice")

    if args.production:
        if args.project.startswith("demo-"):
            parser.error("--production needs a real --project id")
        answer = input(f"Write to the REAL project '{args.project}'? Type the project id to confirm: ")
        if answer != args.project:
            print("Aborted.")
            return 1
    else:
        os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
        os.environ.setdefault("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")

    import firebase_admin
    from firebase_admin import auth, firestore

    firebase_admin.initialize_app(options={"projectId": args.project})
    db = firestore.client()

    members = []
    for person in args.person:
        try:
            user = auth.get_user_by_email(person["email"])
            print(f"user exists: {person['email']} (uid {user.uid})")
        except auth.UserNotFoundError:
            password = secrets.token_urlsafe(12)
            user = auth.create_user(
                email=person["email"], password=password, display_name=person["name"]
            )
            print(f"user created: {person['email']} (uid {user.uid}) temporary password: {password}")
        person["uid"] = user.uid
        members.append(user.uid)

    db.document(f"couples/{args.couple_id}").set(
        {"members": members, "createdAt": firestore.SERVER_TIMESTAMP}
    )
    print(f"couple: {args.couple_id}")

    for person in args.person:
        db.document(f"users/{person['uid']}").set(
            {"displayName": person["name"], "coupleId": args.couple_id}, merge=True
        )
        db.document(f"couples/{args.couple_id}/devices/{person['device_id']}").set(
            {
                "owner": person["uid"],
                "firmwareVersion": args.firmware_version,
                "online": False,
                "battery": None,
                "lastSeen": None,
            }
        )
        print(f"device: {person['device_id']} (owner {person['email']})")

    if args.mint_tokens:
        os.makedirs(args.token_dir, exist_ok=True)
        for person in args.person:
            token = auth.create_custom_token(person["uid"])
            if isinstance(token, bytes):
                token = token.decode("ascii")
            path = os.path.join(args.token_dir, f"{person['device_id']}.token")
            with open(path, "w", encoding="ascii") as f:
                f.write(token)
            print(f"token:  {person['device_id']} -> {path} (expires in 1 hour)")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
