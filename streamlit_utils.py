import streamlit as st
import datetime as dt
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def reset_date_filter():
    st.session_state['dates'] = {"start_date": dt.date(2023, 1, 1), "end_date": dt.date.today()}

def select_date_filter():
    if "dates" not in st.session_state:
        reset_date_filter()
    
    start_date = st.sidebar.date_input(
        "Start date (earliest 26-08-2021)", 
        value=st.session_state['dates']["start_date"], 
        min_value=dt.date(2021, 1, 1), 
        max_value=dt.date.today(),  # Adjusted to use today's date for the max_value
    )

    end_date = st.sidebar.date_input(
        "End date (latest: 00:00:00 today)", 
        value=st.session_state['dates']["end_date"], 
        min_value=dt.date(2021, 1, 1), 
        max_value=dt.date.today(),
    )
    st.session_state['dates']['start_date'] = start_date
    st.session_state['dates']['end_date'] = end_date
    
    st.sidebar.button(
        label="Reset date filter",
        on_click = reset_date_filter
    )
    if end_date < start_date:
        st.sidebar.error("End date cannot be before start date.")
        # Optionally, you could reset the end_date to start_date or vice versa to ensure it's a valid range.
    return start_date, end_date

def clean_dataframe(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], format='mixed', errors='coerce').dt.tz_localize(None)
    elif 'join_date' in df.columns:  # Adjusted to elif to handle 'join_date' specifically
        df['join_date'] = pd.to_datetime(df['join_date'], format='mixed', errors='coerce').dt.tz_localize(None)
    if 'username' in df.columns:
        df['username'] = df['username'].str.lower()
    if 'from' in df.columns:
        df['from'] = df['from'].str.lower()
    # Define table-specific sorting configurations
    sort_config = {
        'chat_messages': [('msg_id', False)],
        'chat_reactions': [('msg_id', False), ('reaction_id', False)],
        'tpl_events': [('datetime', False), ('username', True)]
    }
    if table_name in sort_config:
        sort_by = sort_config[table_name]
        df = df.sort_values(by=[col for col, _ in sort_by], ascending=[asc for _, asc in sort_by]).reset_index(drop=True)
    
    return df

def select_timescale():
    if 'selected_timescale' not in st.session_state:
        st.session_state['selected_timescale'] = st.sidebar.radio("Select timescale for analysis", ["Week", "Month", "Quarter"], index = 1)
    else:
        timescale_index_dict = {
            "Week": 0,
            "Month": 1,
            "Quarter": 2
        }
        index = timescale_index_dict[st.session_state['selected_timescale']]
        st.session_state['selected_timescale'] = st.sidebar.radio("Select timescale for analysis", ["Week", "Month", "Quarter"], index = index)
    
    return st.session_state['selected_timescale']

def select_core_team():
    if 'core_team' not in st.session_state:
        st.session_state['core_team'] = st.sidebar.toggle(label='Include core team', value=False)
    else:
        st.session_state['core_team'] = st.sidebar.toggle(label='Include core team', value=st.session_state['core_team'])
    return st.session_state['core_team']

def select_score():
    st.sidebar.subheader("Scoring actions")
    event_score = st.sidebar.number_input('Event', value=10)
    message_score = st.sidebar.number_input('Message', value=2)
    reaction_score = st.sidebar.number_input('Reaction', value=1)

    scoring_system = {
        'event_count': event_score,
        'message_count': message_score,
        'reaction_count': reaction_score,
    }
    return scoring_system

def group_messages(msgs: pd.DataFrame):
    msgs = (msgs
            .groupby('from')
            .size()
            .reset_index(name='message_count')
            .sort_values(by='message_count', ascending = False)
            .rename({'from' : 'username'}, axis=1)
            )
    return msgs

def group_reactions(rxns: pd.DataFrame):
    rxns = (rxns
            .groupby('username')
            .size()
            .reset_index(name='reaction_count')
            .sort_values(by='reaction_count', ascending = False)
            )
    return rxns

def group_events(events: pd.DataFrame):
    events = (events
              .groupby('username')['participation']
              .sum()
              .reset_index()
              .sort_values(by='participation', ascending = False)
              .rename({'participation':'event_count'},axis=1)
              )
    return events
