# 🧠 MemoryDesk AI — Customer Support Agent with Long-Term Memory

A hackathon-ready customer support agent built around **Hindsight memory**.

The agent remembers:
- past support tickets
- known issues
- customer environment
- frustration/sentiment
- previous troubleshooting steps
- which solutions worked
- preferences learned during support conversations

## Architecture

```text
Customer
   ↓
Streamlit UI
   ↓
Recall customer history from Hindsight
   ↓
Groq LLM + current message + relevant memories
   ↓
Personalized support response
   ↓
Retain the new interaction in Hindsight
   ↓
Future conversations become more informed
```

## Tech stack

- Python
- Streamlit
- Hindsight Cloud
- Groq
- `hindsight-client`
- `python-dotenv`

Hindsight provides the persistent memory layer. The current Hindsight Python SDK exposes `retain`, `recall`, and `reflect` operations; this project uses `retain` and `recall` directly so the memory flow is visible during the demo.

## 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPO_URL
cd customer-support-memory-agent
```

## 2. Create a virtual environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Add API keys

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Put your Hindsight Cloud API key and Groq API key in `.env`.

**Never commit `.env` to GitHub.**

## 5. Run

```bash
streamlit run app.py
```

The browser will open the MemoryDesk dashboard.

## 6. Demo

1. Select `CUST-1001 — Ananya Rao`.
2. Click **Seed demo history**.
3. Ask:

> My checkout is failing again. Do I have to repeat all the troubleshooting steps?

4. The agent should recall the previous checkout error, Chrome/Windows environment, and the extension workaround.
5. Send another message such as:

> I re-enabled the extension and now the error is back.

6. The new conversation is retained in Hindsight.
7. Change the customer to another customer and verify that their memories are different.

## 60-second judge demo

**Problem:** Customers hate repeating their story.

**Interaction 1:** Show a customer with a previous checkout incident.

**Memory:** Hindsight retrieves:
- previous error
- environment
- attempted solution
- successful solution
- customer preference/frustration

**Agent:** Responds using that history instead of restarting generic troubleshooting.

**Interaction 2:** Add a new outcome.

**Learning:** The new interaction is retained and becomes available to later conversations.

## Important

This repository uses synthetic customer data for the hackathon demo. Do not put real customer PII or confidential tickets into a public repository.

## Hackathon alignment

The project makes Hindsight memory central rather than decorative:
- customer-specific memory is tagged
- recall happens before response generation
- every new support interaction is retained
- the UI exposes the retrieved memories
- the demo can show improvement over multiple interactions
