import { useState, useRef, useEffect } from "react";

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([
    { text: "Hello! I'm your Maintenance Assistant. How can I help you today?", sender: 'bot' }
  ]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const send = () => {
    if (!input.trim()) return;

    const userMsg: Message = { text: input, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInput("");

    // Simulate bot response
    setTimeout(() => {
      let botResponse = "I'm analyzing the telemetry data. Everything seems within normal parameters for the selected machine.";
      if (input.toLowerCase().includes("status")) {
        botResponse = "Currently monitoring 5 active machines. Machine-001 shows a slight increase in vibration levels.";
      } else if (input.toLowerCase().includes("help")) {
        botResponse = "I can help you analyze machine health, predict maintenance windows, or explain specific alerts.";
      }

      setMessages(prev => [...prev, { text: botResponse, sender: 'bot' }]);
    }, 1000);
  };

  return (
    <div className="card chatbot-container">
      <h3>🤖 Maintenance AI</h3>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.sender}`}>
            {m.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-container">
        <input
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && send()}
          placeholder="Ask about machine health..."
        />
        <button className="send-btn" onClick={send}>Send</button>
      </div>
    </div>
  );
}
