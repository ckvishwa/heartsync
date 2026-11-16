// heartsync Cloud Functions entry point. One file per area; export from here.
import { initializeApp } from "firebase-admin/app";
import { setGlobalOptions } from "firebase-functions/v2";

initializeApp();
setGlobalOptions({ region: "us-central1", maxInstances: 5 });

export * from "./events";
export * from "./pairing";
export * from "./notifications";
export * from "./ota";
