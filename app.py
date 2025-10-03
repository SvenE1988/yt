from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import os
import random

app = Flask(__name__)

# Deine Webshare Proxies
PROXIES = [
    {"ip": "142.111.48.253", "port": "7030", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "198.23.239.134", "port": "6540", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "45.38.107.97", "port": "6014", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "107.172.163.27", "port": "6543", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "64.137.96.74", "port": "6641", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "154.203.43.247", "port": "5536", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "84.247.60.125", "port": "6095", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "216.10.27.159", "port": "6837", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "142.111.67.146", "port": "5611", "user": "slbfveyo", "pass": "86rico8f7ml1"},
    {"ip": "142.147.128.93", "port": "6593", "user": "slbfveyo", "pass": "86rico8f7ml1"},
]

def get_random_proxy():
    """Wählt zufällig einen Proxy aus"""
    proxy = random.choice(PROXIES)
    proxy_url = f"http://{proxy['user']}:{proxy['pass']}@{proxy['ip']}:{proxy['port']}"
    return {
        'http': proxy_url,
        'https': proxy_url
    }

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
        # Nutze zufälligen Proxy
        proxies = get_random_proxy()
        
        # Neue API mit Proxy
        ytt_api = YouTubeTranscriptApi(proxies=proxies)
        fetched_transcript = ytt_api.fetch(video_id, languages=['de', 'en'])
        
        # Konvertiere zu raw data
        transcript_data = fetched_transcript.to_raw_data()
        
        return jsonify({
            'video_id': video_id,
            'language': fetched_transcript.language,
            'language_code': fetched_transcript.language_code,
            'is_generated': fetched_transcript.is_generated,
            'transcript': transcript_data
        })
    
    except TranscriptsDisabled:
        return jsonify({'error': 'Subtitles are disabled for this video'}), 404
    
    except NoTranscriptFound:
        return jsonify({'error': 'No transcript found in German or English'}), 404
    
    except VideoUnavailable:
        return jsonify({'error': 'Video is unavailable'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'proxies_available': len(PROXIES)}), 200

@app.route('/test-proxy', methods=['GET'])
def test_proxy():
    """Testet ob Proxies funktionieren"""
    try:
        proxies = get_random_proxy()
        ytt_api = YouTubeTranscriptApi(proxies=proxies)
        # Test mit bekanntem Video
        fetched = ytt_api.fetch('dQw4w9WgXcQ', languages=['en'])
        return jsonify({
            'status': 'Proxy works!',
            'proxy_used': proxies['http'].split('@')[1],  # Zeigt IP ohne Credentials
            'test_video': 'dQw4w9WgXcQ',
            'transcript_length': len(fetched)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/languages', methods=['GET'])
def get_languages():
    """Liste verfügbare Sprachen für ein Video"""
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
        proxies = get_random_proxy()
        ytt_api = YouTubeTranscriptApi(proxies=proxies)
        transcript_list = ytt_api.list_transcripts(video_id)
        
        available = []
        for transcript in transcript_list:
            available.append({
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated
            })
        
        return jsonify({
            'video_id': video_id,
            'available_transcripts': available
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'YouTube Transcript API is running',
        'proxies_configured': len(PROXIES),
        'endpoints': {
            '/transcript?video_id=VIDEO_ID': 'Get transcript',
            '/languages?video_id=VIDEO_ID': 'List available languages',
            '/test-proxy': 'Test if proxy works',
            '/health': 'Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
