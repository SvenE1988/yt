from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import os
import traceback
import requests
import random

app = Flask(__name__)

# Deine 10 statischen Webshare Proxies
PROXY_LIST = [
    "142.111.48.253:7030",
    "198.23.239.134:6540",
    "45.38.107.97:6014",
    "107.172.163.27:6543",
    "64.137.96.74:6641",
    "154.203.43.247:5536",
    "84.247.60.125:6095",
    "216.10.27.159:6837",
    "142.111.67.146:5611",
    "142.147.128.93:6593"
]

PROXY_USERNAME = "slbfveyo"
PROXY_PASSWORD = "86rico8f7ml1"

# Proxy-Rotation: Wähle zufälligen Proxy
def get_random_proxy():
    """Wählt zufällig einen Proxy aus der Liste"""
    proxy = random.choice(PROXY_LIST)
    proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{proxy}"
    return GenericProxyConfig(
        http_url=proxy_url,
        https_url=proxy_url
    )

# Custom HTTP Session mit Browser-Headers
def create_session():
    """Erstellt Session mit realistischen Browser-Headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    return session

@app.route('/transcript', methods=['GET'])
def get_transcript():
    """
    Holt Transkript in Originalsprache (Deutsch oder Englisch)
    Query Parameter:
    - video_id: YouTube Video ID (required)
    - preserve_formatting: true/false (optional, default: false)
    """
    video_id = request.args.get('video_id')
    preserve_formatting = request.args.get('preserve_formatting', 'false').lower() == 'true'
    
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    # Versuche mit bis zu 3 verschiedenen Proxies
    max_retries = 3
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Wähle zufälligen Proxy
            proxy_config = get_random_proxy()
            session = create_session()
            
            # Erstelle API-Instanz mit Session + Proxy
            ytt_api = YouTubeTranscriptApi(
                http_client=session,
                proxy_config=proxy_config
            )
            
            # Fetch transcript mit Sprachpriorität: Deutsch > Englisch
            fetched_transcript = ytt_api.fetch(
                video_id, 
                languages=['de', 'en'],
                preserve_formatting=preserve_formatting
            )
            
            # Konvertiere zu raw data
            transcript_data = fetched_transcript.to_raw_data()
            
            return jsonify({
                'video_id': video_id,
                'language': fetched_transcript.language,
                'language_code': fetched_transcript.language_code,
                'is_generated': fetched_transcript.is_generated,
                'transcript': transcript_data,
                'proxy_used': f"Proxy {attempt + 1}/{max_retries}"
            })
        
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            # Diese Fehler sind nicht Proxy-bezogen, sofort abbrechen
            return jsonify({'error': str(e)}), 404
        
        except Exception as e:
            last_error = e
            # Bei 429 oder anderen Fehlern: Nächsten Proxy versuchen
            if attempt < max_retries - 1:
                continue
    
    # Alle Proxies fehlgeschlagen
    return jsonify({
        'error': 'All proxies failed',
        'last_error': str(last_error),
        'error_type': type(last_error).__name__,
        'traceback': traceback.format_exc()
    }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'proxy_provider': 'Webshare Static (Manual Rotation)',
        'proxy_count': len(PROXY_LIST),
        'proxy_username': PROXY_USERNAME
    }), 200

@app.route('/test-proxy', methods=['GET'])
def test_proxy():
    """Testet ob statische Proxies funktionieren"""
    results = []
    
    for i, proxy in enumerate(PROXY_LIST[:3]):  # Teste nur erste 3 Proxies
        try:
            proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{proxy}"
            proxy_config = GenericProxyConfig(
                http_url=proxy_url,
                https_url=proxy_url
            )
            
            session = create_session()
            ytt_api = YouTubeTranscriptApi(
                http_client=session,
                proxy_config=proxy_config
            )
            
            fetched = ytt_api.fetch('dQw4w9WgXcQ', languages=['en'])
            
            results.append({
                'proxy': proxy,
                'status': 'success',
                'transcript_length': len(fetched)
            })
        except Exception as e:
            results.append({
                'proxy': proxy,
                'status': 'failed',
                'error': str(e)[:100]
            })
    
    return jsonify({
        'test_results': results,
        'total_proxies': len(PROXY_LIST)
    })

@app.route('/languages', methods=['GET'])
def get_languages():
    """Liste alle verfügbaren Sprachen für ein Video"""
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
        proxy_config = get_random_proxy()
        session = create_session()
        ytt_api = YouTubeTranscriptApi(
            http_client=session,
            proxy_config=proxy_config
        )
        transcript_list = ytt_api.list(video_id)
        
        available = []
        for transcript in transcript_list:
            available.append({
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            })
        
        return jsonify({
            'video_id': video_id,
            'available_transcripts': available
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'YouTube Transcript API is running',
        'version': '1.2.2',
        'proxy_provider': 'Webshare Static (Manual Rotation)',
        'proxy_count': len(PROXY_LIST),
        'endpoints': {
            '/transcript?video_id=VIDEO_ID': 'Get transcript (DE/EN priority)',
            '/transcript?video_id=VIDEO_ID&preserve_formatting=true': 'Get transcript with HTML formatting',
            '/languages?video_id=VIDEO_ID': 'List available languages',
            '/test-proxy': 'Test first 3 proxies',
            '/health': 'Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
