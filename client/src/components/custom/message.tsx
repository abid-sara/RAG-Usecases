import { message } from "../../interfaces/interfaces";
import ReactMarkdown from "react-markdown";

export function PreviewMessage({ message }: { message: message }) {
  return (
    <div
      className={`flex items-start gap-4 px-4 ${
        message.role === "user" ? "flex-row-reverse" : ""
      }`}
    >
      <div
        className={`flex flex-col gap-2 ${
          message.role === "user" ? "items-end" : "items-start"
        } w-full max-w-3xl`}
      >
        {/* Header with timestamp and user info */}
        <div className="flex items-center gap-2 w-full">
          <div className="flex items-center gap-2 px-2 py-1 bg-muted/50 rounded text-sm">
            <span className="text-muted-foreground">
              {new Date(message.timestamp || Date.now())
                .toISOString()
                .slice(0, 19)
                .replace("T", " ")}{" "}
              UTC
            </span>
            <span className="font-medium">
              {message.role === "user" ? "You" : "AI Assistant"}
            </span>
          </div>
        </div>

        {/* Message content */}
        <div
          className={`w-full rounded-xl px-6 py-4 ${
            message.role === "user"
              ? "bg-primary text-primary-foreground"
              : "bg-card border shadow-sm"
          }`}
        >
          {message.role === "assistant" ? (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  h3: ({ node, ...props }) => (
                    <h3 className="text-lg font-bold mt-4 mb-2" {...props} />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc pl-4 my-2" {...props} />
                  ),
                  li: ({ node, ...props }) => (
                    <li className="my-1" {...props} />
                  ),
                  p: ({ node, ...props }) => <p className="my-2" {...props} />,
                  strong: ({ node, ...props }) => (
                    <strong className="font-semibold" {...props} />
                  ),
                  code: ({ node, ...props }) => (
                    <code className="bg-muted px-1 py-0.5 rounded" {...props} />
                  ),
                  blockquote: ({ node, ...props }) => (
                    <blockquote
                      className="border-l-4 border-primary/50 pl-4 my-2"
                      {...props}
                    />
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <div>{message.content}</div>
          )}
        </div>
      </div>
    </div>
  );
}

export function ThinkingMessage() {
  return (
    <div className="flex flex-col w-full items-center px-4">
      <div className="w-full md:max-w-4xl flex flex-col">
        <div className="flex flex-col w-full bg-muted/50 rounded-lg p-6">
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
