from flask import Flask, request, Response
from resolverurl.hmf import HostedMediaFile
import urllib.parse

app = Flask(__name__)

@app.route('/resolve')
def resolve_url():
    # Obtenir l'URL de base à partir des paramètres de requête
    base_url = request.args.get('url')
    if not base_url:
        return "Error: URL parameter is required", 400

    # Créer une instance de HostedMediaFile avec l'URL donnée
    hmf = HostedMediaFile(url=base_url)

    # Résoudre l'URL pour obtenir le lien direct vers le média
    media_url = hmf.resolve()

    if media_url:
        # Extraire User-Agent, Referer, etc. de l'URL résolue si nécessaire
        # Exemple : https://example.com/video.mp4|User-Agent=...&Referer=...
        url_parts = media_url.split('|')
        direct_url = url_parts[0]
        headers = {}

        # Analysez les en-têtes additionnels, si présents
        if len(url_parts) > 1:
            header_params = url_parts[1].split('&')
            for param in header_params:
                key, value = param.split('=')
                headers[key.replace('-', '_')] = urllib.parse.unquote(value)

        # Générer le contenu du fichier M3U
        m3u_content = "#EXTM3U\n"
        m3u_content += "#EXTINF:-1,%s\n" % base_url  # Vous pouvez personnaliser le titre
        for key, value in headers.items():
            # VLC utilise des options spécifiques pour les en-têtes HTTP
            if key.lower() == 'user_agent':
                m3u_content += '#EXTVLCOPT:http-user-agent=%s\n' % value
            elif key.lower() == 'referer':
                m3u_content += '#EXTVLCOPT:http-referrer=%s\n' % value
            elif key.lower() == 'cookie':
                m3u_content += '#EXTVLCOPT:http-cookie=%s\n' % value
            elif key.lower() == 'origin':
                m3u_content += '#EXTVLCOPT:http-origin=%s\n' % value
            else:
                # Pour d'autres en-têtes, utilisez http-header personnalisé
                m3u_content += '#EXTVLCOPT:http-header=%s=%s\n' % (key, value)
        m3u_content += '%s\n' % direct_url

        # Retourner le contenu M3U avec le type de contenu approprié
        return Response(m3u_content, mimetype='audio/mpegurl')

    # En cas d'échec de la résolution, renvoyer une erreur 404
    return "Failed to resolve the media URL.", 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

