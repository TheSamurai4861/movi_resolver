import cloudscraper
import json

# Crée un scraper pour gérer Cloudflare et les cookies
scraper = cloudscraper.create_scraper()

# URL de la page d'origine
origin_url = "https://darkiworld.xyz/download-page/115280"

# URL de l'API pour la requête POST
api_url = "https://darkiworld.xyz/api/v1/download"

# Étape 1 : Effectuer une requête GET pour récupérer tous les cookies et jetons
response = scraper.get(origin_url)

# Vérifier si la requête GET est réussie
if response.status_code == 200:
    # Récupérer tous les cookies
    cookies = scraper.cookies.get_dict()

    # Extraire le jeton XSRF-TOKEN des cookies
    xsrf_token = cookies.get('XSRF-TOKEN')
    session_cookie = cookies.get('darkiworld_session')

    if not xsrf_token or not session_cookie:
        print("Erreur : Impossible de récupérer les cookies ou le jeton XSRF-TOKEN.")
        exit()

    print(f"Cookies récupérés : {cookies}")
    print(f"Jeton XSRF-TOKEN récupéré : {xsrf_token}")
else:
    print(f"Erreur lors de la récupération de la page d'origine : {response.status_code}")
    exit()

# Étape 2 : Préparer la requête POST
payload = {
    "id": 10152197  # Exemple d'ID
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "X-XSRF-TOKEN": xsrf_token,  # Utilisation du jeton récupéré
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Referer": origin_url,
    "Origin": "https://darkiworld.xyz"
}

# Étape 3 : Effectuer la requête POST avec tous les cookies
response_post = scraper.post(api_url, headers=headers, cookies=cookies, data=json.dumps(payload))

# Afficher le résultat
print(f"Code d'état : {response_post.status_code}")
print(f"Réponse : {response_post.text}")
