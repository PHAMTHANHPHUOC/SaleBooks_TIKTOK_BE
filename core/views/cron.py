import requests

def call_api():
    url = "https://tiktokapi.tinydaisycoloring.com/api/teams/send-report/"
    headers = {
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(url, json={}, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"✅ API called successfully. Status: {response.status_code}")
        print("Response:", response.text)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

