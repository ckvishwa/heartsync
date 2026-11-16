// STUB, filled in Phase 2b (signed OTA).
// Plan: list `releases/{version}` records, show which devices run which
// version, and publish a release from a signed manifest. Publishing goes
// through a Cloud Function that re-verifies the signature.
export default function ReleasesPage() {
  return (
    <>
      <h1>Releases</h1>
      <div className="panel">
        <p>No releases yet.</p>
        <p className="muted">
          Signed firmware releases are managed here from Phase 2b. Until then, firmware is flashed
          over USB.
        </p>
      </div>
    </>
  );
}
