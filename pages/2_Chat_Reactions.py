import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
from db_utils import get_data
from streamlit_utils import select_date_filter, select_timescale, select_core_team, clean_dataframe

st.title("Chat Reactions")
core_team = select_core_team()
selected_timescale = select_timescale()
start_date, end_date = select_date_filter()

rxns = pd.DataFrame(get_data('chat_reactions', st.session_state.get('cache_clear_counter', 0)))
member_list = pd.DataFrame(get_data('member_list', st.session_state.get('cache_clear_counter', 0)))

if not st.session_state['core_team']:
    rxns = rxns[~rxns['user_id'].isin(member_list[member_list['is_mgmt']]['user_id'])]

rxns=clean_dataframe(rxns, 'chat_reactions')
filtered_rxns = rxns[(rxns['datetime'].dt.date > start_date) & (rxns['datetime'].dt.date < end_date)]

timescale_freq_dict = {
    "Week": "W",
    "Month": "M",
    "Quarter":"Q"
}

timescale = filtered_rxns['datetime'].dt.to_period(timescale_freq_dict[selected_timescale])
if selected_timescale == "Week":
    timescale = filtered_rxns['datetime'].dt.strftime('%Y-W%V')

aggfuncs = {
    'reaction_id': 'count',
    'msg_id': 'nunique'
}

plot = (filtered_rxns
        .groupby(by=timescale)
        .agg(aggfuncs)
        .reset_index()
        .rename({
            'datetime': selected_timescale,
            'reaction_id': 'reactions',
            'msg_id': 'reacted_messages'
        },
            axis=1
            )
        )
plot[selected_timescale] = plot[selected_timescale].astype(str)


fig = px.line(plot, 
              x=plot[selected_timescale], 
              y=['reactions', 'reacted_messages'])

fig.update_xaxes(
    tickangle=-45,  # Rotate labels for better readability
    tickmode='array',  # Use a custom array for tick labels
    tickvals=plot[selected_timescale],  # Specify the positions of the ticks
    ticktext=[str(val) for val in plot[selected_timescale]],  # Custom text for each tick
)
st.plotly_chart(fig)

st.write(plot)


refresh_key = 'refresh_key'
if st.sidebar.button('Refresh Data', key=refresh_key):
    if 'cache_clear_counter' not in st.session_state:
        st.session_state['cache_clear_counter'] = 0
    st.session_state['cache_clear_counter'] += 1