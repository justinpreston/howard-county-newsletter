# Howard County Video Content Scraper

## Overview

The Video Content Scraper is a comprehensive workflow that automatically discovers, processes, and analyzes Howard County meeting videos from multiple sources including Granicus and YouTube. It provides AI-powered transcription, content analysis, and newsletter-ready summaries.

## Workflow Architecture

### Multi-Source Video Discovery

- **Granicus Web Scraping**: Extracts meeting information from the official Howard County Granicus archive
- **Granicus API Integration**: Fetches structured video metadata via API calls
- **YouTube Integration**: Discovers Howard County videos published on YouTube
- **Daily Scheduling**: Automatic execution every morning at 9 AM

### Processing Pipeline

1. **Video Discovery** → Multiple sources scraped simultaneously
2. **Metadata Processing** → Video information standardized and enriched
3. **Duplicate Detection** → Database check to avoid reprocessing
4. **Transcript Extraction** → Captions retrieved or generated via AI
5. **AI Analysis** → Content summarized and key moments identified
6. **Data Storage** → Processed information stored for newsletter generation

## Technical Components

### Node Descriptions

#### V1: Schedule Video Check

- **Type**: Schedule Trigger
- **Schedule**: Daily at 9:00 AM
- **Purpose**: Initiates the entire video processing pipeline

#### V2: Scrape Granicus Archive

- **Type**: HTTP Request
- **Target**: Howard County Granicus web interface
- **Purpose**: Discovers new meetings and videos via web scraping

#### V3: Parse Video List HTML

- **Type**: HTML Extract
- **Function**: Extracts meeting titles, dates, video links, and agenda links
- **Selectors**:
  - Meeting titles: `.meetingRow .title a`
  - Dates: `.meetingRow .date`
  - Video links: `.meetingRow .video a`
  - Agendas: `.meetingRow .agenda a`

#### V4: Granicus API Call

- **Type**: HTTP Request
- **Endpoint**: Granicus Events API
- **Purpose**: Fetches structured video metadata via official API

#### V5: Process Video Metadata

- **Type**: Code Node
- **Function**: Standardizes video information from multiple sources
- **Features**:
  - Video ID extraction from URLs
  - Meeting type classification
  - URL construction for various video formats

#### V6: Check New Videos

- **Type**: PostgreSQL Query
- **Purpose**: Identifies videos not yet processed to avoid duplicates
- **Query**: Checks existing video_id values against new discoveries

#### V7: Download Video Transcript

- **Type**: HTTP Request
- **Purpose**: Attempts to retrieve existing captions or transcript data

#### V8: Extract Closed Captions

- **Type**: Code Node
- **Function**: Parses HTML to locate VTT caption files or embedded transcripts
- **Fallback**: Flags videos requiring transcription if no captions found

#### V9: Download Video for Transcription

- **Type**: Code Node
- **Purpose**: Prepares videos without captions for AI transcription
- **Tools**: Generates download commands for video files

#### V10: Whisper Transcription

- **Type**: HTTP Request (OpenAI)
- **Service**: OpenAI Whisper API
- **Features**:
  - High-quality speech-to-text
  - Howard County context prompts
  - Verbose JSON output with timestamps

#### V11: Process Transcript with AI

- **Type**: HTTP Request (Anthropic)
- **Service**: Claude Haiku
- **Analysis Categories**:
  - Key decisions and votes
  - Important discussions
  - Public testimony summaries
  - Action items
  - Affected neighborhoods

#### V12: Extract Key Moments

- **Type**: Code Node
- **Function**: Identifies timestamp-linked significant events
- **Keywords**: Votes, public comments, budget items, zoning discussions
- **Output**: Clickable timestamp links for direct video access

#### V13: Generate Video Summary

- **Type**: Code Node
- **Purpose**: Creates newsletter-ready content summaries
- **Features**:
  - Headlines and quick summaries
  - Key decision highlights
  - Topic categorization
  - Neighborhood impact analysis

#### V14: Store Video Content

- **Type**: PostgreSQL Insert
- **Table**: `council_videos`
- **Purpose**: Persists processed video data for future newsletter generation

#### V15: YouTube Integration

- **Type**: HTTP Request (YouTube API)
- **Purpose**: Discovers Howard County videos on YouTube platform
- **Search**: Council meetings and public events

#### V16: Process YouTube Videos

- **Type**: Code Node
- **Function**: Standardizes YouTube video metadata
- **Features**: Meeting detection, caption URL generation, thumbnail extraction

## Database Schema

### Required Tables

```sql
CREATE TABLE council_videos (
  id SERIAL PRIMARY KEY,
  video_id VARCHAR(255) UNIQUE,
  title TEXT,
  date TIMESTAMP,
  url TEXT,
  transcript TEXT,
  ai_summary TEXT,
  key_moments JSONB,
  topics TEXT[],
  neighborhoods TEXT[],
  duration INTEGER,
  has_captions BOOLEAN,
  processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_council_videos_date ON council_videos(date);
CREATE INDEX idx_council_videos_topics ON council_videos USING GIN(topics);
CREATE INDEX idx_council_videos_neighborhoods ON council_videos USING GIN(neighborhoods);
```

## Setup Requirements

### API Credentials

1. **OpenAI API**

   - Whisper transcription service
   - Account with sufficient credits for audio processing

2. **Anthropic API**

   - Claude Haiku for content analysis
   - API key with appropriate usage limits

3. **YouTube Data API** (Optional)
   - Google Cloud Platform project
   - YouTube Data API v3 enabled
   - Howard County channel ID: `UC6ImqPHwPnqp7MnCxnhBPMA`

### Database Configuration

- PostgreSQL database with appropriate permissions
- Connection credentials configured in n8n
- Required tables created with proper indexes

### Network Access

- Outbound HTTPS access to:
  - `howardcounty.granicus.com`
  - `api.openai.com`
  - `api.anthropic.com`
  - `www.googleapis.com`

## Meeting Type Classification

The workflow automatically classifies meetings into categories:

- **Legislative**: Regular council sessions
- **Public Hearing**: Zoning and development hearings
- **Work Session**: Planning and discussion meetings
- **Zoning**: Zoning Board appeals
- **Budget**: Budget planning and approval sessions
- **Regular**: Standard council meetings

## Content Analysis Features

### AI-Powered Transcript Analysis

- **Key Decisions**: Voting results and major resolutions
- **Important Discussions**: Main topics and debates
- **Public Testimony**: Citizen comment summaries
- **Action Items**: Follow-up tasks and future agenda items
- **Geographic Impact**: Neighborhoods and districts affected

### Key Moment Detection

Automatic identification of significant timestamps:

- Motion voting (passes/fails)
- Public testimony periods
- Budget discussions
- Zoning matters
- Department presentations

### Topic Categorization

- Education and schools
- Development and zoning
- Budget and fiscal matters
- Public safety
- Transportation

## Integration with Newsletter System

### Output Data Structure

```json
{
  "headline": "County Council Meeting - September 14, 2025",
  "quick_summary": "AI-generated meeting summary",
  "key_decisions": ["Budget approved", "Zoning variance denied"],
  "video_link": "https://howardcounty.granicus.com/MediaPlayer.php?clip_id=12345",
  "watch_time": "120 minutes",
  "highlights": [
    {
      "time": "45:30",
      "description": "Public testimony on development project",
      "direct_link": "https://howardcounty.granicus.com/MediaPlayer.php?clip_id=12345&t=2730"
    }
  ],
  "topics": ["development", "public_safety"],
  "neighborhoods_mentioned": ["columbia", "ellicott_city"]
}
```

### Newsletter Integration

1. **Main Workflow Connection**: Video summaries feed into newsletter content generation
2. **Personalization**: Topic and neighborhood data used for subscriber targeting
3. **Embed Generation**: Video content prepared for email embedding

## Performance Considerations

### Processing Time

- Full workflow: 15-30 minutes per video
- Transcript generation: 2-5 minutes per hour of video
- AI analysis: 1-2 minutes per transcript

### Resource Usage

- **Storage**: ~10MB per processed video (transcript + metadata)
- **API Costs**:
  - Whisper: ~$0.006 per minute of audio
  - Claude Haiku: ~$0.25 per 1K tokens
- **Bandwidth**: Variable based on video length and quality

### Scalability

- Processes up to 20 videos per day
- Handles multiple meeting types simultaneously
- Automatic error handling and retry logic

## Monitoring and Maintenance

### Health Checks

- Monitor API response times and success rates
- Track transcription accuracy and processing failures
- Verify database storage and retrieval operations

### Regular Maintenance

- Update Howard County official names and terminology
- Adjust topic keywords based on content trends
- Review and optimize AI prompts for better analysis

### Error Handling

- Failed transcriptions fallback to manual processing
- API timeout handling with automatic retries
- Graceful degradation when services are unavailable

## Security and Compliance

### Data Protection

- Video transcripts contain public meeting information
- Secure API key storage in n8n credentials system
- Database access controls and encryption

### Privacy Considerations

- Public meeting content is already in public domain
- No personal information processing beyond public testimony
- Compliance with local government transparency requirements

## Troubleshooting

### Common Issues

1. **Granicus Access**: Website structure changes may break scraping
2. **API Limits**: Whisper and Claude API quotas may be exceeded
3. **Video Format**: Some Granicus videos may use unsupported formats
4. **Caption Quality**: Automatic captions may have accuracy issues

### Solutions

- Implement fallback scraping strategies
- Monitor API usage and implement rate limiting
- Add support for additional video formats
- Manual review process for critical meetings
