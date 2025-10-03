from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import os
import traceback
import requests

app = Flask(__name__)

# Webshare Credentials
WEBSHARE_USERNAME = "slbfveyo"
WEBSHARE_PASSWORD = "86rico8f7ml1"

# Webshare Proxy Config (Rotating Residential Proxies)
proxy_config = WebshareProxyConfig(
    proxy_username=WEBSHARE_USERNAME,
    proxy_password=WEBSHARE_PASSWORD
)

# Custom HTTP Session mit realistischem User-Agent
def create_session():
    """Erstellt eine Session mit Browser-ähnlichen Headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate'
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
    
    try:
        # Erstelle API-Instanz mit Custom Session + Webshare Proxy
        session = create_session()
        ytt_api = YouTubeTranscriptApi(
            http_client=session,
            proxy_config=proxy_config  # Offizieller Parameter-Name laut Doku
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
            'transcript': transcript_data
        })
    
    except TranscriptsDisabled:
        return jsonify({'error': 'Subtitles are disabled for this video'}), 404
    
    except NoTranscriptFound:
        return jsonify({'error': 'No transcript found in German or English'}), 404
    
    except VideoUnavailable:
        return jsonify({'error': 'Video is unavailable'}), 404
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'proxy_provider': 'Webshare Residential',
        'proxy_username': WEBSHARE_USERNAME
    }), 200

@app.route('/test-proxy', methods=['GET'])
def test_proxy():
    """Testet ob Webshare Proxy funktioniert"""
    try:
        session = create_session()
        ytt_api = YouTubeTranscriptApi(
            http_client=session,
            proxy_config=proxy_config
        )
        fetched = ytt_api.fetch('dQw4w9WgXcQ', languages=['en'])
        
        return jsonify({
            'status': 'Webshare Proxy works!',
            'test_video': 'dQw4w9WgXcQ',
            'transcript_length': len(fetched),
            'language': fetched.language
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        }), 500

@app.route('/languages', methods=['GET'])
def get_languages():
    """Liste alle verfügbaren Sprachen für ein Video"""
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
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
        'proxy_provider': 'Webshare (Rotating Residential)',
        'endpoints': {
            '/transcript?video_id=VIDEO_ID': 'Get transcript (DE/EN priority)',
            '/transcript?video_id=VIDEO_ID&preserve_formatting=true': 'Get transcript with HTML formatting',
            '/languages?video_id=VIDEO_ID': 'List available languages',
            '/test-proxy': 'Test if proxy works',
            '/health': 'Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
