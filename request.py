import json
import cloudscraper
import sys
import urllib.parse

# Assurez-vous que ce module est installé et accessible
from resolverurl.hmf import HostedMediaFile

def get_primary_video_id(scraper, title_id):
    """
    Récupère l'id_lien primaire d'un titre donné.
    
    :param scraper: Instance de cloudscraper.Session
    :param title_id: ID du titre (ex: 26378)
    :return: id_lien ou None si non trouvé
    """
    title_url = f'https://darkiworld.me/api/v1/titles/{title_id}?loader=titlePage'
    headers = {
        'Accept': 'application/json',
        'Referer': f'https://darkiworld.me/titles/{title_id}/captain-america-first-avenger',  # Modifiez si nécessaire
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        # Ajoutez d'autres en-têtes si nécessaire
    }

    response = scraper.get(title_url, headers=headers)

    if response.status_code != 200:
        print(f"Échec de la requête pour le titre {title_id}. Code d'état: {response.status_code}")
        print("Détails de la réponse :", response.text)
        return None

    try:
        data = response.json()
        title = data.get('title', {})
        primary_video = title.get('primary_video', {})
        id_lien = primary_video.get('id_lien')
        if id_lien:
            print(f"ID_LIEN trouvé: {id_lien}")
            return id_lien
        else:
            print("Clé 'id_lien' non trouvée dans la réponse JSON.")
            return None
    except ValueError:
        print("La réponse n'est pas un JSON valide.")
        return None

def download_video(scraper, id_lien):
    """
    Télécharge les informations du lien vidéo primaire.
    
    :param scraper: Instance de cloudscraper.Session
    :param id_lien: ID du lien vidéo (ex: 16099874)
    :return: Contenu JSON de la réponse ou None
    """
    download_url = f'https://darkiworld.me/api/v1/download/{id_lien}'
    headers = {
        'Accept': 'application/json',
        'Referer': f'https://darkiworld.me/download/{id_lien}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        # Ajoutez d'autres en-têtes si nécessaire
    }

    response = scraper.get(download_url, headers=headers)

    if response.status_code == 200:
        print("Requête de téléchargement réussie !")
        try:
            return response.json()
        except ValueError:
            print("La réponse de téléchargement n'est pas un JSON valide.")
            return None
    else:
        print(f"Échec de la requête de téléchargement. Code d'état: {response.status_code}")
        print("Détails de la réponse :", response.text)
        return None

def filter_video_data(download_data):
    """
    Filtre les données JSON pour ne conserver que les champs souhaités.
    
    :param download_data: Données JSON de la réponse de téléchargement
    :return: Dictionnaire filtré
    """
    filtered_data = {}

    # Filtrer la vidéo principale
    primary_video = download_data.get('video', {})
    if primary_video:
        filtered_data['primary_video'] = {
            'src': primary_video.get('src'),
            'language': primary_video.get('language'),
            'quality': primary_video.get('quality')
        }

    # Filtrer les vidéos alternatives
    alternative_videos = download_data.get('alternative_videos', [])
    if alternative_videos:
        filtered_data['alternative_videos'] = []
        for alt_video in alternative_videos:
            filtered_video = {
                'src': alt_video.get('src'),
                'language': alt_video.get('language'),
                'quality': alt_video.get('quality')
            }
            filtered_data['alternative_videos'].append(filtered_video)

    return filtered_data

def get_media_direct_links(title_id):
    # Initialiser cloudscraper
    scraper = cloudscraper.create_scraper()

    # Étape 1: Obtenir l'id_lien primaire
    id_lien = get_primary_video_id(scraper, title_id)
    if not id_lien:
        print("Impossible d'obtenir l'id_lien primaire. Fin du script.")
        return

    # Étape 2: Faire la requête de téléchargement avec id_lien
    download_data = download_video(scraper, id_lien)
    if not download_data:
        print("Aucune donnée de téléchargement disponible. Fin du script.")
        return

    # Étape 3: Filtrer les données
    filtered_data = filter_video_data(download_data)
    if not filtered_data:
        print("Aucune donnée filtrée disponible.")
        return

    # Étape 4: Renvoyer les données filtrées sous forme de JSON
    output_json = json.dumps(filtered_data, ensure_ascii=False, indent=4)
    print("Données filtrées obtenues avec succès :")
    print(output_json)

    # Optionnel : Enregistrer les données filtrées dans un fichier JSON
    with open('filtered_video_links.json', 'w', encoding='utf-8') as f:
        f.write(output_json)
        print("Données filtrées enregistrées dans 'filtered_video_links.json'.")

    # Traitement supplémentaire : Extraction des liens vidéo avec HostedMediaFile
    video_links = []

    # Ajouter la vidéo principale
    if 'primary_video' in filtered_data:
        video = filtered_data['primary_video']
        hmf = HostedMediaFile(url=video['src'])
        media_url = hmf.resolve()
        if media_url:
            url_parts = media_url.split('|')
            direct_url = url_parts[0]
            headers = {}

            # Analyser les en-têtes additionnels, si présents
            if len(url_parts) > 1:
                header_params = url_parts[1].split('&')
                for param in header_params:
                    if '=' in param:
                        key, value = param.split('=', 1)
                        headers[key.replace('-', '_')] = urllib.parse.unquote(value)

            video_links.append({
                "url": direct_url,
                "language": video['language'],
                "quality": video['quality'],
                "headers": headers
            })

    # Ajouter les vidéos alternatives
    if 'alternative_videos' in filtered_data:
        for alt_video in filtered_data['alternative_videos']:
            hmf = HostedMediaFile(url=alt_video['src'])
            media_url = hmf.resolve()
            if media_url:
                url_parts = media_url.split('|')
                direct_url = url_parts[0]
                headers = {}
                if len(url_parts) > 1:
                    header_params = url_parts[1].split('&')
                    for param in header_params:
                        if '=' in param:
                            key, value = param.split('=', 1)
                            headers[key.replace('-', '_')] = urllib.parse.unquote(value)
                video_links.append({
                    "url": direct_url,
                    "language": alt_video['language'],
                    "quality": alt_video['quality'],
                    "headers": headers
                })

    # Renvoyer les liens vidéo avec langage et qualité sous forme de JSON
    final_output_json = json.dumps(video_links, ensure_ascii=False, indent=4)
    print("Liens vidéo avec langage et qualité :")
    print(final_output_json)
