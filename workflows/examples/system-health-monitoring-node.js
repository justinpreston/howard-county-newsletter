// Example: System Health Check Monitoring Node
// This node monitors the overall health of the Howard County newsletter system
// Tracks key metrics and alerts administrators to potential issues

const monitoringNode = {
  name: "System Health Check",
  type: "n8n-nodes-base.code",
  parameters: {
    code: `
      const metrics = {
        timestamp: new Date().toISOString(),
        checks: []
      };
      
      // Check scraping success rate
      const scrapingStats = await $node['PostgreSQL'].executeQuery(
        "SELECT COUNT(*) as total, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful FROM scraping_logs WHERE created_at > NOW() - INTERVAL '24 hours'"
      );
      
      metrics.checks.push({
        name: 'Scraping Success Rate',
        value: (scrapingStats.successful / scrapingStats.total) * 100,
        threshold: 80,
        status: scrapingStats.successful / scrapingStats.total > 0.8 ? 'healthy' : 'warning'
      });
      
      // Check AI API response times
      const aiResponseTimes = await $node['PostgreSQL'].executeQuery(
        "SELECT AVG(response_time_ms) as avg_time FROM ai_api_logs WHERE created_at > NOW() - INTERVAL '1 hour'"
      );
      
      metrics.checks.push({
        name: 'AI API Response Time',
        value: aiResponseTimes.avg_time,
        threshold: 3000,
        status: aiResponseTimes.avg_time < 3000 ? 'healthy' : 'warning'
      });
      
      // Check subscriber growth
      const subscriberGrowth = await $node['PostgreSQL'].executeQuery(
        "SELECT (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY DATE(created_at))) as daily_growth FROM subscribers WHERE created_at > NOW() - INTERVAL '7 days' GROUP BY DATE(created_at)"
      );
      
      metrics.checks.push({
        name: 'Subscriber Growth',
        value: subscriberGrowth.daily_growth,
        threshold: 0,
        status: subscriberGrowth.daily_growth >= 0 ? 'healthy' : 'warning'
      });
      
      // Check email delivery rate
      const emailStats = await $node['SendGrid'].getStats({
        start_date: new Date(Date.now() - 86400000).toISOString().split('T')[0]
      });
      
      const deliveryRate = (emailStats.delivered / emailStats.requests) * 100;
      metrics.checks.push({
        name: 'Email Delivery Rate',
        value: deliveryRate,
        threshold: 95,
        status: deliveryRate > 95 ? 'healthy' : 'critical'
      });
      
      // Alert if any critical issues
      const criticalIssues = metrics.checks.filter(check => check.status === 'critical');
      if (criticalIssues.length > 0) {
        // Trigger alert
        await $node['Send Alert'].execute({
          message: 'Critical issues detected in newsletter system',
          issues: criticalIssues
        });
      }
      
      return metrics;
    `,
  },
};

// Export for use in n8n workflow
module.exports = monitoringNode;

// Usage Notes:
// 1. This node requires PostgreSQL database access for metrics queries
// 2. Integrates with SendGrid for email delivery statistics
// 3. Monitors multiple aspects of system health and performance
// 4. Automatically triggers alerts for critical issues
// 5. Should be run on a regular schedule (hourly or daily)
//
// Required Database Tables:
// - scraping_logs: Tracks web scraping operations and success rates
// - ai_api_logs: Records AI API calls and response times
// - subscribers: Newsletter subscriber database with creation timestamps
//
// Monitored Metrics:
// 1. Scraping Success Rate (24-hour window, threshold: 80%)
// 2. AI API Response Time (1-hour average, threshold: 3000ms)
// 3. Subscriber Growth (daily growth trend, threshold: 0 or positive)
// 4. Email Delivery Rate (daily statistics, threshold: 95%)
//
// Health Status Levels:
// - healthy: All metrics within acceptable thresholds
// - warning: Metrics approaching concerning levels
// - critical: Metrics indicating system issues requiring immediate attention
//
// Workflow Integration:
// 1. Schedule this node to run hourly or daily
// 2. Connect to alert mechanisms for critical issues
// 3. Store metrics in dashboard or reporting system
// 4. Use outputs to trigger maintenance workflows
//
// Database Schema Requirements:
//
// CREATE TABLE scraping_logs (
//   id SERIAL PRIMARY KEY,
//   source VARCHAR(255),
//   status VARCHAR(50),
//   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
// );
//
// CREATE TABLE ai_api_logs (
//   id SERIAL PRIMARY KEY,
//   provider VARCHAR(100),
//   response_time_ms INTEGER,
//   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
// );
//
// CREATE TABLE subscribers (
//   id SERIAL PRIMARY KEY,
//   email VARCHAR(255),
//   status VARCHAR(50),
//   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
// );
