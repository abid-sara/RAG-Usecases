export function Overview() {
  const formatDateTime = () => {
    const now = new Date();
    return now.toISOString().slice(0, 19).replace("T", " ");
  };

  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-4 px-4 py-20">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="text-sm text-muted-foreground mb-4">
          {formatDateTime()} UTC
        </div>
        <h1 className="text-4xl font-bold">Welcome to PCI DSS Assistant</h1>
        <p className="text-muted-foreground max-w-96">
          How can I help you with PCI DSS requirements today?
        </p>
      </div>
    </div>
  );
}
