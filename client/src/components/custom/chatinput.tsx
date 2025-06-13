import { Textarea } from "../ui/textarea";
import { cx } from "classix";
import { toast } from "sonner";

interface ChatInputProps {
  question: string;
  setQuestion: (question: string) => void;
  onSubmit: (text?: string) => void;
  isLoading: boolean;
}

export const ChatInput = ({
  question,
  setQuestion,
  onSubmit,
  isLoading,
}: ChatInputProps) => {
  return (
    <div className="relative w-full flex flex-col gap-4">
      <input
        type="file"
        className="fixed -top-4 -left-4 size-0.5 opacity-0 pointer-events-none"
        multiple
        tabIndex={-1}
      />

      <Textarea
        placeholder="Example: What are the PCI DSS requirements for password management?"
        className={cx(
          "min-h-[24px] max-h-[calc(75dvh)] overflow-hidden resize-none rounded-xl text-base bg-muted"
        )}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();

            if (isLoading) {
              toast.error("Please wait until the model finishes responding!");
            } else {
              onSubmit();
            }
          }
        }}
        rows={3}
      />
    </div>
  );
};
