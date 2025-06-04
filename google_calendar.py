import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Скоупи
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Де будемо зберігати токени
TOKEN_DIR = r'C:\Temp\tokens'
Path(TOKEN_DIR).mkdir(parents=True, exist_ok=True)

# Тут зберігатимемо flow об'єкти для юзерів
user_flows = {}

def generate_auth_url(user_id):
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'  # <-- Спеціальний редірект для ручного коду
    )
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
    user_flows[user_id] = flow  # Зберігаємо flow, щоб потім обробити код
    return auth_url

def save_user_token(user_id, auth_code):
    flow = user_flows.get(user_id)
    if not flow:
        raise Exception("No OAuth flow found for this user")
    flow.fetch_token(code=auth_code)
    creds = flow.credentials

    token_path = os.path.join(TOKEN_DIR, f'{user_id}_token.json')
    with open(token_path, 'w') as token_file:
        token_file.write(creds.to_json())
    return True

def get_calendar_service(user_id):
    token_path = os.path.join(TOKEN_DIR, f'{user_id}_token.json')
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    else:
        raise Exception("User not authorized yet")

    service = build('calendar', 'v3', credentials=creds)
    return service

def add_event_to_calendar(user_id, summary, description, start_time, end_time):
    service = get_calendar_service(user_id)

    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Europe/Kiev',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Europe/Kiev',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    return event.get('htmlLink')
