import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)
api_key = (os.getenv("GEMINI_API_KEY") or os.getenv("Apikey") or "").strip()
model = "gemini-3.8-flash"
base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

st.set_page_config(page_title="Study Agent")
st.title("Study Agent")
st.caption("Your personal study helper for learning and revision.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.button("Clear conversation"):
    st.session_state.messages = []
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.subheader("Ask your study question")
question = st.text_area(
    "Your question",
    key="question_input",
    placeholder="Example: Explain photosynthesis in simple terms...",
    height=110,
)
cleaned_question = question.strip()
validation_checks = [
    ("Question is not empty", bool(cleaned_question)),
    (
        "Contains at least one letter or number",
        any(character.isalnum() for character in cleaned_question),
    ),
    ("500 characters or fewer", len(cleaned_question) <= 500),
]

with st.container(border=True):
    st.markdown("#### Input validation")
    st.caption(f"{len(cleaned_question)} / 500 characters")
    for label, passed in validation_checks:
        icon = "✅" if passed else "❌"
        st.markdown(f"{icon} **{label}**")

question_is_valid = all(passed for _, passed in validation_checks)
if question_is_valid:
    st.success("Question is valid and ready to send.")
else:
    st.info("Fix the checks above before sending your question.")

if st.button("Validate and ask study agent", type="primary"):
    if not question_is_valid:
        st.error("Please fix the validation checks before continuing.")
    elif not api_key:
        st.error(
            f"Gemini API key not found. Add `GEMINI_API_KEY=your_key` to "
            f"`{ENV_PATH.name}` and restart the app."
        )
    else:
        conversation = [
            *st.session_state.messages,
            {"role": "user", "content": cleaned_question},
        ]

        study_prompt = (
            "You are a patient and encouraging study agent. Explain concepts clearly, "
            "break difficult ideas into simple steps, use examples, and help the student learn "
            "without rushing. If the user asks for homework help, provide guidance and explanations "
            "without giving direct answers that replace learning."
        )

        try:
            with st.chat_message("user"):
                st.markdown(cleaned_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": study_prompt},
                            *conversation,
                        ],
                    )
                answer = (response.choices[0].message.content or "").strip()

                if not answer:
                    st.warning("The study agent returned an empty response. Please try again.")
                else:
                    st.markdown(answer)
                    st.session_state.messages = [
                        *conversation,
                        {"role": "assistant", "content": answer},
                    ]
        except OpenAIError as error:
            st.error(f"Could not get an answer from Gemini: {error}")
