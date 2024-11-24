from flask import Flask, request, jsonify, redirect
from utils.resolver import get_media_direct_links

app = Flask(__name__)

@app.route('/stream')
def stream_media():
    # Obtain parameters from query
    tmdb_id = request.args.get('tmdb_id')
    season = request.args.get('season')
    episode = request.args.get('episode')
    quality = request.args.get('quality')
    language = request.args.get('language')

    if not tmdb_id or not quality or not language:  # Updated condition to ensure both are present
        return jsonify({"error": "Parameters 'tmdb_id', 'quality' and 'language' are required"}), 400

    try:
        # Fetch media URLs based on the presence of season and episode
        if season and episode:
            media_url = get_media_direct_links(tmdb_id, quality, season, episode, language)
        else:
            media_url = get_media_direct_links(tmdb_id, quality, language)

        # Redirect if a URL is successfully resolved
        if media_url:
            return redirect(media_url['url'])
        else : 
            return jsonify({"error" : "No media direct link for the requested media."}), 404

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
    
@app.route('/resolve')
def resolve_media():
    # Obtain parameters from query
    tmdb_id = request.args.get('tmdb_id')
    season = request.args.get('season')
    episode = request.args.get('episode')
    quality = request.args.get('quality')
    language = request.args.get('language')

    if not tmdb_id or not quality or not language:  # Updated condition to ensure both are present
        return jsonify({"error": "Parameters 'tmdb_id', 'quality' and 'language' are required"}), 400

    try:
        # Fetch media URLs based on the presence of season and episode
        if season and episode:
            media = get_media_direct_links(tmdb_id, quality, season, episode, language)
        else:
            media = get_media_direct_links(tmdb_id, quality, language)

        # Redirect if a URL is successfully resolved
        if media:
            return jsonify(media)
        else : 
            return jsonify({"error" : "No media direct link for the requested media."}), 404

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
