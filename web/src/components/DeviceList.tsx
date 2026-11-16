"use client";

import { onAuthStateChanged, signInWithEmailAndPassword, signOut, type User } from "firebase/auth";
import { collection, doc, getDoc, onSnapshot, type Timestamp } from "firebase/firestore";
import { type FormEvent, useEffect, useState } from "react";

import { auth, db, useEmulator } from "@/lib/firebase";

// couples/{coupleId}/devices/{deviceId}, see docs/protocol.md
type Device = {
  id: string;
  owner: string;
  firmwareVersion?: string;
  online?: boolean;
  battery?: number | null;
  lastSeen?: Timestamp | null;
};

type DevicesState =
  | { status: "loading" }
  | { status: "unpaired" }
  | { status: "error"; message: string }
  | { status: "ready"; devices: Device[] };

export function DeviceList() {
  // undefined: auth state not known yet. null: signed out.
  const [user, setUser] = useState<User | null | undefined>(undefined);

  useEffect(() => onAuthStateChanged(auth, setUser), []);

  if (user === undefined) return <p className="muted">Loading...</p>;
  if (user === null) return <SignIn />;
  return <Devices user={user} />;
}

function SignIn() {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError(null);
    try {
      await signInWithEmailAndPassword(
        auth,
        String(form.get("email")),
        String(form.get("password")),
      );
    } catch {
      setError(
        useEmulator
          ? "Could not sign in. Check the email and password, and that the Firebase emulators are running and seeded."
          : "Could not sign in. Check the email and password.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="signin panel" onSubmit={onSubmit}>
      <p className="muted">Sign in to see your devices.</p>
      <input name="email" type="email" placeholder="Email" autoComplete="email" required />
      <input
        name="password"
        type="password"
        placeholder="Password"
        autoComplete="current-password"
        required
      />
      {error && <p className="error">{error}</p>}
      <button className="primary" type="submit" disabled={busy}>
        {busy ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}

function Devices({ user }: { user: User }) {
  const [state, setState] = useState<DevicesState>({ status: "loading" });

  useEffect(() => {
    let unsubscribe = () => {};
    let cancelled = false;

    (async () => {
      const profile = await getDoc(doc(db, "users", user.uid));
      const coupleId: unknown = profile.get("coupleId");
      if (cancelled) return;
      if (typeof coupleId !== "string" || coupleId.length === 0) {
        setState({ status: "unpaired" });
        return;
      }
      unsubscribe = onSnapshot(
        collection(db, "couples", coupleId, "devices"),
        (snapshot) =>
          setState({
            status: "ready",
            devices: snapshot.docs.map((d) => ({ id: d.id, ...d.data() }) as Device),
          }),
        (error) => setState({ status: "error", message: error.message }),
      );
    })().catch((error: Error) => {
      if (!cancelled) setState({ status: "error", message: error.message });
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [user.uid]);

  return (
    <div className="panel">
      <div className="toolbar">
        <span className="muted">Signed in as {user.email}</span>
        <button type="button" onClick={() => signOut(auth)}>
          Sign out
        </button>
      </div>
      {state.status === "loading" && <p className="muted">Loading devices...</p>}
      {state.status === "unpaired" && <p>This account is not paired with a partner yet.</p>}
      {state.status === "error" && <p className="error">Could not load devices: {state.message}</p>}
      {state.status === "ready" && state.devices.length === 0 && <p>No devices registered yet.</p>}
      {state.status === "ready" && state.devices.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Device</th>
              <th>Status</th>
              <th>Owner</th>
              <th>Firmware</th>
              <th>Battery</th>
              <th>Last seen</th>
            </tr>
          </thead>
          <tbody>
            {state.devices.map((device) => (
              <tr key={device.id}>
                <td>{device.id}</td>
                <td>
                  <span className={device.online ? "dot on" : "dot"} />
                  {device.online ? "Online" : "Offline"}
                </td>
                <td>{device.owner === user.uid ? "You" : "Partner"}</td>
                <td>{device.firmwareVersion ?? "unknown"}</td>
                <td>{device.battery == null ? "n/a" : `${device.battery}%`}</td>
                <td>{device.lastSeen ? device.lastSeen.toDate().toLocaleString() : "never"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
