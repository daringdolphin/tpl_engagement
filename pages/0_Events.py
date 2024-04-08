import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
from streamlit_utils import select_date_filter, select_timescale, select_core_team, clean_dataframe
from db_utils import get_data

st.title("Events")
core_team = select_core_team()
start_date, end_date = select_date_filter()

events = clean_dataframe(get_data('tpl_events', st.session_state.get('cache_clear_counter', 0)), 'tpl_events')
member_list = get_data('member_list', st.session_state.get('cache_clear_counter', 0))

events['username'] = events['username'].str.lower()

if not core_team:
    events = events[~events['user_id'].isin(member_list[member_list['is_mgmt']]['user_id'])]


filtered_events = events[(events['datetime'].dt.date > start_date) & (events['datetime'].dt.date < end_date)]

event_participation = filtered_events.pivot_table(
    index="username",
    columns="event_name",
    values="participation"
).reset_index().fillna(0)

event_participation.columns.name = None
event_participation['Total events'] = (sum(event_participation[event] for event in filtered_events['event_name'].unique()))
event_participation = event_participation.sort_values(by=["Total events", "username"], ascending=[False, True]).reset_index(drop=True)

col1, col2 = st.columns([1,4])
with col1:
    min_score = st.number_input("Total events attended", min_value=0, max_value=int(event_participation['Total events'].max()), value=1)

st.write(event_participation[event_participation["Total events"] >= min_score])


refresh_key = 'refresh_key'
if st.sidebar.button('Refresh Data', key=refresh_key):
    if 'cache_clear_counter' not in st.session_state:
        st.session_state['cache_clear_counter'] = 0
    st.session_state['cache_clear_counter'] += 1


