import streamlit as st
from utils import *

st.title("Chatbot to manage schedules in Google Calendar")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# prompt 입력 후
if prompt := st.chat_input("궁금한 것을 물어보세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    intent, start_time, end_time, title = info_extractor(prompt)

    if intent == "일정 추가":        
        start_time_obj = datetime.datetime.fromisoformat(start_time)
        end_time_obj = datetime.datetime.fromisoformat(end_time)
        response = add_calendar_event(title, start_time_obj.isoformat(), end_time_obj.isoformat())

    elif intent == "일정 조회":
        start_time_obj = datetime.datetime.fromisoformat(start_time).isoformat() + 'Z'
        end_time_obj = datetime.datetime.fromisoformat(end_time).isoformat() + 'Z'
        response = get_calendar_events(start_time_obj, end_time_obj)

    elif intent == "일정 삭제":
        start_time_obj = datetime.datetime.fromisoformat(start_time).isoformat() + 'Z'
        response = delete_calendar_event(start_time) 

    else:
        response = generate_response(prompt)

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)                       