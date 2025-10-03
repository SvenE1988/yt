from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import os

app = Flask(__name__)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
        # Explizite Sprachauswahl: Deutsch oder Englisch
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['de', 'en'])
        return jsonify({'transcript': transcript})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'YouTube Transcript API is running', 'usage': '/transcript?video_id=VIDEO_ID'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
