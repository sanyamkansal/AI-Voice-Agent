# Building Dukaan Sathi: An AI Voice Assistant for India's Kirana Stores

Over the past 9 days, I took on the **Voice for Bharat Challenge** to build an AI Voice Agent tailored for India. The result? **Dukaan Sathi**, a fully functional voice assistant designed specifically for local Kirana store owners (dukaandars).

Here is the story of how Dukaan Sathi evolved from a simple starter template into a multi-agent powerhouse capable of managing inventory, handling escalations, and speaking in authentic, pure Hindi.

---

## 🚀 The Problem & The Solution

India runs on Kirana stores. Dukaandars are incredibly busy people, often juggling inventory, customer queries, and billing all at once. They don’t have the time to sit at a laptop and type data into complicated software.

**Why voice?** Voice is the most natural, frictionless interface. I wanted a Dukaandar to be able to just speak to their phone: *"Mere paas kitna chawal bacha hai?"* (How much rice do I have left?) and get an instant, helpful response.

**Dukaan Sathi** is that solution. It is a helpful, polite, and intelligent voice agent that acts as a digital assistant for the store.

---

## 🛠️ Key Features Built Over 9 Days

Dukaan Sathi isn't just a basic chatbot with text-to-speech bolted on. It's a complete, intelligent system. Here are the highlights of what I built:

1. **Authentic Indian Voices:** Powered by **Murf Falcon**, Dukaan Sathi uses extremely natural-sounding Indian voices. The main agent uses a polite female voice (Anisha), ensuring a welcoming tone.
2. **Strict Native Script Guardrails:** One of the most important features I enforced was ensuring the LLM *always* outputs Hindi in the native Devanagari script (नमस्ते) and *never* in Romanized Hinglish (namaste). This ensures the text-to-speech engine pronounces words perfectly without awkward accents.
3. **Persistent Memory:** The agent remembers returning customers! Using SQLite and LiveKit's Job Context, the agent seamlessly pulls up past interactions so it doesn't have to re-ask for your name.
4. **Tool Use & Analytics:** The agent can actively fetch stock balances and log call outcomes. I built a real-time **Call Analytics Dashboard** in Next.js that updates the moment a call ends!
5. **Human Escalation:** When a customer gets angry or the agent doesn't know the answer, it triggers a `create_escalation` tool that saves a transcript and logs a ticket for the human owner to review.
6. **Multi-Agent Handoffs:** The crowning achievement! If a user asks for a refund, Dukaan Sathi transfers the call to a dedicated Returns Specialist. The caller actually hears the voice change to a completely new male voice (Samar), and he instantly knows the context of the conversation.

---

## 🧗 The Difficult Parts & Lessons Learned

Pretending everything worked perfectly on the first try wouldn't be helpful! Here are some hurdles I faced and how I solved them:

### 1. The Language Barrier (Romanized vs. Devanagari)
**The Problem:** LLMs naturally default to writing Hindi in the Latin alphabet (Hinglish) because that's how a lot of their training data looks. However, when you feed Romanized Hindi into an Indian Text-to-Speech engine, the pronunciation often breaks down or sounds unnatural.
**The Solution:** Heavy prompt engineering. I had to explicitly instruct the agent: *"Always write every language in its own native script. Hindi -> Devanagari (नमस्ते), never romanized."* This instantly fixed the pronunciation issues.

### 2. Next.js `node_modules` Nightmares
**The Problem:** When copying my daily workspaces (Day 7, Day 8, Day 9) to keep track of progress, I was getting bizarre `d3` export errors in the Next.js frontend build. 
**The Solution:** The `node_modules` folder doesn't take kindly to being duplicated via copy-paste across environments. The fix was simple but crucial: delete the old `node_modules` and `.next` folders and run a fresh `pnpm install` in the new directory.

---

## 🛠️ Build Your Own Voice Agent

Want to build your own version of Dukaan Sathi? It's easier than you think. You need four main components:
* **Speech-to-Text (STT):** To transcribe the user's voice.
* **LLM:** The "brain" (e.g., OpenAI or Gemini).
* **Text-to-Speech (TTS):** To generate the agent's voice (Murf Falcon is highly recommended for Indian voices).
* **Real-time Transport:** LiveKit handles the ultra-low latency WebRTC streaming.

### Getting Started

1. **Clone the Starter:** Start with a LiveKit + Next.js + Python template.
2. **Environment Variables:** You'll need API keys for LiveKit, your LLM, and your TTS provider. **Never commit these to GitHub!** Always store them in a `.env.local` (frontend) and `.env` (backend) file.
3. **Run the Backend (Python):** 
   ```bash
   uv run src/agent.py dev
   ```
4. **Run the Frontend (Next.js):** 
   ```bash
   npm run dev
   ```
5. **Test it:** Open `localhost:3000`, click connect, and start talking! You can write a custom `SYSTEM_PROMPT` in `agent.py` to give your agent any personality you want.

---

This 10-day challenge proved that voice AI is no longer a futuristic concept—it is accessible, buildable, and ready to solve real-world problems in India today. 

*Thanks to LiveKit and Murf AI for providing the incredible tools that made this possible!*
