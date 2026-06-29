import requests

url = "https://homeassistant.capital-labs.dev/api/webhook/-bx5tofcNJevp2m_KnWrNrlu9"

json = {
    "message": "It is cooked"
}

response = requests.post(url, json = json)

print(response.status_code)