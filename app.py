from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import os
import traceback

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
    
    except TranscriptsDisabled:
        return jsonify({'error': 'Subtitles are disabled for this video'}), 404
    
    except NoTranscriptFound:
        return jsonify({'error': 'No transcript found in German or English'}), 404
    
    except VideoUnavailable:
        return jsonify({'error': 'Video is unavailable'}), 404
    
    except AttributeError as e:
        return jsonify({'error': f'Library error: {str(e)}', 'traceback': traceback.format_exc()}), 500
    
    except Exception as e:
        return jsonify({'error': str(e), 'type': type(e).__name__, 'traceback': traceback.format_exc()}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/test', methods=['GET'])
def test():
    """Test if library is properly imported"""
    try:
        import youtube_transcript_api
        return jsonify({
            'library_version': youtube_transcript_api.__version__ if hasattr(youtube_transcript_api, '__version__') else 'unknown',
            'has_get_transcript': hasattr(YouTubeTranscriptApi, 'get_transcript'),
            'available_methods': dir(YouTubeTranscriptApi)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'YouTube Transcript API is running', 'usage': '/transcript?video_id=VIDEO_ID'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
