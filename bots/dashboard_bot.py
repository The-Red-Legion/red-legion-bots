from flask import Flask, render_template, redirect
import psycopg2
import os
from datetime import timedelta

app = Flask(__name__, template_folder='/opt/render/project/src/templates')

def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def format_duration(seconds):
    td = timedelta(seconds=float(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

@app.route('/')
def index():
    return redirect('/dashboard', code=302)

@app.route('/dashboard')
def dashboard():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            SELECT e.event_name, e.channel_name, e.start_time, e.end_time, p.username, p.duration, p.is_org_member
            FROM events e
            JOIN participation p ON e.channel_id = p.channel_id
            ORDER BY p.is_org_member DESC, e.channel_name, e.start_time DESC
        ''')
        data = c.fetchall()
        conn.close()

        # Format data for display
        events = []
        for row in data:
            event_name, channel_name, start_time, end_time, username, duration, is_org_member = row
            events.append({
                'event_name': event_name,
                'channel_name': channel_name,
                'start_time': start_time,
                'end_time': end_time or 'Ongoing',
                'username': username or 'Unknown',
                'duration': format_duration(duration),
                'is_org_member': 'Yes' if is_org_member else 'No'
            })
        return render_template('dashboard.html', events=events)
    except psycopg2.OperationalError as e:
        print(f"Database error: {e}")
        return render_template('dashboard.html', events=[])

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)