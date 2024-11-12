from flask import Flask, request, jsonify
import request
import urllib.parse

app = Flask(__name__)

@app.route('/resolve')
def resolve_url():
    # Obtenir l'URL de base à partir des paramètres de requête
    base_url = request.args.get('url')
    if not base_url:
        return jsonify({"error": "URL parameter is required"}), 400

    # Résoudre l'URL pour obtenir le lien direct vers le média
    media_urls = request.get_media_direct_links(base_url)

    if media_urls:
        return jsonify(media_urls)

    # En cas d'échec de la résolution, renvoyer une erreur 404
    return jsonify({"error": "Failed to resolve the media URL"}), 404
