import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()

st.set_page_config(
    page_title="MemoryDesk AI",
    page_icon="🧠",
    layout="wide",
)

HINDSIGHT_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "memorydesk-support")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

CUSTOMERS = {
    "CUST-1001": {
        "name": "Ananya Rao",
        "email": "ananya.rao@example.com",
        "plan": "Pro",
        "environment": "Windows 11 + Chrome 140",
    },
    "CUST-1002": {
        "name": "Rahul Mehta",
        "email": "rahul.mehta@example.com",
        "plan": "Business",
        "environment": "macOS 15 + Safari",
    },
    "CUST-1003": {
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "plan": "Starter",
        "environment": "Android 16 + Chrome",
    },
}

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_memories" not in st.session_state:
    st.session_state.last_memories = []
if "seeded" not in st.session_state:
    st.session_state.seeded = False

def get_clients():
    if not HINDSIGHT_API_KEY:
        raise RuntimeError("Missing HINDSIGHT_API_KEY in .env")
    if not GROQ_API_KEY:
        raise RuntimeError("Missing GROQ_API_KEY in .env")

    memory = Hindsight(
        base_url=HINDSIGHT_URL,
        api_key=HINDSIGHT_API_KEY,
    )
    llm = Groq(api_key=GROQ_API_KEY)
    return memory, llm

def ensure_bank(memory):
    memory.create_bank(
        bank_id=BANK_ID,
        name="MemoryDesk Customer Support",
        retain_mission=(
            "For customer support, remember durable customer facts, "
            "past tickets, known issues, environment details, preferences, "
            "frustration or sentiment, attempted solutions, and whether "
            "those solutions worked. Ignore greetings and other transient chatter."
        ),
        reflect_mission=(
            "Act as a customer-support memory layer. Use remembered history "
            "to avoid asking customers to repeat information. Never invent "
            "a ticket, solution, product behavior, or customer fact."
        ),
    )

def customer_tag(customer_id):
    # Hindsight tags let us keep one memory bank while strictly scoping
    # recall/retention to the selected customer.
    return f"customer:{customer_id}"

def seed_customer_history(memory, customer_id):
    tag = customer_tag(customer_id)
    histories = {
        "CUST-1001": [
            (
                "2026-08-14: Customer reported checkout failing with error "
                "PAY-204 on Chrome 140 under Windows 11. They were frustrated "
                "because the issue blocked a purchase."
            ),
            (
                "2026-08-14: Support asked the customer to disable a browser "
                "extension and retry. The extension was the cause and checkout "
                "worked afterward."
            ),
            (
                "2026-08-21: Customer said they prefer concise instructions and "
                "do not want to repeat troubleshooting steps already attempted."
            ),
            (
                "2026-09-03: Customer reported the same checkout error after "
                "re-enabling the extension. The previous extension workaround "
                "worked again."
            ),
        ],
        "CUST-1002": [
            (
                "2026-07-18: Customer reported that CSV exports were empty "
                "when using Safari on macOS 15."
            ),
            (
                "2026-07-18: Clearing the application cache did not help. "
                "Switching to Chrome produced a correct CSV export."
            ),
            (
                "2026-08-02: Customer prefers email follow-up and wants "
                "technical explanations with the exact steps included."
            ),
        ],
        "CUST-1003": [
            (
                "2026-08-29: Customer reported that push notifications were "
                "delayed on Android. Battery optimization was enabled."
            ),
            (
                "2026-08-29: Disabling battery optimization for the app fixed "
                "the notification delay."
            ),
            (
                "2026-09-10: Customer was highly frustrated after missing an "
                "important alert. Avoid repeating generic notification advice."
            ),
        ],
    }

    for item in histories.get(customer_id, []):
        memory.retain(
            bank_id=BANK_ID,
            content=item,
            context="historical support ticket",
            metadata={"customer_id": customer_id},
            tags=[tag],
        )

def recall_history(memory, customer_id, query):
    result = memory.recall(
        bank_id=BANK_ID,
        query=query,
        tags=[customer_tag(customer_id)],
        tags_match="any_strict",
        budget="mid",
        max_tokens=2500,
    )
    memories = []
    for item in result.results:
        text_value = getattr(item, "text", None)
        if text_value:
            memories.append(text_value)
    return memories

def generate_reply(llm, customer, user_message, memories):
    memory_block = "\n".join(f"- {m}" for m in memories) or "- No relevant historical memory found."

    system = f"""
You are MemoryDesk, a professional customer-support agent.

Customer:
- Name: {customer['name']}
- Plan: {customer['plan']}
- Environment: {customer['environment']}

Relevant long-term memory retrieved from Hindsight:
{memory_block}

Rules:
1. Use the memory to avoid making the customer repeat their history.
2. Explicitly acknowledge previous attempts when relevant.
3. If a previous fix worked, build on it instead of restarting from generic troubleshooting.
4. Be empathetic, especially if the customer has a history of frustration.
5. Do not claim that a fix worked unless the memory or current conversation supports it.
6. If information is missing, ask only the minimum necessary question.
7. Give concise, actionable steps.
8. Never expose internal memory-system details unless asked.
"""

    response = llm.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            *st.session_state.messages[-8:],
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=700,
    )
    return response.choices[0].message.content

def retain_interaction(memory, customer_id, user_message, assistant_reply):
    conversation = (
        f"Customer ({datetime.now().isoformat(timespec='seconds')}): {user_message}\n"
        f"Support agent ({datetime.now().isoformat(timespec='seconds')}): {assistant_reply}"
    )
    memory.retain(
        bank_id=BANK_ID,
        content=conversation,
        context="live customer support conversation",
        metadata={"customer_id": customer_id},
        tags=[customer_tag(customer_id)],
    )

st.title("🧠 MemoryDesk AI")
st.caption("Customer support that remembers what happened before.")

with st.sidebar:
    st.header("Customer")
    customer_id = st.selectbox(
        "Select customer",
        list(CUSTOMERS.keys()),
        format_func=lambda x: f"{x} — {CUSTOMERS[x]['name']}",
    )
    customer = CUSTOMERS[customer_id]

    st.write(f"**Plan:** {customer['plan']}")
    st.write(f"**Environment:** {customer['environment']}")

    if st.button("🌱 Seed demo history", use_container_width=True):
        try:
            memory, _ = get_clients()
            ensure_bank(memory)
            seed_customer_history(memory, customer_id)
            st.session_state.seeded = True
            st.success("Historical tickets stored in Hindsight.")
        except Exception as exc:
            st.error(f"Could not seed memory: {exc}")

    if st.button("🧹 New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_memories = []
        st.rerun()

    st.divider()
    st.markdown("**Demo story**")
    st.caption(
        "Seed a customer's history → ask about an old issue → "
        "show that the agent remembers the environment and previous fix → "
        "send another message → show that the new interaction is retained."
    )

chat_col, memory_col = st.columns([2.2, 1])

with chat_col:
    st.subheader(f"Support chat · {customer['name']}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Describe your issue…")
    if prompt:
        try:
            memory, llm = get_clients()
            ensure_bank(memory)

            memories = recall_history(
                memory,
                customer_id,
                f"{prompt}\nCustomer environment: {customer['environment']}",
            )
            st.session_state.last_memories = memories

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Checking customer history…"):
                    reply = generate_reply(llm, customer, prompt, memories)
                    st.markdown(reply)

            st.session_state.messages.append(
                {"role": "assistant", "content": reply}
            )

            # Retain after generating the answer so the next interaction can
            # learn from this one.
            retain_interaction(memory, customer_id, prompt, reply)

        except Exception as exc:
            st.error(
                "The agent could not complete the request. "
                f"Check your API keys and Hindsight connection.\n\n{exc}"
            )

with memory_col:
    st.subheader("🧠 Memory used")
    if st.session_state.last_memories:
        st.success(
            f"{len(st.session_state.last_memories)} relevant memories recalled"
        )
        for memory in st.session_state.last_memories:
            st.markdown(f"• {memory}")
    else:
        st.info("No memory retrieved yet. Seed history and send a message.")

    st.divider()
    st.markdown("**Why this matters**")
    st.write(
        "Without memory, the agent starts from the latest message. "
        "With Hindsight, it can retrieve past tickets, environments, "
        "preferences, and previously successful solutions."
    )
