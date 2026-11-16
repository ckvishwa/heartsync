# web

Next.js dashboard (TypeScript, App Router): device status, pixel editor, OTA releases.

## Commands (run in `web/`)

- `npm install`: first-time setup.
- `npm run dev`: dev server on http://localhost:3000. Needs the Firebase emulators
  running and seeded (`npm run emulators`, `npm run seed` in `cloud/`) for `/devices`.
- `npm test`: typecheck (`tsc --noEmit`). `npm run build`: production build.

## Routes

`/` overview, `/devices` live device list, `/editor` placeholder pixel grid,
`/releases` stub until Phase 2b.

## Conventions

- App Router: routes are `src/app/<route>/page.tsx`. Pages are server components
  and stay thin; interactive parts are client components in `src/components/`.
- Add `"use client"` only where state, effects, or Firebase are used.
- Import with the `@/` alias (`@/components/...`, `@/lib/...`).
- Firebase: import `auth` and `db` from `src/lib/firebase.ts` only, and only in
  client components. Never call `initializeApp` anywhere else.
- No Admin SDK and no service accounts in this package. Trusted writes go
  through Cloud Functions.

## Env handling

- With no env file the app uses the emulators and project `demo-heartsync`.
- For the real project, copy `env.example` to `.env.local` (git-ignored, and
  off-limits to agents).
- `NEXT_PUBLIC_*` values are shipped to the browser. Firebase web config is fine
  there; secrets are not.

## Gotchas

- The emulator connection is guarded by a global flag because hot reload
  re-evaluates `firebase.ts`.
- Firestore rules apply to the dashboard like any client: it sees only the
  signed-in user's couple.
- The art format must match the app and firmware: define it once in `docs/protocol.md`.
