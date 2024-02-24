import streamlit as st
import pandas as pd
from streamlit_utils import select_date_filter, clean_dataframe
from db_utils import get_data
from datetime import datetime

st.title("Raw data")
st.write("Interact with raw data here, or download as csv for your own analysis")
st.write(f"Last updated: {datetime.today().date()}")

with st.expander("TPL member list"):
    member_list = clean_dataframe(get_data('member_list'), 'member_list')
    st.write(member_list)

with st.expander("Chat messages"):
    chat_messages = clean_dataframe(get_data('chat_messages'), 'chat_messages')
    st.write(chat_messages)

with st.expander("Chat reactions"):
    chat_reactions = clean_dataframe(get_data('chat_reactions'), 'chat_reactions')
    st.write(chat_reactions)