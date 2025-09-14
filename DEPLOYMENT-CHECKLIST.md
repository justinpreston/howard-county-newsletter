# 🚀 Howard County Civic Journalism Platform - Deployment Checklist

## 📋 Pre-Deployment Checklist

### ✅ Infrastructure Setup (Already Complete)
- [x] **n8n Docker Instance**: Running and accessible
- [ ] **PostgreSQL Database**: Created and configured
- [ ] **Redis Cache**: Available for session management
- [ ] **Domain Name**: Configured with SSL certificate
- [ ] **Email Domain**: SPF, DKIM, DMARC records configured

### 🔧 Core Configuration
- [ ] **Environment Variables**: All required API keys configured
- [ ] **Database Schema**: Tables created and indexed
- [ ] **n8n Workflows**: Imported and activated
- [ ] **Webhook URLs**: n8n webhook endpoints documented

### 🤖 AI Services Setup
- [ ] **OpenAI API**: Key configured, Whisper access verified
- [ ] **Anthropic Claude API**: Key configured, model access verified
- [ ] **API Rate Limits**: Understood and monitored
- [ ] **Cost Monitoring**: Budget alerts configured

### 📧 Communication Channels
- [ ] **SendGrid**: API key configured, domain verified
- [ ] **Twilio**: Account SID and auth token configured
- [ ] **Firebase**: Service account JSON configured
- [ ] **Test Notifications**: Emergency alert system tested

### 🔄 GitHub Actions Pipeline (Next Step)
- [ ] **Repository Setup**: Code pushed to GitHub
- [ ] **Secrets Configuration**: All API keys added to repository secrets
- [ ] **Workflow Files**: GitHub Actions YAML files configured
- [ ] **Permissions**: Repository and workflow permissions set
- [ ] **Test Run**: Initial workflow execution successful

### 🌐 Platform Integrations (Optional)
- [ ] **Zapier**: Webhook URL configured
- [ ] **Make.com**: Integration scenarios created
- [ ] **Canva API**: Design automation configured
- [ ] **Webflow**: CMS publishing setup
- [ ] **Mailchimp**: Advanced email marketing configured
- [ ] **Plausible Analytics**: Privacy-focused tracking setup

### 🧪 Testing & Validation
- [ ] **Integration Tests**: All platform connections validated
- [ ] **Data Scraping**: Government sources accessible
- [ ] **Video Processing**: Whisper transcription working
- [ ] **Newsletter Generation**: End-to-end workflow tested
- [ ] **Emergency Alerts**: Real-time notification system tested

### 📊 Monitoring & Analytics
- [ ] **System Health**: Monitoring dashboard configured
- [ ] **Error Tracking**: Notification system for failures
- [ ] **Performance Metrics**: Response time monitoring
- [ ] **Cost Tracking**: API usage and billing alerts

## 🎯 GitHub Actions Setup Guide

Since you already have n8n running in Docker, let's set up the automated data collection pipeline with GitHub Actions.

### Step 1: Repository Configuration

First, ensure your code is in a GitHub repository:

```bash
# If not already done, create GitHub repository
gh repo create howard-county-newsletter --public --description "Comprehensive civic journalism platform for Howard County"

# Add remote origin if needed
git remote add origin https://github.com/YOUR-USERNAME/howard-county-newsletter.git

# Push your code
git add .
git commit -m "Initial commit: Howard County civic journalism platform"
git push -u origin main
```

### Step 2: Configure Repository Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions

Add these **required secrets**:

#### Core Infrastructure Secrets
```
GITHUB_TOKEN (automatically provided by GitHub)
N8N_WEBHOOK_URL=http://your-n8n-docker-host:5678/webhook/howard-county
N8N_EMERGENCY_WEBHOOK_URL=http://your-n8n-docker-host:5678/webhook/emergency
N8N_QUALITY_WEBHOOK_URL=http://your-n8n-docker-host:5678/webhook/quality
```

#### AI Service Secrets
```
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

#### Communication Service Secrets
```
SENDGRID_API_KEY=SG.your-sendgrid-api-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
FIREBASE_SERVICE_ACCOUNT={"type": "service_account", "project_id": "..."}
```

#### Optional Platform Integration Secrets
```
ZAPIER_WEBHOOK_URL=https://hooks.zapier.com/hooks/catch/xxxxx/xxxxx
MAKE_WEBHOOK_URL=https://hook.integromat.com/xxxxx/xxxxx
WEBFLOW_API_KEY=your-webflow-api-key
WEBFLOW_SITE_ID=your-webflow-site-id
CANVA_API_KEY=your-canva-api-key
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_LIST_ID=your-mailchimp-list-id
PLAUSIBLE_API_KEY=your-plausible-api-key
PLAUSIBLE_DOMAIN=your-domain.com
GRANICUS_API_KEY=your-granicus-api-key
YOUTUBE_API_KEY=your-youtube-api-key
```

### Step 3: Update n8n Webhook URLs

Since you have n8n running in Docker, you need to configure the webhook URLs that GitHub Actions will call:

1. **Access your n8n instance** (typically at http://localhost:5678)

2. **Import the main workflow** if you haven't already:
   - Go to Workflows → Import from file
   - Upload `workflows/howard-county-n8n-workflow.json`

3. **Configure webhook nodes** in your n8n workflow:
   - **GitHub Actions Webhook**: Set to `/webhook/howard-county`
   - **Emergency Alert Webhook**: Set to `/webhook/emergency`  
   - **Quality Report Webhook**: Set to `/webhook/quality`

4. **Get your webhook URLs**:
   ```bash
   # If running locally
   N8N_WEBHOOK_URL=http://localhost:5678/webhook/howard-county
   
   # If running on a server
   N8N_WEBHOOK_URL=https://your-domain.com/webhook/howard-county
   
   # If using n8n tunnel
   N8N_WEBHOOK_URL=https://your-tunnel-url.app.n8n.cloud/webhook/howard-county
   ```

### Step 4: Test GitHub Actions Workflow

The workflow file `.github/workflows/data-collection.yml` is already configured. To test it:

1. **Enable GitHub Actions** in your repository:
   - Go to repository → Actions tab
   - If prompted, click "I understand my workflows and want to enable them"

2. **Trigger a manual run**:
   ```bash
   # Using GitHub CLI
   gh workflow run data-collection.yml
   
   # Or via web interface: Actions → Data Collection Pipeline → Run workflow
   ```

3. **Monitor the execution**:
   ```bash
   # Check workflow status
   gh run list --workflow=data-collection.yml
   
   # View detailed logs
   gh run view --log
   ```

### Step 5: Verify n8n Integration

After GitHub Actions runs, check your n8n instance:

1. **Check executions**: Workflows → Executions
2. **Verify webhook calls**: Look for successful webhook triggers
3. **Review data processing**: Confirm that scraped data flows through your workflow

### Step 6: Configure Scheduled Execution

The workflow is already configured to run:
- **Every 4 hours** during business days (Monday-Friday)
- **Once daily** on weekends
- **Manually** when needed

You can modify the schedule in `.github/workflows/data-collection.yml`:

```yaml
on:
  schedule:
    # Run every 4 hours during business days
    - cron: '0 */4 * * 1-5'
    # Run once daily on weekends  
    - cron: '0 8 * * 0,6'
  workflow_dispatch: # Allow manual triggers
```

## 🔧 Quick Setup Commands

### For n8n Docker Integration:

```bash
# 1. Get your n8n container info
docker ps | grep n8n

# 2. Check n8n logs
docker logs n8n-container-name

# 3. Access n8n shell if needed
docker exec -it n8n-container-name /bin/sh

# 4. Test webhook connectivity from GitHub Actions
curl -X POST "http://your-n8n-host:5678/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{"test": true, "source": "github_actions"}'
```

### For GitHub Repository Setup:

```bash
# 1. Create and configure repository
gh repo create howard-county-newsletter --public
git remote add origin https://github.com/YOUR-USERNAME/howard-county-newsletter.git

# 2. Add secrets via CLI
gh secret set OPENAI_API_KEY --body "sk-your-key"
gh secret set ANTHROPIC_API_KEY --body "sk-ant-your-key"
gh secret set N8N_WEBHOOK_URL --body "http://your-n8n-host:5678/webhook/howard-county"

# 3. Push code and trigger workflow
git push origin main
gh workflow run data-collection.yml
```

## ⚠️ Important Notes

### Network Configuration
- **Docker networking**: Ensure GitHub Actions can reach your n8n instance
- **Firewall settings**: Open necessary ports for webhook communication
- **SSL certificates**: Use HTTPS for production webhook URLs

### Security Considerations
- **API key rotation**: Regularly update all API keys
- **Webhook authentication**: Consider adding authentication to n8n webhooks
- **Rate limiting**: Monitor API usage to avoid unexpected charges

### Cost Management
- **OpenAI costs**: ~$0.006/minute for Whisper transcription
- **Anthropic costs**: ~$0.50/1K tokens for content analysis
- **GitHub Actions**: Free tier includes 2,000 minutes/month

## 🚀 Next Steps After GitHub Actions Setup

1. **Monitor first few runs** to ensure data collection works
2. **Validate webhook communication** between GitHub Actions and n8n
3. **Test emergency alert system** with sample data
4. **Configure subscriber management** in your n8n workflow
5. **Set up monitoring dashboards** for system health
6. **Launch with beta subscriber group** before full deployment

---

## 📞 Troubleshooting

### Common Issues:

**GitHub Actions can't reach n8n webhooks:**
- Check if n8n is accessible from outside Docker network
- Verify webhook URLs in repository secrets
- Test webhook connectivity manually

**API rate limits exceeded:**
- Check current usage in API dashboards
- Implement request batching in workflows
- Add retry logic with exponential backoff

**Workflow execution failures:**
- Review GitHub Actions logs for specific errors
- Check n8n execution logs
- Verify all required secrets are configured

Need help with any of these steps? I can provide more detailed guidance for your specific setup!