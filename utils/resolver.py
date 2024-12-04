import json
import re
import unicodedata
import cloudscraper
import urllib.parse

tmdb_access_token = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0ZjliZDI0YzhiMjYyNWUyMzk2ZTNlZjg2YTg5ZmU0YyIsIm5iZiI6MTczMTc2MzI1MC42OTU1NjEyLCJzdWIiOiI2MjQwNTY0MWM3NDBkOTAwNDdhMzZjYzMiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.fbuA-ZrjBmdf7Ev8x5zDzK-wMzpO5CfyqoMJOOD91Xg'
darkiworld_url = 'https://darkiworld.xyz'

# Assurez-vous que ce module est installé et accessible
from resolverurl.hmf import HostedMediaFile

def get_primary_video_ids(scraper, title_id, referer, season_number=None, episode_number=None):
    title_url = f'{darkiworld_url}/api/v1/titles/{title_id}?loader=titlePage'
    headers = {
        'Accept': 'application/json',
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'x-xsrf-token': scraper.cookies.get('XSRF-TOKEN', '')
    }

    response = scraper.get(title_url, headers=headers)

    if response.status_code != 200:
        print(f"Échec de la requête pour le titre {title_id}. Code d'état: {response.status_code}")
        print("Détails de la réponse :", response.text)
        return None

    try:
        data = response.json()
        title = data.get('title', {})
        is_series = title.get('is_series', False)
        if is_series:
            id_liens = []
            if season_number is None:
                # Récupérer le numéro de saison par défaut ou la première saison disponible
                seasons = data.get('seasons', [])
                if seasons:
                    season_number = seasons[0].get('number', '1')
                else:
                    season_number = '1'  # Valeur par défaut si aucune saison n'est disponible
            page = 1
            found = False
            while not found:
                episodes_url = f'{darkiworld_url}/api/v1/titles/{title_id}/seasons/{season_number}/episodes?truncateDescriptions=true&staleTime=300000&query=&page={page}'
                episodes_response = scraper.get(episodes_url, headers=headers)
                if episodes_response.status_code != 200:
                    print(f"Échec de la requête pour les épisodes de la saison. Code d'état: {episodes_response.status_code}")
                    break
                episodes_data = episodes_response.json()
                # print(episodes_data)
                episodes_pagination = episodes_data.get('pagination')
                episodes_list = episodes_pagination.get('data', [])
                if not episodes_list:
                    break  # Plus d'épisodes disponibles, sortie de la boucle
                for episode in episodes_list:
                    ep_number = episode.get('episode_number', 0)
                    if episode_number is None or str(ep_number) == str(episode_number):
                        primary_video = episode.get('primary_video', {})
                        id_lien = primary_video.get('id_lien')
                        if id_lien:
                            id_liens.append({
                                'id_lien': id_lien,
                                'season': season_number,
                                'episode': ep_number
                            })
                            found = True
                            if episode_number is not None:
                                break  # Épisode trouvé, sortie de la boucle
                        else:
                            print(f"Clé 'id_lien' non trouvée pour l'épisode {ep_number} de la saison {season_number}")
                if found or episode_number is None:
                    break  # Épisode trouvé ou tous les épisodes récupérés
                else:
                    page += 1  # Passer à la page suivante
            return id_liens
        else:
            # Ce n'est pas une série, traiter comme un film
            primary_video = title.get('primary_video', {})
            id_lien = primary_video.get('id_lien')
            if id_lien:
                print(f"ID_LIEN trouvé: {id_lien}")
                return [{'id_lien': id_lien}]
            else:
                print("Clé 'id_lien' non trouvée dans la réponse JSON.")
                return None
    except ValueError:
        print("La réponse n'est pas un JSON valide.")
        return None

def download_video(scraper, id_lien):
    """
    Télécharge les informations du lien vidéo en gérant les cookies et le jeton CSRF.
    """
    # URL de téléchargement
    download_url = f'{darkiworld_url}/api/v1/download/{id_lien}'
    # URL de référence
    referer_url = f'{darkiworld_url}/download/{id_lien}'

    # Effectuer une première requête pour obtenir les cookies et le jeton CSRF
    initial_response = scraper.get(referer_url)
    if initial_response.status_code != 200:
        print(f"Échec de la requête initiale pour id_lien {id_lien}. Code d'état: {initial_response.status_code}")
        return None
    
    # Préparer les en-têtes avec le jeton CSRF
    headers = {
        'Accept': 'application/json',
        'Referer': referer_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        
    }

    # Extraire le jeton CSRF des cookies
    if 'XSRF-TOKEN' in scraper.cookies:
        xsrf_token = scraper.cookies['XSRF-TOKEN']
        headers['x-xsrf-token'] = xsrf_token
    else:
        print("Impossible de trouver le jeton XSRF-TOKEN dans les cookies.")

    

    # Effectuer la requête de téléchargement avec les en-têtes et les cookies appropriés
    response = scraper.get(download_url, headers=headers)

    if response.status_code == 200:
        print(f"Requête de téléchargement réussie pour id_lien {id_lien}!")
        try:
            return response.json()
        except ValueError:
            print("La réponse de téléchargement n'est pas un JSON valide.")
            return None
    else:
        print(f"Échec de la requête de téléchargement pour id_lien {id_lien}. Code d'état: {response.status_code}")
        print("Détails de la réponse :", response.text)
        return None


def filter_video_data(download_data, season=None, episode=None):
    """
    Extrait les informations vidéo des données JSON, y compris la saison et l'épisode si c'est une série.
    """
    video_links = []

    # Déterminer si c'est une série ou un film
    is_series = False
    title_info = download_data.get('title', {})
    if title_info:
        is_series = title_info.get('is_series', False)

    # Traiter la vidéo principale
    primary_video = download_data.get('video', {})
    if primary_video:
        src = primary_video.get('src')
        if src:
            video_data = {
                'src': src,
                'language': primary_video.get('language'),
                'quality': primary_video.get('quality'),
            }
            if is_series:
                video_data['season'] = season or primary_video.get('saison')
                video_data['episode'] = episode or primary_video.get('episode')
            video_links.append(video_data)

    # Traiter les vidéos alternatives
    alternative_videos = download_data.get('alternative_videos', [])
    for alt_video in alternative_videos:
        src = alt_video.get('src')
        if src:
            video_data = {
                'src': src,
                'language': alt_video.get('language'),
                'quality': alt_video.get('quality'),
            }
            if is_series:
                video_data['season'] = season or alt_video.get('saison')
                video_data['episode'] = episode or alt_video.get('episode')
            video_links.append(video_data)

    return video_links

def extract_title_id_and_slug(url):
    pattern = r'/titles/(\d+)(?:/([^/]+))?'
    match = re.search(pattern, url)
    if match:
        title_id = match.group(1)
        slug = match.group(2)
        return title_id, slug
    else:
        return None, None

def get_media_direct_url(url):
    expected_link = None
    hmf = HostedMediaFile(url)
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

        output_link = {
            "url": direct_url,
            "language": "",
            "quality": "",
            "headers": headers
        }

        if 'season' in link and 'episode' in link:
            output_link['season'] = ""
            output_link['episode'] = ""

        expected_link = output_link
    else:
        print(f"Impossible de résoudre l'URL média pour src: {link['src']}")
    return expected_link

def filter_with_arguments(links, quality, language):
    expected_link = None
    if quality==None:
        link = links[0]
        hmf = HostedMediaFile(url=link['src'])
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

            output_link = {
                "url": direct_url,
                "language": link['language'],
                "quality": link['quality'],
                "headers": headers
            }

            if 'season' in link and 'episode' in link:
                output_link['season'] = link['season']
                output_link['episode'] = link['episode']

            expected_link = output_link
        else:
            print(f"Impossible de résoudre l'URL média pour src: {link['src']}")
    else :
        for link in links:
            # Filtrer par qualité
            link_quality = link.get('quality', '').lower()
            link_language = link.get('language', '').lower()
            if quality:
                if quality == '1080' and '1080' not in link_quality:
                    continue
                elif quality == '2160' and ('ultra' not in link_quality and '2160' not in link_quality):
                    continue
                elif quality == '720' and '720' not in link_quality:
                    continue
            if language:
                if language == 'fr' and 'fr' not in link_language and 'multi' not in link_language:
                    continue
                elif language == 'en' and 'en' not in link_language and 'multi' not in link_language:
                    continue
            hmf = HostedMediaFile(url=link['src'])
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

                output_link = {
                    "url": direct_url,
                    "language": link['language'],
                    "quality": link['quality'],
                    "headers": headers
                }

                if 'season' in link and 'episode' in link:
                    output_link['season'] = link['season']
                    output_link['episode'] = link['episode']

                expected_link = output_link
                # Puisque nous ne voulons que le premier correspondant à la qualité, nous sortons de la boucle
                break
            else:
                print(f"Impossible de résoudre l'URL média pour src: {link['src']}")
    return expected_link

def get_media_direct_links(tmdb_id, quality, language, season_number=None, episode_number=None):
    # Initialiser cloudscraper
    scraper = cloudscraper.create_scraper()

    tmdb_url = ''
    if season_number :
        tmdb_url = f'https://api.themoviedb.org/3/tv/{tmdb_id}?language=fr-FR'
    else :
        tmdb_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}?language=fr-FR'
    headers = {
        'Authorization': f'Bearer {tmdb_access_token}',
        'accept': 'application/json'
    }

    response = scraper.get(tmdb_url, headers=headers)
    if response.status_code != 200:
        print(f"Échec de la requête à TMDB pour tmdb_id {tmdb_id}. Code d'état: {response.status_code}")
        return None

    tmdb_data = response.json()
    title = tmdb_data.get('title')
    if not title:
        title = tmdb_data.get('name')

    print(f"Titre obtenu depuis TMDB: {title}")

    # Étape 2: Rechercher le titre sur DarkiWorld
    search_title = urllib.parse.quote(title)
    search_url = f'{darkiworld_url}/api/v1/search/{search_title}?loader=searchPage'
    headers = {
        'Accept': 'application/json',
        'Referer': f'{darkiworld_url}/search/{search_title}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    # Effectuer une première requête pour obtenir les cookies et le jeton CSRF
    initial_response = scraper.get(f'{darkiworld_url}/search/{search_title}')
    if initial_response.status_code != 200:
        print(f"Échec du chargement de la page de recherche pour le titre '{title}'. Code d'état: {initial_response.status_code}")
        return None

    # **NOUVEAU** : Visiter la page d'accueil pour initialiser les cookies
    homepage_response = scraper.get(f'{darkiworld_url}')
    if homepage_response.status_code != 200:
        print(f"Échec du chargement de la page d'accueil. Code d'état: {homepage_response.status_code}")
        return None

    # **Mise à jour** : Vérifier si le jeton XSRF-TOKEN est dans les cookies
    if 'XSRF-TOKEN' in scraper.cookies:
        xsrf_token = scraper.cookies['XSRF-TOKEN']
        # Ajouter le jeton CSRF aux en-têtes
        headers['x-xsrf-token'] = xsrf_token
    else:
        print("Impossible de trouver le jeton XSRF-TOKEN dans les cookies après la visite de la page d'accueil.")

    # Effectuer la requête de recherche
    response = scraper.get(search_url, headers=headers)
    if response.status_code != 200:
        print(f"Échec de la recherche pour le titre '{title}' sur DarkiWorld. Code d'état: {response.status_code}")
        return None

    search_data = response.json()
    results = search_data.get('results', [])
    if not results:
        print(f"Aucun résultat de recherche trouvé pour le titre '{title}' sur DarkiWorld.")
        return None

    # Étape 3: Trouver l'élément avec le même tmdb_id
    title_id = None
    for item in results:
        if str(item.get('tmdb_id')) == str(tmdb_id):
            title_id = item.get('id')
            break

    if not title_id:
        print(f"Aucun titre correspondant trouvé sur DarkiWorld pour tmdb_id {tmdb_id}.")
        return None

    print(f"Title ID trouvé sur DarkiWorld: {title_id}")

    # Étape 4: Construire l'URL du titre
    formatted_title = title.lower()
    # Supprimer les accents
    formatted_title = ''.join(
        (c for c in unicodedata.normalize('NFD', formatted_title) if unicodedata.category(c) != 'Mn')
    )
    # Remplacer les espaces par des tirets
    formatted_title = formatted_title.replace(' ', '-')
    # Supprimer les deux-points, apostrophes, virgules
    formatted_title = formatted_title.replace(':', '').replace("'", '').replace(',', '')

    url = f'{darkiworld_url}/titles/{title_id}/{formatted_title}'
    print(f"URL construite: {url}")

    # Étape 5: Obtenir les id_lien
    id_liens = get_primary_video_ids(scraper, title_id, url, season_number, episode_number)
    if not id_liens:
        print("Impossible d'obtenir les id_lien. Fin du script.")
        return

    video_links = None

    # Étape 6: Pour chaque id_lien, faire la requête de téléchargement
    for item in id_liens:
        id_lien = item['id_lien']
        season = item.get('season')
        episode = item.get('episode')
        download_data = download_video(scraper, id_lien)
        if not download_data:
            print(f"Aucune donnée de téléchargement disponible pour id_lien {id_lien}.")
            continue

        # Étape 7: Filtrer les données
        video_links = filter_video_data(download_data, season, episode)
        if not video_links:
            print(f"Aucune donnée filtrée disponible pour id_lien {id_lien}.")
            continue

    expected_link = filter_with_arguments(video_links, quality, language)

    if expected_link:
        return expected_link
    else : 
        expected_link = None
        if quality=='2160':
            expected_link = filter_with_arguments(video_links, '1080', language)
        elif quality=='1080':
            expected_link = filter_with_arguments(video_links, '720', language)
        if not expected_link : 
            expected_link = filter_with_arguments(video_links, None, language) 
    return expected_link


# tmdb_id = 1726  # Exemple pour le film Titanic
# quality = '1080'  # Qualité souhaitée (1080, 2160, 720)
# language = 'fr'
# season_number = 1  # Facultatif, pour les séries
# episode_number = 1  # Facultatif, pour les séries

# lien_video = get_media_direct_links(tmdb_id, quality, None, None, language)
