from flask import Flask, request, jsonify, redirect
from resolver import get_media_direct_links

app = Flask(__name__)

@app.route('/resolve')
def resolve_url():
    # Obtain parameters from query
    tmdb_id = request.args.get('tmdb_id')
    season = request.args.get('season')  # Corrected
    episode = request.args.get('episode')  # Corrected
    quality = request.args.get('quality')  # Corrected

    if not tmdb_id or not quality:  # Updated condition to ensure both are present
        return jsonify({"error": "Parameters 'tmdb_id' and 'quality' are required"}), 400

    try:
        # Fetch media URLs based on the presence of season and episode
        if season and episode:
            media_url = get_media_direct_links(tmdb_id, quality, season, episode)
        else:
            media_url = get_media_direct_links(tmdb_id, quality)

        # Redirect if a URL is successfully resolved
        if media_url:
            print(media_url)
            return redirect(media_url[0]['url'])  # Assuming we redirect to the first URL in the list

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    # If resolution fails, return a 404 error
    return jsonify({"error": "Failed to resolve the media URL"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
