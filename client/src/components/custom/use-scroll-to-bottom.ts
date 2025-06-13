import { useEffect, useRef, RefObject } from "react";

export function useScrollToBottom<T extends HTMLElement>(): [
  RefObject<T>,
  RefObject<T>,
] {
  const containerRef = useRef<T>(null);
  const endRef = useRef<T>(null);
  // Store the previous scroll height
  const previousScrollHeightRef = useRef<number | undefined>(undefined);
  // Flag to track if the user has manually scrolled up
  const userScrolledUpRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    const end = endRef.current;

    if (container && end) {
      // Function to handle scroll event and update the flag
      const handleScroll = () => {
        const { scrollHeight, scrollTop, clientHeight } = container;
        // Consider user scrolled up if they are more than a few pixels from the bottom
        const isNearBottom = scrollHeight - scrollTop - clientHeight <= 5;
        userScrolledUpRef.current = !isNearBottom;
      };

      // Add scroll listener
      container.addEventListener('scroll', handleScroll, { passive: true });

      const observer = new MutationObserver(() => {
        const { scrollHeight } = container;

        // Only scroll down automatically if the user hasn't manually scrolled up
        // or if it's the initial load/very first mutation.
        const shouldScroll = !userScrolledUpRef.current || previousScrollHeightRef.current === undefined;

        if (shouldScroll) {
          end.scrollIntoView({ behavior: "smooth", block: "end" });
        }
        // Update the scroll height for the next check
        previousScrollHeightRef.current = scrollHeight;
      });

      observer.observe(container, {
        childList: true, // Observe direct children additions/removals
        subtree: true,   // Observe all descendants
      });

      // Initial scroll to bottom when the component mounts
      end.scrollIntoView({ behavior: "instant", block: "end" });
      previousScrollHeightRef.current = container.scrollHeight;
      // Assume user starts at the bottom
      userScrolledUpRef.current = false;


      // Cleanup function
      return () => {
        observer.disconnect();
        container.removeEventListener('scroll', handleScroll);
      }
    }
  // Add dependencies to re-run effect if refs change (though unlikely)
  }, [containerRef, endRef]);

  return [containerRef, endRef];
}