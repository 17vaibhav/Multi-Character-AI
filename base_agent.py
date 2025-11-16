import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Character Profiles ---
CHARACTERS = {
    "yoda": "Speak like Yoda — wise, inverted sentence order, calm and philosophical.",
    "jar jar binks": "Speak like Jar Jar Binks — silly, clumsy, and cheerful.",
    "pikachu": "Speak like Pikachu — only say variations of 'Pika!'.",
    "groot": "Speak like Groot — only say 'I am Groot' with tone variations.",
    "toge inumaki": "Speak like Toge Inumaki — use onigiri ingredient words"
}

# --- Base Agent Instructions ---
BASE_PROMPT = """You are a base agent that manages which fictional character the user is talking to.
You can hand off control to one of these characters: Yoda, Jar Jar Binks, Pikachu, Groot, or Toge Inumaki.

Rules:
1. If the user hasn’t picked anyone, ask them which character they’d like to talk to.
2. If the user mentions or refers to another character’s name, interpret that as a request to switch.
3. When switching, announce it naturally (e.g., “Switching to Groot...”).
4. Once switched, the chosen character should continue the conversation naturally until another switch is requested.
5. Preserve what each character said before — maintain memory per character.
"""

# --- Memory Store ---
conversation_memory = {name: [] for name in CHARACTERS}
active_character = None


async def chat_with_character(character: str, message: str):
    """Generate response as the given character using its prior context."""
    global conversation_memory

    conversation = "\n".join(conversation_memory[character] + [f"User: {message}"])
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CHARACTERS[character]},
            {"role": "user", "content": conversation}
        ],
    )

    reply = response.choices[0].message.content.strip()
    conversation_memory[character].append(f"User: {message}")
    conversation_memory[character].append(f"{character.title()}: {reply}")
    return reply


async def base_decision(message: str):
    """Let the base agent decide what to do next."""
    global active_character

    base_context = (
        f"Currently active character: {active_character or 'None'}\n"
        f"User said: {message}\n\n"
        "Decide whether to continue the current conversation or switch to a different character.\n"
        "Respond ONLY with:\n"
        "1. 'switch:<character_name>' if a switch is needed, or\n"
        "2. 'stay' if we should continue with the current one, or\n"
        "3. 'prompt' if user hasn't chosen any yet."
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": BASE_PROMPT},
            {"role": "user", "content": base_context}
        ],
    )

    decision = response.choices[0].message.content.strip().lower()
    return decision


async def main():
    global active_character

    print("Welcome! Type a message or 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting the chat. Goodbye!")
            break

        if active_character is None:
            # Ask which character to start with
            print("Assistant: Hello! Who would you like to talk to? (Yoda, Jar Jar Binks, Pikachu, Groot, or Toge Inumaki)")
            choice = user_input.lower()

            # Find best match
            for name in CHARACTERS.keys():
                if name in choice:
                    active_character = name
                    print(f"Assistant: Switching to {active_character.title()}...")
                    break

            if active_character is None:
                continue

            reply = await chat_with_character(active_character, user_input)
            print(f"{active_character.title()}: {reply}")
            continue

        # Let base decide whether to stay or switch
        decision = await base_decision(user_input)

        if decision.startswith("switch:"):
            new_char = decision.split(":")[1].strip()
            if new_char in CHARACTERS:
                print(f"Assistant: Switching to {new_char.title()}...")
                active_character = new_char
                reply = await chat_with_character(active_character, user_input)
                print(f"{active_character.title()}: {reply}")
            else:
                print("Assistant: Sorry, I don’t recognize that character.")
        elif decision == "stay":
            reply = await chat_with_character(active_character, user_input)
            print(f"{active_character.title()}: {reply}")
        else:
            print("Assistant: Who would you like to talk to? (Yoda, Jar Jar Binks, Pikachu, Groot, or Toge Inumaki)")


if __name__ == "__main__": 
    asyncio.run(main())

