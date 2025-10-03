from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import os

app = Flask(__name__)

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
        # Neue API: Instanz erstellen und fetch() nutzen
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id, languages=['de', 'en'])
        
        # Konvertiere zu raw data (Liste von Dicts)
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
    return jsonify({'status': 'ok'}), 200

@app.route('/languages', methods=['GET'])
def get_languages():
    """Liste verfügbare Sprachen für ein Video"""
    video_id = request.args.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id parameter required'}), 400
    
    try:
        ytt_api = YouTubeTranscriptApi()
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
        'endpoints': {
            '/transcript?video_id=VIDEO_ID': 'Get transcript',
            '/languages?video_id=VIDEO_ID': 'List available languages',
            '/health': 'Health check'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
