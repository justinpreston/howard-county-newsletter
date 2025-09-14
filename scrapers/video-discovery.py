#!/usr/bin/env python3
"""
Video Discovery and Processing Pipeline
Discovers, downloads, and processes government meeting videos
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import subprocess
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/video-processing-{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        self.data_dir = "data/videos"
        self.transcript_dir = "data/transcripts"
        self.temp_dir = tempfile.mkdtemp(prefix="hc_video_")
        
        for directory in [self.data_dir, self.transcript_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Video sources for Howard County
        self.video_sources = {
            'granicus': {
                'name': 'Granicus Live Streaming',
                'api_base': 'https://howardcounty.granicus.com/ViewPublisher.php',
                'archive_url': 'https://howardcounty.granicus.com/MediaPlayer.php'
            },
            'youtube': {
                'name': 'Howard County YouTube',
                'channel_id': 'UC_HOWARD_COUNTY_CHANNEL_ID',  # Replace with actual
                'api_key': os.getenv('YOUTUBE_API_KEY')
            },
            'facebook': {
                'name': 'Howard County Facebook',
                'page_id': 'HowardCountyMD'
            }
        }
        
        self.openai_api_key = os.getenv('OPENAI_API_KEY')

    def discover_recent_videos(self) -> List[Dict[str, Any]]:
        """Discover recent government meeting videos from all sources"""
        all_videos = []
        
        for source_name, source_config in self.video_sources.items():
            logger.info(f"Discovering videos from {source_name}")
            
            try:
                if source_name == 'granicus':
                    videos = self.discover_granicus_videos(source_config)
                elif source_name == 'youtube':
                    videos = self.discover_youtube_videos(source_config)
                elif source_name == 'facebook':
                    videos = self.discover_facebook_videos(source_config)
                else:
                    continue
                    
                all_videos.extend(videos)
                logger.info(f"Found {len(videos)} videos from {source_name}")
                
            except Exception as e:
                logger.error(f"Error discovering videos from {source_name}: {e}")
        
        return all_videos

    def discover_granicus_videos(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover videos from Granicus platform"""
        videos = []
        
        try:
            # Granicus typically uses a structured API
            # This is a simplified example - actual implementation depends on their API
            
            session = requests.Session()
            
            # Get recent meetings list
            meetings_url = f"{config['api_base']}?view=&clip_id="
            response = session.get(meetings_url)
            response.raise_for_status()
            
            # Parse response for video metadata
            # This would need to be customized based on Granicus API structure
            
            sample_video = {
                'id': f"granicus_{int(datetime.now().timestamp())}",
                'title': 'Howard County Council Meeting - Sample',
                'description': 'Weekly council meeting discussion',
                'url': config['archive_url'],
                'source': 'granicus',
                'meeting_date': datetime.now().strftime('%Y-%m-%d'),
                'duration_estimate': 7200,  # 2 hours
                'discovered_at': datetime.utcnow().isoformat()
            }
            
            videos.append(sample_video)
            
        except Exception as e:
            logger.error(f"Error with Granicus discovery: {e}")
            
        return videos

    def discover_youtube_videos(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover videos from YouTube channel"""
        videos = []
        
        if not config.get('api_key'):
            logger.warning("YouTube API key not configured")
            return videos
        
        try:
            # YouTube Data API v3 call
            api_url = "https://www.googleapis.com/youtube/v3/search"
            
            params = {
                'part': 'snippet',
                'channelId': config['channel_id'],
                'maxResults': 10,
                'order': 'date',
                'type': 'video',
                'key': config['api_key'],
                'publishedAfter': (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
            }
            
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get('items', []):
                video = {
                    'id': f"youtube_{item['id']['videoId']}",
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'source': 'youtube',
                    'meeting_date': item['snippet']['publishedAt'][:10],
                    'thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'discovered_at': datetime.utcnow().isoformat()
                }
                
                videos.append(video)
                
        except Exception as e:
            logger.error(f"Error with YouTube discovery: {e}")
            
        return videos

    def discover_facebook_videos(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover videos from Facebook page"""
        videos = []
        
        try:
            # Facebook Graph API would be used here
            # This is a placeholder implementation
            
            logger.info("Facebook video discovery not fully implemented")
            
        except Exception as e:
            logger.error(f"Error with Facebook discovery: {e}")
            
        return videos

    def download_video(self, video_info: Dict[str, Any]) -> Optional[str]:
        """Download video using yt-dlp"""
        try:
            video_id = video_info['id']
            video_url = video_info['url']
            
            output_path = os.path.join(self.temp_dir, f"{video_id}")
            
            # yt-dlp command for downloading
            cmd = [
                'yt-dlp',
                '--format', 'best[height<=720]',  # Limit quality for processing
                '--output', f"{output_path}.%(ext)s",
                '--write-info-json',
                video_url
            ]
            
            logger.info(f"Downloading video: {video_info['title']}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            
            if result.returncode == 0:
                # Find the downloaded file
                for filename in os.listdir(self.temp_dir):
                    if filename.startswith(video_id) and not filename.endswith('.json'):
                        downloaded_file = os.path.join(self.temp_dir, filename)
                        logger.info(f"Successfully downloaded: {downloaded_file}")
                        return downloaded_file
            else:
                logger.error(f"Download failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error downloading video {video_info['id']}: {e}")
            
        return None

    def extract_audio(self, video_path: str) -> Optional[str]:
        """Extract audio from video file for transcription"""
        try:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            audio_path = os.path.join(self.temp_dir, f"{video_name}.wav")
            
            # Use FFmpeg to extract audio
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ar', '16000',  # 16kHz sample rate for Whisper
                '-ac', '1',      # Mono audio
                '-c:a', 'pcm_s16le',
                '-y',            # Overwrite output file
                audio_path
            ]
            
            logger.info(f"Extracting audio from {video_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)  # 15 min timeout
            
            if result.returncode == 0 and os.path.exists(audio_path):
                logger.info(f"Audio extracted: {audio_path}")
                return audio_path
            else:
                logger.error(f"Audio extraction failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            
        return None

    def transcribe_audio(self, audio_path: str, video_info: Dict[str, Any]) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper"""
        if not self.openai_api_key:
            logger.warning("OpenAI API key not configured for transcription")
            return None
        
        try:
            import openai
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            # Open audio file
            with open(audio_path, 'rb') as audio_file:
                logger.info(f"Transcribing audio: {os.path.basename(audio_path)}")
                
                # Use Whisper API for transcription
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
                
                # Save transcript
                video_id = video_info['id']
                transcript_path = os.path.join(self.transcript_dir, f"{video_id}_transcript.txt")
                
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                
                logger.info(f"Transcript saved: {transcript_path}")
                return transcript_path
                
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            
        return None

    def process_video(self, video_info: Dict[str, Any]) -> Dict[str, Any]:
        """Complete video processing pipeline"""
        result = {
            'video_info': video_info,
            'processed_at': datetime.utcnow().isoformat(),
            'status': 'failed',
            'transcript_path': None,
            'processing_time': None
        }
        
        start_time = datetime.now()
        
        try:
            # Download video
            video_path = self.download_video(video_info)
            if not video_path:
                result['error'] = 'Failed to download video'
                return result
            
            # Extract audio
            audio_path = self.extract_audio(video_path)
            if not audio_path:
                result['error'] = 'Failed to extract audio'
                return result
            
            # Transcribe audio
            transcript_path = self.transcribe_audio(audio_path, video_info)
            if transcript_path:
                result['transcript_path'] = transcript_path
                result['status'] = 'success'
            else:
                result['error'] = 'Failed to transcribe audio'
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Video processing error: {e}")
        
        finally:
            # Cleanup temporary files
            try:
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
                    self.temp_dir = tempfile.mkdtemp(prefix="hc_video_")
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")
        
        result['processing_time'] = (datetime.now() - start_time).total_seconds()
        return result

    def run_video_discovery(self):
        """Main video discovery execution"""
        logger.info("Starting video discovery and processing")
        
        # Discover videos
        videos = self.discover_recent_videos()
        logger.info(f"Discovered {len(videos)} videos")
        
        # Process recent videos (limit to prevent overload)
        processed_results = []
        
        for video in videos[:3]:  # Limit to 3 most recent videos
            logger.info(f"Processing video: {video['title']}")
            result = self.process_video(video)
            processed_results.append(result)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.data_dir, f"video_processing_{timestamp}.json")
        
        final_results = {
            'discovery_timestamp': datetime.utcnow().isoformat(),
            'videos_discovered': len(videos),
            'videos_processed': len(processed_results),
            'processing_results': processed_results,
            'all_discovered_videos': videos
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Video processing complete. Results saved to {results_file}")
        
        return final_results

if __name__ == "__main__":
    processor = VideoProcessor()
    results = processor.run_video_discovery()
    print(json.dumps({
        'videos_discovered': results['videos_discovered'],
        'videos_processed': results['videos_processed'],
        'timestamp': results['discovery_timestamp']
    }, indent=2))