from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
import random

app = Flask(__name__)

# Deine 10 Proxies
PROXIES = [
    "142.111.48.253:7030", "198.23.239.134:6540", "45.38.107.97:6014",
    "107.172.163.27:6543", "64.137.96.74:6641", "154.203.43.247:5536",
    "84.247.60.125:6095", "216.10.27.159:6837", "142.111.67.146:5611",
    "142.147.128.93:6593"
]
USER = "slbfveyo"
PASS = "86rico8f7ml1"

def get_proxy():
    """Wählt zufälligen Proxy"""
    proxy = random.choice(PROXIES)
    url = f"http://{USER}:{PASS}@{proxy}"
    return GenericProxyConfig(http_url=url, https_url=url)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id required'}), 400
    
    try:
        ytt_api = YouTubeTranscriptApi(proxy_config=get_proxy())
        transcript = ytt_api.fetch(video_id, languages=['de', 'en'])
        
        return jsonify({
            'video_id': video_id,
            'language': transcript.language,
            'transcript': transcript.to_raw_data()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'proxies': len(PROXIES)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
