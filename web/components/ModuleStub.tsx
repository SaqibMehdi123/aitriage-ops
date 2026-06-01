// Placeholder for sections delivered in later modules. Keeps navigation and the
// shell honest during the foundation phase without faking feature behaviour.
export default function ModuleStub({
  title,
  description,
  icon,
  module,
}: {
  title: string;
  description: string;
  icon: string;
  module: string;
}) {
  return (
    <div className="p-margin-desktop max-w-container-max">
      <header className="mb-lg">
        <h1 className="text-display-lg">{title}</h1>
        <p className="text-body-md text-on-surface-variant">{description}</p>
      </header>
      <div className="rounded-xl border border-dashed border-outline-variant bg-surface-container-low p-xl flex flex-col items-center text-center gap-sm">
        <span className="material-symbols-outlined text-[40px] text-on-surface-variant">{icon}</span>
        <h2 className="text-headline-sm">Coming in {module}</h2>
        <p className="text-body-sm text-on-surface-variant max-w-md">
          This screen is designed and scoped. It will be built when {module} lands.
        </p>
      </div>
    </div>
  );
}
