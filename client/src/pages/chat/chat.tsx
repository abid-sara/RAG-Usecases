import { ChatInput } from "@/components/custom/chatinput";
import { PreviewMessage, ThinkingMessage } from "../../components/custom/message";
import { useScrollToBottom } from '@/components/custom/use-scroll-to-bottom';
import { useState } from "react";
import { message } from "../../interfaces/interfaces";
import { Overview } from "@/components/custom/overview";
import { Header } from "@/components/custom/header";
import { v4 as uuidv4 } from "uuid";
import axios from "axios";

const API_URL = "http://localhost:5000/api/qa"; // Flask API endpoint

export function Chat() {
  const [messagesContainerRef, messagesEndRef] = useScrollToBottom<HTMLDivElement>();
  const [messages, setMessages] = useState<message[]>([]);
  const [question, setQuestion] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  async function handleSubmit(text?: string) {
    if (isLoading) return;

    const messageText = text || question;
    setIsLoading(true);
    
    const traceId = uuidv4();
    setMessages(prev => [...prev, { content: messageText, role: "user", id: traceId }]);
    setQuestion("");

    try {
      const response = await axios.post(API_URL, { 
        query: messageText,
        top_n: 20,
        weights: {    
            tfidf: 0.3,
            bm25: 0.3,
            embeddings: 0.4
        },
        search_method: "hybrid"
      });
      setMessages(prev => [...prev, { content: response.data.answer, role: "assistant", id: uuidv4() }]);
    } catch (error) {
      console.error("API error:", error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <Header/>
      <div className="flex flex-col min-w-0 gap-6 flex-1 overflow-y-scroll pt-4" ref={messagesContainerRef}>
        {messages.length === 0 && <Overview />}
        {messages.map((message, index) => (
          <PreviewMessage key={index} message={message} />
        ))}
        {isLoading && <ThinkingMessage />}
        <div ref={messagesEndRef} className="shrink-0 min-w-[24px] min-h-[24px]" />
      </div>
      <div className="flex flex-col items-center mx-auto px-4 bg-background pb-4 md:pb-6 gap-2 w-full md:max-w-3xl">
        <ChatInput  
          question={question}
          setQuestion={setQuestion}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
        <p className="reminder-text rtl-text" dir="rtl">
          تنبيه: هذا النظام يعتمد على نموذج لغوي كبير (LLM)، وقد تحدث أخطاء. يرجى الرجوع دائمًا إلى الوثائق الرسمية للتأكد.
        </p>
      </div>
    </div>
  );
};