import os
import asyncio
import streamlit as st
from openai import AsyncOpenAI
from dotenv import load_dotenv

# ------------------------------------------------------
# Environment Setup
# ------------------------------------------------------
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------------------------------
# Character Profiles
# ------------------------------------------------------
CHARACTERS = {
    "yoda": {
        "desc": "Speak like Yoda — wise, inverted sentences, calm and thoughtful.",
        "avatar": "🧙‍♂️",
    },
    "jar jar binks": {
        "desc": "Speak like Jar Jar Binks — silly, clumsy, and overly cheerful.",
        "avatar": "🤪",
    },
    "pikachu": {
        "desc": "Speak like Pikachu — use variations of 'Pika!' expressively.",
        "avatar": "⚡",
    },
    "groot": {
        "desc": "Speak like Groot — only say 'I am Groot' with emotional nuance.",
        "avatar": "🌱",
    },
    "toge inumaki": {
        "desc": "Speak like Toge Inumaki — use onigiri ingredient words like 'Salmon' and 'Tuna' to convey meaning.",
        "avatar": "🍙",
    },
}

BASE_PROMPT = """You are a base agent managing which fictional character the user is talking to.
Available characters: Yoda, Jar Jar Binks, Pikachu, Groot, and Toge Inumaki.

Rules:
1. Ask which character to talk to if none selected.
2. Detect if user wants to switch.
3. Say “Switching to <Character>...” when switching.
4. Preserve memory per character.
"""

# ------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------
if "conversation_memory" not in st.session_state:
    st.session_state.conversation_memory = {name: [] for name in CHARACTERS}
if "active_character" not in st.session_state:
    st.session_state.active_character = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ------------------------------------------------------
# Core Logic
# ------------------------------------------------------
async def chat_with_character(character: str, message: str):
    """Generate response as the given character using its prior context."""
    memory = "\n".join(st.session_state.conversation_memory[character] + [f"User: {message}"])
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CHARACTERS[character]["desc"]},
            {"role": "user", "content": memory},
        ],
    )
    reply = response.choices[0].message.content.strip()
    st.session_state.conversation_memory[character] += [
        f"User: {message}",
        f"{character.title()}: {reply}",
    ]
    return reply

async def base_decision(message: str):
    """Ask the base agent if we should switch or stay."""
    active = st.session_state.active_character or "None"
    base_context = (
        f"Current character: {active}\n"
        f"User said: {message}\n\n"
        "Respond ONLY with:\n"
        "1. 'switch:<character_name>' if a switch is needed, or\n"
        "2. 'stay' if we should continue with the current one, or\n"
        "3. 'prompt' if user hasn't chosen any yet."
    )
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": BASE_PROMPT},
            {"role": "user", "content": base_context},
        ],
    )
    return response.choices[0].message.content.strip().lower()

async def process_user_input(user_input: str):
    """Handle user input and conversation logic."""
    if st.session_state.active_character is None:
        # Initial character selection
        for name in CHARACTERS.keys():
            if name in user_input.lower():
                st.session_state.active_character = name
                msg = f"Switching to {name.title()}..."
                st.session_state.chat_history.append(("Assistant", msg))
                reply = await chat_with_character(name, user_input)
                st.session_state.chat_history.append((name.title(), reply))
                return
        st.session_state.chat_history.append(
            ("Assistant", "Who would you like to talk to? (Yoda, Jar Jar Binks, Pikachu, Groot, or Toge Inumaki)")
        )
        return

    # Base agent decides switch/stay
    decision = await base_decision(user_input)
    if decision.startswith("switch:"):
        new_char = decision.split(":")[1].strip()
        if new_char in CHARACTERS:
            st.session_state.active_character = new_char
            msg = f"Switching to {new_char.title()}..."
            st.session_state.chat_history.append(("Assistant", msg))
            reply = await chat_with_character(new_char, user_input)
            st.session_state.chat_history.append((new_char.title(), reply))
        else:
            st.session_state.chat_history.append(("Assistant", "Sorry, I don’t recognize that character."))
    elif decision == "stay":
        reply = await chat_with_character(st.session_state.active_character, user_input)
        st.session_state.chat_history.append((st.session_state.active_character.title(), reply))
    else:
        st.session_state.chat_history.append(
            ("Assistant", "Who would you like to talk to? (Yoda, Jar Jar Binks, Pikachu, Groot, or Toge Inumaki)")
        )

# ------------------------------------------------------
# Streamlit UI Configuration
# ------------------------------------------------------
st.set_page_config(
    page_title="🎭 Multi-Character AI Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished UI
st.markdown(
    """
    <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #111827, #1e293b);
            color: white;
            font-family: 'Inter', sans-serif;
        }
        .chat-bubble {
            border-radius: 1rem;
            padding: 0.8rem 1.2rem;
            margin-bottom: 0.6rem;
            max-width: 80%;
            word-wrap: break-word;
        }
        .user-bubble {
            background-color: #2563eb;
            color: white;
            align-self: flex-end;
        }
        .assistant-bubble {
            background-color: #334155;
            color: white;
            align-self: flex-start;
        }
        .character-bubble {
            background-color: #475569;
            color: white;
            align-self: flex-start;
        }
        .character-card {
            background-color: #1e293b;
            padding: 1rem;
            border-radius: 1rem;
            margin-bottom: 0.5rem;
            border: 1px solid #334155;
        }
        .character-card:hover {
            background-color: #334155;
        }
        .stChatInput textarea {
            background-color: #0f172a !important;
            color: white !important;
            border-radius: 1rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------
# Sidebar
# ------------------------------------------------------
st.sidebar.title("🎭 Characters")
st.sidebar.caption("Select a character to view their description.")
for name, info in CHARACTERS.items():
    st.sidebar.markdown(
        f"<div class='character-card'><b>{info['avatar']} {name.title()}</b><br><small>{info['desc']}</small></div>",
        unsafe_allow_html=True,
    )

if st.session_state.active_character:
    st.sidebar.success(f"Current Character: {st.session_state.active_character.title()}")

# ------------------------------------------------------
# Main Chat Window
# ------------------------------------------------------
st.title("💬 Multi-Character AI Chat")
st.caption("Talk to your favorite fictional characters — switch naturally, and continue where you left off.")

chat_container = st.container()
for speaker, text in st.session_state.chat_history:
    bubble_class = (
        "user-bubble" if speaker == "You"
        else "assistant-bubble" if speaker == "Assistant"
        else "character-bubble"
    )
    avatar = ""
    if speaker.lower() in CHARACTERS:
        avatar = CHARACTERS[speaker.lower()]["avatar"] + " "
    chat_container.markdown(
        f"<div class='chat-bubble {bubble_class}'><b>{avatar}{speaker}:</b> {text}</div>",
        unsafe_allow_html=True,
    )

# ------------------------------------------------------
# Input Box
# ------------------------------------------------------
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.chat_history.append(("You", user_input))
    asyncio.run(process_user_input(user_input))
    st.rerun()
