"use client";

import { useCallback, useEffect, useState } from "react";
import { connectImap, disconnectAccount, listAccounts, syncAccount } from "@/lib/triage";
import type { MailAccount } from "@/lib/types";
import { Icon, Spinner } from "@/components/ui";

const STATUS_STYLES: Record<string, string> = {
  connected: "bg-tertiary-fixed text-on-tertiary-fixed",
  error: "bg-error-container text-on-error-container",
  disconnected: "bg-surface-container-high text-on-surface-variant",
};

export default function SettingsPage() {
  const [accounts, setAccounts] = useState<MailAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [host, setHost] = useState("imap.gmail.com");
  const [port, setPort] = useState(993);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAccounts(await listAccounts());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function connect() {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await connectImap({ host, port, username: username.trim(), password: password.replace(/\s+/g, "") });
      setNotice("Mailbox connected — initial sync started. New mail will appear in the queue shortly.");
      setPassword("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Connection failed");
    } finally {
      setBusy(false);
    }
  }

  async function sync(id: string) {
    await syncAccount(id).catch(() => {});
    setNotice("Sync triggered.");
  }

  async function disconnect(id: string) {
    await disconnectAccount(id).catch(() => {});
    setAccounts((a) => a.filter((x) => x.id !== id));
  }

  return (
    <div className="p-margin-desktop max-w-container-max">
      <header className="mb-lg">
        <h1 className="text-display-lg">Settings</h1>
        <p className="text-body-md text-on-surface-variant">
          Manage your workspace configuration, integrations, and security policies.
        </p>
      </header>

      {error && <div className="mb-md rounded-lg border border-error-container bg-error-container text-on-error-container px-md py-sm text-body-sm">{error}</div>}
      {notice && <div className="mb-md rounded-lg border border-tertiary-fixed bg-tertiary-fixed text-on-tertiary-fixed px-md py-sm text-body-sm">{notice}</div>}

      {/* Connected mailboxes */}
      <section className="rounded-xl border border-outline-variant bg-surface-container-lowest p-lg mb-lg">
        <h2 className="text-headline-sm mb-xs">Mailbox Connection</h2>
        <p className="text-body-sm text-on-surface-variant mb-md">
          Connect a shared inbox so incoming email is triaged automatically.
        </p>

        {loading ? (
          <Spinner label="Loading…" />
        ) : accounts.length > 0 ? (
          <div className="flex flex-col gap-sm mb-lg">
            {accounts.map((a) => (
              <div key={a.id} className="flex items-center justify-between rounded-lg border border-outline-variant bg-surface-container-low px-md py-sm">
                <div className="flex items-center gap-sm min-w-0">
                  <Icon name="alternate_email" className="text-on-surface-variant" />
                  <div className="min-w-0">
                    <p className="text-body-sm text-on-surface truncate">{a.email_address}</p>
                    <p className="text-label-sm text-on-surface-variant">
                      via {a.provider.toUpperCase()} · {a.last_synced_at ? `last synced ${new Date(a.last_synced_at).toLocaleString()}` : "not synced yet"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-sm">
                  <span className={`rounded-full px-sm py-unit text-label-sm font-medium capitalize ${STATUS_STYLES[a.status] ?? STATUS_STYLES.disconnected}`}>{a.status}</span>
                  <button onClick={() => sync(a.id)} className="p-xs hover:bg-surface-container rounded text-on-surface-variant" title="Sync now"><Icon name="sync" className="text-[20px]" /></button>
                  <button onClick={() => disconnect(a.id)} className="p-xs hover:bg-surface-container rounded text-on-surface-variant" title="Disconnect"><Icon name="link_off" className="text-[20px]" /></button>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {/* IMAP connect form */}
        <div className="rounded-lg border border-dashed border-outline-variant p-md">
          <p className="text-label-md text-on-surface mb-sm flex items-center gap-xs">
            <Icon name="add_link" className="text-[18px]" /> Connect a mailbox (IMAP / Gmail app password)
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-sm">
            <input value={host} onChange={(e) => setHost(e.target.value)} placeholder="IMAP host (imap.gmail.com)"
              className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            <input type="number" value={port} onChange={(e) => setPort(Number(e.target.value))} placeholder="Port (993)"
              className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="you@gmail.com"
              className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary" />
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="16-char app password"
              className="rounded border border-outline-variant bg-surface-container-lowest px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-primary" />
          </div>
          <button onClick={connect} disabled={busy || !username || !password}
            className="mt-sm rounded bg-primary text-on-primary px-md py-sm text-label-md font-medium hover:bg-primary-container transition-colors disabled:opacity-60 flex items-center gap-xs">
            <Icon name="link" className="text-[18px]" /> {busy ? "Connecting…" : "Connect mailbox"}
          </button>
          <p className="text-label-sm text-on-surface-variant mt-sm">
            Gmail: enable 2-Step Verification, then create an App Password and paste it here. Credentials are encrypted at rest.
          </p>
        </div>
      </section>

      <section className="rounded-xl border border-outline-variant bg-surface-container-low p-lg">
        <h2 className="text-headline-sm mb-xs">Privacy &amp; Security</h2>
        <p className="text-body-sm text-on-surface-variant">
          PII redaction and per-tenant data-retention controls arrive in Module 9 (Hardening).
        </p>
      </section>
    </div>
  );
}
