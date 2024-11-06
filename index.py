from flask import Flask, request, jsonify
from resolverurl.hmf import HostedMediaFile
import urllib.parse

app = Flask(__name__)

@app.route('/resolve')
def resolve_url():
    # Obtenir l'URL de base à partir des paramètres de requête
    base_url = request.args.get('url')
    if not base_url:
        return jsonify({"error": "URL parameter is required"}), 400

    # Créer une instance de HostedMediaFile avec l'URL donnée
    hmf = HostedMediaFile(url=base_url)

    # Résoudre l'URL pour obtenir le lien direct vers le média
    media_url = hmf.resolve()

    if media_url:
        # Extraire User-Agent, Referer, etc. de l'URL résolue si nécessaire
        url_parts = media_url.split('|')
        direct_url = url_parts[0]
        headers = {}

        # Analyser les en-têtes additionnels, si présents
        if len(url_parts) > 1:
            header_params = url_parts[1].split('&')
            for param in header_params:
                key, value = param.split('=')
                headers[key.replace('-', '_')] = urllib.parse.unquote(value)

        # Retourner les données sous forme de JSON
        return jsonify({"url": direct_url, "headers": headers})

    # En cas d'échec de la résolution, renvoyer une erreur 404
    return jsonify({"error": "Failed to resolve the media URL"}), 404
