import { Icon } from "@/components/ui";

const FAQS: { q: string; a: string }[] = [
  {
    q: "How does triage work?",
    a: "Incoming email is classified by intent (Support / Sales / Billing / Spam / Other) with a confidence score, routed to a teammate by your rules, and given an AI-drafted reply grounded in your knowledge base.",
  },
  {
    q: "Why isn't an email getting a draft?",
    a: "Low-confidence emails are sent to the human-review lane without a draft, and Spam/Other are not auto-drafted. Open the email and click Generate to draft one manually.",
  },
  {
    q: "How do I improve reply quality?",
    a: "Upload more documents (FAQs, policies, canned answers) in Knowledge Base. Replies are grounded in and cite those sources.",
  },
  {
    q: "How do I connect my inbox?",
    a: "Settings → Connect a mailbox. Use a Gmail App Password with host imap.gmail.com and port 993. New mail is then ingested automatically.",
  },
];

export default function SupportPage() {
  return (
    <div className="p-margin-desktop max-w-container-max">
      <header className="mb-lg">
        <h1 className="text-display-lg">Support</h1>
        <p className="text-body-md text-on-surface-variant">Help and answers for running AITriage Ops.</p>
      </header>

      <section className="rounded-xl border border-outline-variant bg-surface-container-lowest divide-y divide-surface-container-high mb-lg">
        {FAQS.map((f) => (
          <div key={f.q} className="p-lg">
            <h2 className="text-title-lg mb-xs flex items-center gap-sm">
              <Icon name="help" className="text-primary text-[20px]" /> {f.q}
            </h2>
            <p className="text-body-sm text-on-surface-variant">{f.a}</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-outline-variant bg-surface-container-low p-lg flex items-center justify-between">
        <div>
          <h2 className="text-title-lg">Still need help?</h2>
          <p className="text-body-sm text-on-surface-variant">Reach the team or open an issue on the project repository.</p>
        </div>
        <div className="flex gap-sm">
          <a href="mailto:support@aitriage.local"
            className="rounded border border-outline-variant px-md py-sm text-label-md hover:bg-surface-container transition-colors flex items-center gap-xs">
            <Icon name="mail" className="text-[18px]" /> Email us
          </a>
          <a href="https://github.com/SaqibMehdi123/aitriage-ops" target="_blank" rel="noreferrer"
            className="rounded bg-primary text-on-primary px-md py-sm text-label-md font-medium hover:bg-primary-container transition-colors flex items-center gap-xs">
            <Icon name="open_in_new" className="text-[18px]" /> Project repo
          </a>
        </div>
      </section>
    </div>
  );
}
