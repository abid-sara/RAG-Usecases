export function MessageTimestamp({ date }: { date: Date }) {
  const formatTime = (date: Date) => {
    return date.toISOString().slice(0, 19).replace('T', ' ') + ' UTC';
  };

  return (
    <div className="text-xs text-muted-foreground">
      {formatTime(date)}
    </div>
  );
}