import React, { useState } from "react";
import { sendMessage } from "../utils/api";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const handleSend = async () => {
    const reply = await sendMessage(input);
    setMessages([...messages, { user: input, bot: reply }]);
    setInput("");
  };

  return (
    <div>
      <div>
        {messages.map((m, i) => (
          <div key={i}>
            <p><strong>You:</strong> {m.user}</p>
            <p><strong>Bot:</strong> {m.bot}</p>
          </div>
        ))}
      </div>
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={handleSend}>Send</button>
    </div>
  );
}
