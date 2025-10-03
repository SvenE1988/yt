from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

@app.route('/transcript')
def get_transcript():
    video_id = request.args.get('video_id')
    lang = request.args.get('lang', 'de,en').split(',')
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=lang)
        return jsonify(transcript)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)