#!/usr/bin/env node
/**
 * Optional: one-shot Cursor SDK prompt to run ./run in the repo root.
 * Requires CURSOR_API_KEY and: npm install (in this directory).
 * Any agentic IDE can run ./run directly without this script.
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

async function main() {
  const apiKey = process.env.CURSOR_API_KEY;
  if (apiKey) {
    try {
      const { Agent } = await import("@cursor/sdk");
      const result = await Agent.prompt(
        "From the repository root, run ./run (or run.ps1 on Windows). " +
          "Ableton should be quit first. Report M4L_RUN_OK or errors.",
        {
          apiKey,
          local: { cwd: root },
        },
      );
      console.log(result.status, result.result ?? "");
      return;
    } catch (e) {
      console.warn("Cursor SDK unavailable, falling back to shell:", e.message);
    }
  }

  const isWin = process.platform === "win32";
  const cmd = isWin ? "powershell" : "bash";
  const args = isWin
    ? ["-ExecutionPolicy", "Bypass", "-File", path.join(root, "run.ps1")]
    : [path.join(root, "run")];
  const child = spawn(cmd, args, { cwd: root, stdio: "inherit", shell: false });
  const code = await new Promise((res) => child.on("close", res));
  process.exit(code ?? 1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
