# Emergency Alert Monitor Subworkflow

## Overview

The Emergency Alert Monitor is a critical subworkflow designed to provide real-time emergency notifications to Howard County residents. It monitors multiple emergency feeds and sends immediate alerts through SMS, email, and push notifications for critical situations.

## Features

### Multi-Source Monitoring

- **Police Alerts**: Howard County Police Department emergency notifications
- **Weather Warnings**: National Weather Service alerts for Maryland
- **School Closures**: Howard County Public School System closure announcements

### Smart Filtering

Automatically identifies critical alerts based on:

- Severity levels (extreme, severe)
- Critical keywords (evacuation, shelter in place, tornado warning, etc.)
- Area impact assessment

### Multi-Channel Notifications

- **SMS Alerts**: Immediate text messages via Twilio
- **Email Alerts**: HTML-formatted emergency emails via SendGrid
- **Push Notifications**: Mobile app notifications via Firebase Cloud Messaging

### Alert Management

- Deduplication to prevent spam
- 24-hour alert tracking
- Comprehensive logging for audit trails

## Setup Requirements

### Prerequisites

1. **Database Table**: Create the `emergency_alerts` table:

```sql
CREATE TABLE emergency_alerts (
  id SERIAL PRIMARY KEY,
  alert_hash VARCHAR(255) UNIQUE,
  type VARCHAR(100),
  message TEXT,
  area VARCHAR(255),
  severity VARCHAR(50),
  sent_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Required Credentials

Configure these in your n8n credentials:

1. **Twilio Credentials**

   - Account SID
   - Auth Token
   - From Phone Number: +14435551234 (update with actual number)

2. **SendGrid Credentials**

   - API Key
   - From Email Address

3. **Firebase Credentials** (for push notifications)

   - Server Key for FCM

4. **PostgreSQL Database**
   - Connection details for alert logging

### API Endpoints

Verify these endpoints are accessible:

- Howard County Police: `https://www.howardcountymd.gov/police/alerts/feed`
- Weather Service: `https://api.weather.gov/alerts/active?area=MD`
- School Closures: `https://www.hcpss.org/closures/api`

## Configuration

### Critical Keywords

The workflow flags alerts containing these terms:

- evacuation
- shelter in place
- active shooter
- tornado warning
- flash flood warning
- hazmat
- school closure
- boil water
- power outage

### Polling Frequency

- Default: Every 15 minutes
- Can be adjusted in the Schedule Trigger node

### Message Formatting

- **SMS**: 140 character limit with unsubscribe option
- **Email**: HTML format with emergency styling
- **Push**: 100 character limit for mobile notifications

## Integration with Main Newsletter Workflow

### Option 1: Standalone Operation

Run as an independent workflow for real-time emergency monitoring.

### Option 2: Newsletter Integration

Connect to main newsletter workflow to:

- Include emergency summaries in regular newsletters
- Track emergency response metrics
- Generate emergency preparedness content

## Testing & Validation

### Test Scenarios

1. **Mock Emergency**: Test with sample alert data
2. **Channel Verification**: Confirm all notification methods work
3. **Deduplication**: Verify repeated alerts are filtered
4. **Database Logging**: Check alert storage and retrieval

### Monitoring

- Monitor workflow execution logs
- Track notification delivery rates
- Review false positive/negative rates

## Maintenance

### Regular Updates

- Update Howard County official contact lists
- Verify API endpoint availability
- Review and adjust critical keywords
- Test notification channels monthly

### Performance Optimization

- Monitor API response times
- Adjust polling frequency based on system load
- Optimize database queries for large alert volumes

## Security Considerations

### Data Protection

- Secure credential storage in n8n
- Encrypt sensitive alert data
- Implement proper access controls

### Rate Limiting

- Respect API rate limits for external services
- Implement backoff strategies for failed requests
- Monitor notification volume to prevent spam

## Compliance & Legal

### Emergency Communications

- Ensure compliance with emergency notification regulations
- Maintain audit trails for all sent alerts
- Implement proper opt-out mechanisms

### Data Retention

- Store alerts for regulatory compliance
- Implement data archival policies
- Regular backup of emergency communication logs

## Troubleshooting

### Common Issues

1. **API Failures**: Check endpoint availability and credentials
2. **Missing Alerts**: Verify polling schedule and filtering logic
3. **Duplicate Notifications**: Check deduplication logic and database connectivity
4. **Delivery Failures**: Validate notification service credentials and recipient data

### Support Contacts

- Technical Support: IT Department
- Emergency Management: Howard County Emergency Services
- Public Information: County Communications Office
