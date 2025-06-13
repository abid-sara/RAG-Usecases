import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { cx } from "classix";
import { SparklesIcon } from "./icons";
import { Markdown } from "./markdown";
import { message } from "../../interfaces/interfaces";
import { MessageActions } from "@/components/custom/actions";

export const PreviewMessage = ({ message }: { message: message }) => {
  const [displayedText, setDisplayedText] = useState("");

  useEffect(() => {
    if (message.role === "assistant" && message.content) {
      setDisplayedText(""); // Reset for new message
      
      const messageLength = message.content.length;
      const typingDuration = 20000; // Total animation time in ms (adjust as needed)
      const chunkSize = Math.max(1, Math.ceil(messageLength / (typingDuration / 16))); // Characters per frame
      let displayedLength = 0;
      
      const animationFrame = () => {
        // Add next chunk of characters
        displayedLength = Math.min(displayedLength + chunkSize, messageLength);
        setDisplayedText(message.content.substring(0, displayedLength));
        
        // Continue animation if not complete
        if (displayedLength < messageLength) {
          requestId = requestAnimationFrame(animationFrame);
        }
      };
      
      // Start animation
      let requestId = requestAnimationFrame(animationFrame);
      
      // Cleanup function
      return () => {
        cancelAnimationFrame(requestId);
      };
    } else {
      setDisplayedText(message.content); // Instantly show user messages
    }
  }, [message]);

  // Improved function to process and fix tables in RTL content
  useEffect(() => {
    if (message.role === "assistant" && displayedText) {
      // Use setTimeout to ensure DOM is updated
      const timeoutId = setTimeout(() => {
        const tables = document.querySelectorAll('.rtl-content table');
        tables.forEach(table => {
          // Add RTL class
          table.classList.add('rtl-table');
          
          // Force RTL on all cells
          const cells = table.querySelectorAll('th, td');
          cells.forEach(cell => {
            cell.classList.add('rtl-cell');
            //cell.style.textAlign = 'right'; // Add inline style for immediate effect
          });
          
          // Center the table with a wrapper if needed
          if (!table.parentElement?.classList.contains('table-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.classList.add('table-wrapper');
            wrapper.style.display = 'flex';
            wrapper.style.justifyContent = 'center';
            wrapper.style.width = '100%';
            wrapper.style.margin = '1rem 0';
            table.parentNode?.insertBefore(wrapper, table);
            wrapper.appendChild(table);
          }
        });
      }, 200); // Slightly longer delay to ensure content is rendered
      
      return () => clearTimeout(timeoutId);
    }
  }, [displayedText, message.role]);

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      data-role={message.role}
    >
      <div
        className={cx(
          "group-data-[role=user]/message:bg-zinc-700 dark:group-data-[role=user]/message:bg-muted group-data-[role=user]/message:text-white flex gap-4 group-data-[role=user]/message:px-3 w-full group-data-[role=user]/message:w-fit group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:py-2 rounded-xl"
        )}
      >
        {message.role === "assistant" && (
          <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
            <SparklesIcon size={14} />
          </div>
        )}

        <div className="flex flex-col w-full">
          {message.content && (
            <div className="flex flex-col gap-4 text-right rtl-content" dir="rtl">
              <Markdown>{displayedText}</Markdown>
            </div>
          )}

          {message.role === "assistant" && <MessageActions message={message} />}
        </div>
      </div>
    </motion.div>
  );
};

// Enhanced ThinkingMessage with animation
export const ThinkingMessage = () => {
  const role = "assistant";
  const [dots, setDots] = useState("");
  
  // Animate the dots for thinking effect
  useEffect(() => {
    const interval = setInterval(() => {
      setDots(prev => {
        if (prev.length >= 3) return "";
        return prev + ".";
      });
    }, 500);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.div
      className="w-full mx-auto max-w-3xl px-4 group/message"
      initial={{ y: 5, opacity: 0 }}
      animate={{ y: 0, opacity: 1, transition: { delay: 0.2 } }}
      data-role={role}
    >
      <div
        className={cx(
          "flex gap-4 w-full rounded-xl"
        )}
      >
        <div className="size-8 flex items-center rounded-full justify-center ring-1 shrink-0 ring-border">
          <SparklesIcon size={14} />
        </div>
        
        <div className="flex flex-col w-full">
          <div className="flex flex-col gap-4 text-right" dir="rtl">
            <p className="text-sm text-muted-foreground">
              جاري التفكير{dots}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};