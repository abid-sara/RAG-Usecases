import { message } from "../../interfaces/interfaces";

export function PreviewMessage({ message }: { message: message }) {
  return (
    <div className="flex flex-col w-full items-center px-4">
      <div className="w-full md:max-w-4xl flex flex-col">
        {message.role === "assistant" ? (
          <div className="flex flex-col w-full bg-background border border-border rounded-lg p-6">
            <pre className="whitespace-pre-wrap font-mono text-base break-words w-full text-foreground">
              {message.content}
            </pre>
          </div>
        ) : (
          // User message
          <div className="flex flex-col w-full bg-muted/20 rounded-lg p-6 bg-[white]">
            <pre className="whitespace-pre-wrap font-sans text-black text-base break-words">
              {message.content}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

// ThinkingMessage component
export function ThinkingMessage() {
  return (
    <div className="flex flex-col w-full items-center px-4">
      <div className="w-full md:max-w-4xl flex flex-col">
        <div className="flex flex-col w-full bg-background border border-border rounded-lg p-6">
          <div className="flex gap-2 items-center">
            <span className="animate-bounce">●</span>
            <span className="animate-bounce [animation-delay:0.2s]">●</span>
            <span className="animate-bounce [animation-delay:0.4s]">●</span>
          </div>
        </div>
      </div>
    </div>
  );
}
