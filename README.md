# Howard County Civic Journalism Platform

A comprehensive automated civic journalism platform that monitors, processes, and delivers Howard County government information to residents through intelligent newsletter generation, multi-platform publishing, and real-time civic engagement tools.

## 🎯 Project Vision

**Complete Government Transparency**: Every meeting, every decision, every document tracked and summarized

This platform serves as a comprehensive **civic engagement hub** for Howard County residents, providing:

- **Complete Government Transparency**: Every meeting, every decision, every document tracked and summarized  
- **Automated Data Collection**: GitHub Actions pipeline scrapes government sources every 4 hours
- **Multi-AI Processing**: Anthropic Claude + OpenAI GPT-4 + Whisper for comprehensive content analysis
- **Cross-Platform Publishing**: Email (SendGrid/Mailchimp) + Web (Webflow/Ghost) + Social Media
- **Real-Time Alerts**: Emergency notifications via SMS (Twilio) and push notifications (Firebase)
- **Privacy-Focused Analytics**: Plausible/Matomo tracking without compromising resident privacy

## 🏗️ System Architecture

### Comprehensive Tech Stack

**Core Automation Platform**:
- **n8n Workflows**: Primary orchestration engine (25-node comprehensive workflow)
- **GitHub Actions**: Scheduled data collection and processing (every 4 hours during business days)
- **PostgreSQL**: Structured data storage with full-text search capabilities
- **Redis**: Caching and session management

**AI Processing Pipeline**:
- **OpenAI Whisper**: Video transcription from government meetings
- **OpenAI GPT-4**: Content generation and enhancement 
- **Anthropic Claude**: Summarization and analysis
- **Custom ML Models**: Sentiment analysis and content categorization

**Integration & Automation Layer**:
- **Zapier Integration Hub**: Cross-platform workflow automation
- **Make.com**: Advanced integration scenarios and conditional logic
- **GitHub Actions**: Scheduled scraping, data validation, and deployment

**Publishing & Design**:
- **Canva API**: Automated newsletter design and social media graphics
- **Webflow CMS**: Dynamic web publishing with SEO optimization
- **Ghost CMS**: Blog publishing and content management
- **SendGrid**: Reliable email delivery infrastructure  
- **Mailchimp**: Advanced email marketing and subscriber segmentation

**Analytics & Monitoring**:
- **Plausible Analytics**: Privacy-focused website and content analytics
- **Matomo**: Comprehensive visitor behavior tracking
- **Custom Dashboard**: Real-time civic engagement metrics

### Data Sources for Howard County

- **Government Meetings**: County Council, Planning Board, School Board, Department meetings
- **Planning & Development**: Zoning applications, building permits, development proposals, variance requests  
- **Education (HCPSS)**: Board meetings, policy updates, enrollment data, budget allocations
- **Public Safety**: Emergency alerts, road closures, public safety updates
- **Video Content**: Granicus meeting recordings, YouTube live streams

### Newsletter Structure

#### Multi-Channel Content Distribution:

- **Email Newsletter**: Weekly digest with neighborhood-specific sections
- **Web Dashboard**: Real-time updates and searchable government document archive
- **Social Media**: Automated posts for breaking news and meeting highlights
- **SMS Alerts**: Emergency notifications and urgent civic deadlines
- **Push Notifications**: Mobile app alerts for time-sensitive civic engagement opportunities

#### Content Processing & Enhancement:

- **Meeting Summarization**: Convert 3-hour meetings into 300-word digestible summaries
- **Impact Assessment**: AI-powered analysis of which neighborhoods and stakeholders are affected
- **Trend Analysis**: Track policy changes and their long-term implications over time
- **Public Interest Scoring**: Prioritize content based on community impact and engagement history

## 🚀 Technical Implementation

### Core Workflows

#### Main Newsletter Workflow

- **File**: `workflows/howard-county-n8n-workflow.json`
- **Function**: Complete newsletter generation pipeline from data collection to personalized delivery
- **Features**:
  - Multi-source data collection from 6+ government platforms
  - AI-powered content processing and summarization
  - Neighborhood-specific content organization
  - Personalized delivery based on subscriber preferences
  - Comprehensive analytics and cost tracking
- **Schedule**: Daily at 6:00 AM with full automation
- **Processing Time**: ~25 minutes for complete newsletter generation
- **Capacity**: Handles unlimited subscribers with personalization

#### Emergency Alert System

- **File**: `workflows/emergency-alert-monitor.json`
- **Function**: Real-time emergency monitoring and instant notification
- **Capabilities**:
  - Multi-source emergency feed monitoring
  - Intelligent alert filtering and deduplication
  - Geographic impact assessment
  - Multi-channel delivery (SMS, email, push notifications)
- **Response Time**: Under 5 minutes from alert detection to delivery
- **Coverage**: County-wide and neighborhood-specific alerts

#### Video Processing Pipeline

- **File**: `workflows/video-content-scraper.json`
- **Function**: Comprehensive government meeting video analysis
- **Process**: Discovery → Download → Transcription → AI Analysis → Newsletter Integration
- **Capabilities**:
  - Multi-platform video discovery (Granicus, YouTube, direct links)
  - High-quality transcription with speaker identification
  - AI-powered content analysis and key point extraction
  - Automated newsletter content generation

### Specialized Node Examples

Located in `workflows/examples/` for workflow extension:

1. **Sentiment Analysis** (`sentiment-analysis-node.js`)

   - Public comment sentiment tracking across meetings
   - Policy impact assessment and community response measurement
   - Trend analysis for controversial topics

2. **AI Cost Management** (`ai-cost-optimizer-node.js`)

   - Real-time API usage monitoring and cost prediction
   - Intelligent caching to reduce redundant processing
   - Automated cost alerts and budget management

3. **Fact Verification** (`fact-check-validation-node.js`)

   - Multi-source fact checking against official records
   - Misinformation detection and accuracy scoring
   - Source credibility assessment and verification

4. **System Health Monitoring** (`system-health-monitoring-node.js`)

   - Real-time workflow performance tracking
   - Database health monitoring and optimization alerts
   - Automated issue detection and recovery procedures

5. **ML Personalization** (`ml-personalization-node.js`)

   - Subscriber preference learning and content scoring
   - Engagement pattern analysis and optimization
   - Dynamic content recommendation engine

6. **Video Embedding** (`video-embed-generator-node.js`)
   - Responsive video player generation for newsletters
   - Accessibility compliance (captions, transcripts)
   - Multi-platform compatibility and optimization
