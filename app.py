import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
from streamlit_feedback import streamlit_feedback


import weave


class WritingResponse(BaseModel):
    commentary: Optional[str]
    retwritten_text: Optional[str]


weave_client = weave.init('writing-assistant')


class WritingAssistantModel(weave.Model):
    last_call_id: Optional[str] = None

    @weave.op()
    def predict(self, writing_guidelines, text):
        openai_client = OpenAI()
        response = openai_client.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system",
                    "content": f"You are a helpful assistant that improves writing"},
                {"role": "user", "content": f"""Update and improve the following text using the following guidelines:
                GUIDELINES:
                    {writing_guidelines}
                TEXT:
                    {text}
                """
                 }
            ],
            n=1,
            response_format=WritingResponse
        )
        print("LCID@PREDICT", weave.get_current_call().id)
        self.last_call_id = weave.get_current_call().id
        resp = response.choices[0].message.parsed
        return resp.retwritten_text


model = WritingAssistantModel()


def handle_feedback(feedback: dict):
    last_call = weave_client.call(st.session_state['last_call_id'])

    if 'score' in feedback:
        last_call.feedback.add_reaction(feedback['score'])
    if 'text' in feedback and feedback['text'] != None:
        last_call.feedback.add_note(feedback['text'])
    # model.last_call.feedback.add_note("👍")

    st.toast("✔️ Feedback received!")


def main():
    st.title("Improve Writing")

    writing_guidelines = get_prompt_from_file('clarity.txt')

    # Input text box
    user_input = st.text_area("Enter text here:", "", height=250)

    if st.button("Improve Writing"):
        if user_input.strip():

            # Call OpenAI API to improve writing
            improved_text = model.predict(writing_guidelines, user_input)
            st.session_state['improved_text'] = improved_text
            st.session_state['last_call_id'] = model.last_call_id

        else:
            improved_text = None
            st.warning("Please enter some text to check.")

    if 'improved_text' in st.session_state:
        st.text_area("Improved Text:",
                     st.session_state['improved_text'], height=250)

        feedback = streamlit_feedback(feedback_type="thumbs",
                                      optional_text_label="[Optional] Please provide an explanation",
                                      align="flex-start")
        if feedback:
            print("HERE")
            handle_feedback(feedback)

    with st.expander("View Writing Prompt"):
        st.text_area("Current Writing Prompt:", writing_guidelines, height=250)


def get_prompt_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Correct the grammar of the following text:\\n{text}\\n"


if __name__ == "__main__":
    main()
