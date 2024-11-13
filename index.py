from flask import Flask, request, jsonify
from resolver import get_media_direct_links
import requests  # Renaming to avoid conflict

app = Flask(__name__)

@app.route('/resolve')
def resolve_url():
    # Obtain the base URL from query parameters
    base_url = request.args.get('url')
    if not base_url:
        return jsonify({"error": "URL parameter is required"}), 400

    # Resolve the URL to get the direct link to the media
    media_urls = get_media_direct_links(base_url)

    if media_urls:
        return jsonify(media_urls)

    # If resolution fails, return a 404 error
    return jsonify({"error": "Failed to resolve the media URL"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
