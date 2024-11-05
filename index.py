from flask import Flask, request, Response, stream_with_context
from resolverurl.hmf import HostedMediaFile
import urllib.parse
import requests

app = Flask(__name__)

@app.route('/stream')
def stream_video():
    # Obtenir l'URL de base à partir des paramètres de requête
    base_url = request.args.get('url')
    if not base_url:
        return "Error: URL parameter is required", 400

    # Créer une instance de HostedMediaFile avec l'URL donnée
    hmf = HostedMediaFile(url=base_url)

    # Résoudre l'URL pour obtenir le lien direct vers le média
    media_url = hmf.resolve()

    if media_url:
        # Extraire l'URL directe et les en-têtes supplémentaires
        url_parts = media_url.split('|')
        direct_url = url_parts[0]
        headers = {}

        # Analysez les en-têtes additionnels, si présents
        if len(url_parts) > 1:
            header_params = url_parts[1].split('&')
            for param in header_params:
                key, value = param.split('=')
                headers[key.replace('-', '_')] = urllib.parse.unquote(value)

        # Fonction pour streamer le contenu
        def generate():
            with requests.get(direct_url, headers=headers, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=8192):
                    yield chunk

        # Déterminer le type de contenu à partir des en-têtes de la réponse
        content_type = 'application/octet-stream'
        response_headers = {}
        head = requests.head(direct_url, headers=headers)
        if 'Content-Type' in head.headers:
            content_type = head.headers['Content-Type']
        if 'Content-Length' in head.headers:
            response_headers['Content-Length'] = head.headers['Content-Length']

        # Retourner la réponse en streaming
        return Response(stream_with_context(generate()), headers=response_headers, content_type=content_type)
    else:
        return "Failed to resolve the media URL.", 404
