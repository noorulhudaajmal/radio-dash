import streamlit as st
import pandas as pd
import datetime
import time
import pytz
import requests
import math
from PIL import Image
import io
import base64
import random

# Set page config to wide mode and page title
st.set_page_config(
    page_title="KLKT Radio Station Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main {
        padding: 0rem 0rem;
    }
    .block-container {
        padding: 0;
        margin-top: 20px;
    }
    .stApp {
        background-color: #13151a;
        color: white;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    .announcement-box {
        background-color: #1e2130;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
    }
    .alert-box {
        background-color: #7e57c2;
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: center;
        animation: pulse 1.5s infinite;
    }
    .underwriting-alert {
        background-color: #ff9800;
    }
    .psa-alert {
        background-color: #4caf50;
    }
    .station-id-alert {
        background-color: #2196f3;
    }
    .message-box {
        background-color: #1e2130;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 5px;
    }
    .title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        font-size: 18px;
        margin-bottom: 5px;
    }
    .time-display {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
    }
    .date-display {
        font-size: 24px;
        text-align: center;
        margin-bottom: 20px;
    }
    .weather-box {
        background-color: #1e2130;
        color: white;
        padding: 15px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .caller-container {
        display: flex;
        flex-direction: column;
    }
    .caller-box {
        background-color: #1e2130;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    .weekly-message {
        background-color: #303446;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
    }
    .schedule-box {
        background-color: #1e2130;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .schedule-item {
        display: flex;
        justify-content: space-between;
        padding: 5px 0;
        border-bottom: 1px solid #2d3142;
    }
    .schedule-item.current {
        background-color: rgba(126, 87, 194, 0.3);
        border-radius: 5px;
        padding: 5px;
    }
    .special-day {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .special-day-icon {
        margin-right: 8px;
        font-size: 18px;
    }
    .legal-id {
        background-color: #ff5722;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
        text-align: center;
        font-weight: bold;
    }
    .upcoming-event {
        background-color: #673ab7;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    hr {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Function to get local time in central time zone
def get_current_time():
    central = pytz.timezone('US/Central')
    return datetime.datetime.now(central)

# Function to calculate time until next announcement
def time_until_next(hour, minute):
    now = get_current_time()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target <= now:
        target += datetime.timedelta(hours=1)

    time_diff = target - now
    return time_diff, target

# Function to determine next announcement details
def get_next_announcement():
    now = get_current_time()
    current_hour = now.hour
    current_minute = now.minute

    # Calculate time until next announcements
    time_until_20, target_20 = time_until_next(current_hour, 20)
    time_until_30, target_30 = time_until_next(current_hour, 30)
    time_until_40, target_40 = time_until_next(current_hour, 40)
    time_until_00, target_00 = time_until_next((current_hour + 1) % 24, 0)

    # Find the next announcement
    announcements = [
        (time_until_20, "Underwriting", target_20, "underwriting-alert"),
        (time_until_30, "PSA", target_30, "psa-alert"),
        (time_until_40, "Underwriting", target_40, "underwriting-alert"),
        (time_until_00, "Station ID", target_00, "station-id-alert")
    ]

    announcements.sort(key=lambda x: x[0])
    return announcements[0]

# Function to get underwriter for specific time slot
def get_underwriter(hour, minute, underwriters_df):
    day_of_week = get_current_time().weekday()  # 0 is Monday, 6 is Sunday
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    current_day = days[day_of_week]

    if minute == 20:
        slot = f"{hour:02d}:20"
    elif minute == 40:
        slot = f"{hour:02d}:40"
    else:
        return "Unknown"

    # In a real implementation, you would fetch this from your spreadsheet
    # This is a placeholder that randomly selects an underwriter
    if len(underwriters_df) > 0:
        return random.choice(underwriters_df['Underwriter Name'].tolist())
    return "Unknown Underwriter"

# Function to get PSA for specific time slot
def get_psa(hour, underwriters_df):
    # In a real implementation, you would fetch this from your spreadsheet
    # This is a placeholder
    return "Community Announcement"

# Function to format time difference for display
def format_time_diff(time_diff):
    total_seconds = time_diff.total_seconds()
    minutes = math.floor(total_seconds / 60)
    seconds = math.floor(total_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# Function to check if we're in the alert window (3 minutes before to 3 minutes after)
def is_alert_window(target_time):
    now = get_current_time()
    alert_start = target_time - datetime.timedelta(minutes=3)
    alert_end = target_time + datetime.timedelta(minutes=3)
    return alert_start <= now <= alert_end

# Load schedule data
def load_schedule_data():
    schedule = [
        {"time": "10:00", "program": "Lions Radio - LHS"},
        {"time": "12:00", "program": "Blue Plate Special - Peabody and Jones"},
        {"time": "13:00", "program": "Good Texas Music - Max Landry"},
        {"time": "15:00", "program": "Sacred Nano - DJ Yeena Davis"}
    ]
    return schedule

# Load special days data
def load_special_days():
    special_days = [
        {"icon": "🌍", "name": "World Healing Day"},
        {"icon": "☢️", "name": "International Chernobyl Disaster Remembrance Day"},
        {"icon": "🎨", "name": "World Intellectual Property Day"},
        {"icon": "👽", "name": "Alien Day"},
        {"icon": "💉", "name": "World Immunization Week"},
        {"icon": "📚", "name": "Independent Bookstore Day"}
    ]
    return special_days

# Load upcoming events
def load_upcoming_events():
    events = [
        {
            "title": "KLKT Movie night! Faders Up: The John Aielli Experience",
            "date": "04/25/25",
            "time": "7:00 pm - 10:00 pm",
            "location": "at the Baker",
            "note": "Official KLKT Event!"
        }
    ]
    return events

# Mock data for testing (replace these with your actual data sources)
def load_underwriters_data():
    # In a real implementation, you would fetch this from Google Sheets
    data = {
        'Underwriter Name': ['Settlers', 'Bevies', 'Best Little', 'Porter', 'Central Texas CSA',
                             'Mario\'s', 'RBFCU', 'First Lockhart', 'Courthouse Nights'],
        'Package Level': ['*Special*', 'Platinum', 'Silver', 'Monthly 60', 'Monthly 107',
                          'Gold', 'Platnum', 'Silver', '*Special*'],
        'Weekly Play Count': [20, 16, 4, 4, 6, 7, 16, 4, 14]
    }
    return pd.DataFrame(data)

def load_messages_data():
    # In a real implementation, you would fetch this from Google Sheets
    data = {
        'message': ['This is where the message to the host goes.'],
        'weekly message': ['This is where our studio updates go'],
        'caller 1': ['Sam in Bastrop'],
        'caller 2': ['Bob in Cleveland'],
        'caller 3': ['Teddy in Ohio'],
        'caller 4': ['Jill in Oakland'],
        'caller 5': ['Renee in Lockhart']
    }
    return pd.DataFrame(data)

# Mock weather data (replace with actual API call)
def get_weather_data():
    # In a real implementation, use a weather API like OpenWeatherMap
    return {
        'location': 'Lockhart, TX',
        'temperature': 78,
        'condition': 'Partly Cloudy',
        'icon': '🌤️',
        'forecast': [
            {'day': 'Today', 'high': 82, 'low': 65, 'condition': '🌤️'},
            {'day': 'Tomorrow', 'high': 85, 'low': 67, 'condition': '☀️'},
            {'day': 'Monday', 'high': 80, 'low': 62, 'condition': '🌧️'}
        ]
    }

# Function to find current show
def get_current_show(schedule):
    now = get_current_time()
    current_hour = now.hour
    current_minute = now.minute
    current_time = current_hour * 100 + current_minute  # Convert to numeric format for comparison

    for i, show in enumerate(schedule):
        show_time = int(show["time"].replace(":", ""))
        next_show_time = int(schedule[(i+1) % len(schedule)]["time"].replace(":", "")) if i < len(schedule) - 1 else 2400

        if show_time <= current_time < next_show_time:
            return i

    return 0  # Default to first show if none match

# Load data
underwriters_df = load_underwriters_data()
messages_df = load_messages_data()
weather_data = get_weather_data()
schedule_data = load_schedule_data()
special_days = load_special_days()
upcoming_events = load_upcoming_events()

# Create dashboard layout
col1, col2, col3 = st.columns([2, 1, 1])

# Main column - Announcements and Time
with col1:
    # Time and Date display
    current_time = get_current_time()

    st.markdown(f"""
    <div class="time-display">{current_time.strftime('%I:%M:%S %p')}</div>
    <div class="date-display">{current_time.strftime('%A, %B %d, %Y')}</div>
    """, unsafe_allow_html=True)

    # Announcement display
    next_announcement = get_next_announcement()
    time_diff, announcement_type, target_time, alert_class = next_announcement

    # Check if we're in the alert window
    if is_alert_window(target_time):
        # Show alert
        hour = target_time.hour
        minute = target_time.minute

        if announcement_type == "Underwriting":
            underwriter = get_underwriter(hour, minute, underwriters_df)
            st.markdown(f"""
            <div class="alert-box {alert_class}">
                <div class="title">⚠️ UNDERWRITING ANNOUNCEMENT NOW ⚠️</div>
                <div class="subtitle">{target_time.strftime('%I:%M %p')}</div>
                <div style="font-size: 32px; font-weight: bold; margin-top: 10px;">{underwriter}</div>
            </div>
            """, unsafe_allow_html=True)
        elif announcement_type == "PSA":
            psa = get_psa(hour, underwriters_df)
            st.markdown(f"""
            <div class="alert-box {alert_class}">
                <div class="title">⚠️ PUBLIC SERVICE ANNOUNCEMENT NOW ⚠️</div>
                <div class="subtitle">{target_time.strftime('%I:%M %p')}</div>
                <div style="font-size: 32px; font-weight: bold; margin-top: 10px;">{psa}</div>
            </div>
            """, unsafe_allow_html=True)
        else:  # Station ID
            st.markdown(f"""
            <div class="alert-box {alert_class}">
                <div class="title">⚠️ STATION ID NOW ⚠️</div>
                <div class="subtitle">{target_time.strftime('%I:%M %p')}</div>
                <div style="font-size: 32px; font-weight: bold; margin-top: 10px;">KLKT 96.1 FM</div>
                <div class="legal-id" style="margin-top: 10px; font-size: 18px;">
                    "You're listening to KLKT-LP, 107.9, Lockhart"
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Show countdown
        st.markdown(f"""
        <div class="announcement-box">
            <div class="title">Next Announcement</div>
            <div class="subtitle">{announcement_type} at {target_time.strftime('%I:%M %p')}</div>
            <div style="font-size: 32px; font-weight: bold; margin-top: 10px;">
                {format_time_diff(time_diff)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Station ID Legal Text
    st.markdown(f"""
    <div class="legal-id">
        <div class="subtitle">LEGAL STATION ID:</div>
        "You're listening to KLKT-LP, 107.9, Lockhart"
    </div>
    """, unsafe_allow_html=True)

    # Producer message to host
    st.markdown('<div class="title" style="margin-top: 15px;">Producer Message</div>', unsafe_allow_html=True)

    message = messages_df['message'].iloc[0] if not messages_df.empty else "No messages at this time."
    st.markdown(f"""
    <div class="message-box" style="font-size: 24px; min-height: 100px;">
        {message}
    </div>
    """, unsafe_allow_html=True)

    # Weekly studio updates
    weekly_message = messages_df['weekly message'].iloc[0] if not messages_df.empty else "No weekly updates."
    st.markdown(f"""
    <div class="weekly-message">
        <div class="subtitle">Weekly Studio Updates</div>
        {weekly_message}
    </div>
    """, unsafe_allow_html=True)

    # Upcoming events
    if upcoming_events:
        st.markdown('<div class="title" style="margin-top: 15px;">Upcoming Events</div>', unsafe_allow_html=True)

        for event in upcoming_events:
            st.markdown(f"""
            <div class="upcoming-event">
                <div style="font-weight: bold; font-size: 20px;">{event['title']}</div>
                <div>{event['date']} @ {event['time']}</div>
                <div>{event['location']}</div>
                <div style="font-style: italic; margin-top: 5px;">{event['note']}</div>
            </div>
            """, unsafe_allow_html=True)

# Right column - Weather, Schedule, and Callers
with col2:
    # Special days
    st.markdown('<div class="title">Today\'s Special</div>', unsafe_allow_html=True)

    special_days_html = ""
    for day in special_days:
        special_days_html += f"""
        <div class="special-day">
            <span class="special-day-icon">{day['icon']}</span>
            <span>{day['name']}</span>
        </div>
        """


    st.html(f"""
    <div class="message-box">
        {special_days_html}
    </div>
    """)

    # Schedule
    st.markdown('<div class="title" style="margin-top: 15px;">Today\'s Schedule</div>', unsafe_allow_html=True)

    current_show_index = get_current_show(schedule_data)

    schedule_html = ""
    for i, show in enumerate(schedule_data):
        # Format time for display (10:00 instead of 1000)
        display_time = show["time"]
        if ":" not in display_time:
            display_time = f"{display_time[:len(display_time)-2]}:{display_time[-2:]}"

        class_name = "schedule-item current" if i == current_show_index else "schedule-item"

        schedule_html += f"""
        <div class="{class_name}">
            <span>{display_time}</span>
            <span style="flex-grow: 1; margin-left: 15px;">{show['program']}</span>
        </div>
        """

    st.html(f"""
    <div class="schedule-box">
        {schedule_html}
    </div>
    """)

with col3:
    # Weather display
    st.markdown('<div class="title" style="margin-top: 15px;">Weather</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="weather-box">
        <div style="font-size: 32px;">{weather_data['icon']} {weather_data['temperature']}°F</div>
        <div>{weather_data['condition']}</div>
        <div>{weather_data['location']}</div>
        <hr style="width: 100%;">
        <div style="width: 100%;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{weather_data['forecast'][0]['day']}</span>
                <span>{weather_data['forecast'][0]['condition']} {weather_data['forecast'][0]['high']}°/{weather_data['forecast'][0]['low']}°</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span>{weather_data['forecast'][1]['day']}</span>
                <span>{weather_data['forecast'][1]['condition']} {weather_data['forecast'][1]['high']}°/{weather_data['forecast'][1]['low']}°</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span>{weather_data['forecast'][2]['day']}</span>
                <span>{weather_data['forecast'][2]['condition']} {weather_data['forecast'][2]['high']}°/{weather_data['forecast'][2]['low']}°</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Callers list
    st.markdown('<div class="title" style="margin-top: 15px;">Callers</div>', unsafe_allow_html=True)

    caller_cols = [col for col in messages_df.columns if col.startswith('caller')]

    for col in caller_cols:
        if not messages_df.empty and not pd.isna(messages_df[col].iloc[0]):
            caller = messages_df[col].iloc[0]
            st.markdown(f"""
            <div class="caller-box">
                <strong>{col.replace('_', ' ').title()}:</strong> {caller}
            </div>
            """, unsafe_allow_html=True)


# Auto-refresh the page
st.markdown("""
<script>
    setTimeout(function(){
        window.location.reload();
    }, 1000);
</script>
""", unsafe_allow_html=True)

# Add the auto-refresh functionality
auto_refresh = st.empty()
placeholder = st.empty()

# Add radio station logo at bottom
st.markdown("""
<div style="margin-top: 20px; text-align: center;">
    <h1>KLKT 107.9 FM</h1>
    <p>Live Studio Dashboard</p>
</div>
""", unsafe_allow_html=True)

# def main():
#     while True:
#         # Update at 1-second intervals
#         time.sleep(1)
#         st.experimental_rerun()
#
# if __name__ == "__main__":
#     main()