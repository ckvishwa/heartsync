# cloud

Firebase: Firestore and Storage rules, Cloud Functions (TypeScript), emulator tooling.
The CLI is a local devDependency: use `npx firebase ...` or the npm scripts.

## Commands (run in `cloud/`)

- `npm install && npm --prefix functions install`: first-time setup.
- `npm run emulators`: build functions, then `firebase emulators:start`
  (Auth 9099, Firestore 8080, Functions 5001, Storage 9199, UI 4000).
- `npm run seed`: load `emulator/seed.json` into the running emulators.
- `npm test`: build, start emulators, run `test/*.test.mjs` (rules and `sendHeart`).

## Conventions

- **Rules first.** For any new collection or field: update `docs/protocol.md`, write the
  rule, write an allow test and a deny test, then write the code that uses it.
- **Deny by default.** No wildcard allows. Every match block is explicit.
- Membership (`couples/{id}.members`, `users/{uid}.coupleId`) is written only by
  Functions or seed scripts. Clients can never set it.
- Functions derive the couple from server data, check `request.auth`, and validate input.
- One file per area in `functions/src/`, exported from `index.ts`. Use v2 APIs.
- Project id `demo-heartsync` keeps the emulators offline. Do not change it until
  the real project exists.

## Gotchas

- The Functions emulator runs compiled JS from `functions/lib/`. Run `npm run build`
  (or `npm --prefix functions run watch`) after editing TypeScript.
- Rules are OR-ed across overlapping `match` blocks. A broad match can undo a strict one
  (see `private/{docId}` vs `private/cycle`).
- `storage.rules` reads Firestore (`firestore.get`), so Storage tests need both emulators.
- Cycle data is health data: never log it, never put it in a notification or an index.
- **Deploy only through CI** (`.github/workflows/cloud.yml`). Never run
  `firebase deploy` from a laptop.
- `emulator/seed.mjs` forces emulator hosts; it cannot touch a real project.
