import requests

response = requests.post(
    "https://frederic-lagniez-api-jenedai.hf.space/predict",
    json={
        "secteur_activite": "S1: Agriculture",
        "plage_de_puissance_souscrite": "P1: ]36-120] kVA",
        "nb_points_soutirage": 120.0,
        "ville": "Paris",
        "en_vacances": 0,
        "temperature_2m_mean": 18.5,
        "relative_humidity_mean": 70.0,
        "precipitation_sum": 2.0,
        "month": 7,
        "jour_semaine": 2,
    },
)

print("Status code:", response.status_code)
print("Headers:", response.headers)
print("Body brut:", response.text)

print(" Response :", response.json())
