import requests

def call_api():
    url = "http://192.168.1.28:8000/api/teams/send-report/"  # Đúng API cần gửi Teams
    try:
        response = requests.post(url, timeout=10)  # POST, không phải GET
        response.raise_for_status()
        print("API response:", response.status_code, response.text)
    except requests.exceptions.RequestException as e:
        print("Request error:", e)
    except Exception as e:
        print("Unexpected error:", e)
