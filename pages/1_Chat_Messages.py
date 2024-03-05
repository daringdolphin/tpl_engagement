import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
from streamlit_utils import select_date_filter, select_timescale, select_core_team, clean_dataframe
from db_utils import get_data

st.title("Chat Messages")
core_team = select_core_team()
selected_timescale = select_timescale()
start_date, end_date = select_date_filter()

msgs = pd.DataFrame(get_data('chat_messages', st.session_state.get('cache_clear_counter', 0)))
member_list = pd.DataFrame(get_data('member_list', st.session_state.get('cache_clear_counter', 0)))


if not core_team:
    msgs = msgs[~msgs['from_id'].isin(member_list[member_list['is_mgmt']]['user_id'])]
 

msgs = clean_dataframe(msgs, 'chat_messages')
filtered_msgs = msgs[(msgs['datetime'].dt.date > start_date) & (msgs['datetime'].dt.date < end_date)]

timescale_freq_dict = {
"Week": "W",
"Month": "M",
"Quarter":"Q"
}
timescale = filtered_msgs['datetime'].dt.to_period(timescale_freq_dict[selected_timescale])
if selected_timescale == "Week":
    timescale = filtered_msgs['datetime'].dt.strftime('%Y-W%V')

aggfuncs = {
    'msg_id': 'count',
    'from_id': 'nunique',
    'reply_to_message_id': 'count'
}

plot = (filtered_msgs
        .groupby(by=timescale)
        .agg(aggfuncs)
        .reset_index()
        .rename({
            'datetime': selected_timescale,
            'msg_id': 'messages',
            'from_id': 'unique senders',
            'reply_to_message_id': 'replies'
        },
            axis=1
        ))
plot[selected_timescale] = plot[selected_timescale].astype(str)

fig = px.line(plot, 
              x=plot[str(selected_timescale)].astype(str), 
              y=['messages', 'replies'])

fig.update_xaxes(
    tickangle=-45,  # Rotate labels for better readability
    tickmode='array',  # Use a custom array for tick labels
    tickvals=plot[selected_timescale],  # Specify the positions of the ticks
    ticktext=[str(val) for val in plot[selected_timescale]],  # Custom text for each tick
)
st.plotly_chart(fig)
st.write(plot)

# with st.expander:
#     as
st.write(filtered_msgs)


refresh_key = 'refresh_key'
if st.sidebar.button('Refresh Data', key=refresh_key):
    if 'cache_clear_counter' not in st.session_state:
        st.session_state['cache_clear_counter'] = 0
    st.session_state['cache_clear_counter'] += 1