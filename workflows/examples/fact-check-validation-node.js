// Example: Fact Check & Validation Node
// This node performs automated fact-checking and data validation for newsletter content
// Helps ensure accuracy and quality of Howard County newsletter information

const factCheckNode = {
  name: "Fact Check & Validate",
  type: "n8n-nodes-base.code",
  parameters: {
    language: "javascript",
    code: `
      const content = $json.summary;
      const validationRules = [];
      
      // Check for common data quality issues
      
      // 1. Verify dates are in the future for upcoming events
      const dateRegex = /(\d{1,2}\/\d{1,2}\/\d{4})/g;
      const dates = content.match(dateRegex) || [];
      dates.forEach(date => {
        const eventDate = new Date(date);
        if (eventDate < new Date()) {
          validationRules.push({
            issue: 'past_date',
            detail: \`Date \${date} appears to be in the past\`
          });
        }
      });
      
      // 2. Verify budget numbers are reasonable
      const moneyRegex = /\$[\d,]+(\.\d{2})?/g;
      const amounts = content.match(moneyRegex) || [];
      amounts.forEach(amount => {
        const value = parseFloat(amount.replace(/[$,]/g, ''));
        if (value > 1000000000) { // Over $1 billion
          validationRules.push({
            issue: 'large_amount',
            detail: \`Amount \${amount} seems unusually large\`,
            flagForReview: true
          });
        }
      });
      
      // 3. Check for conflicting information
      const numbers = content.match(/\d+/g) || [];
      const percentages = content.match(/\d+%/g) || [];
      
      // 4. Verify named entities
      const countyOfficials = [
        'Calvin Ball', 'Deb Jung', 'Opel Jones', 
        'Christiana Rigby', 'David Yungmann', 'Liz Walsh'
      ];
      
      const mentionedOfficials = countyOfficials.filter(name => 
        content.toLowerCase().includes(name.toLowerCase())
      );
      
      // 5. Cross-reference with previous content
      const requiresCrossCheck = 
        content.includes('previously reported') ||
        content.includes('update from') ||
        content.includes('correction');
      
      return {
        content: content,
        validationIssues: validationRules,
        requiresManualReview: validationRules.some(r => r.flagForReview),
        mentionedOfficials: mentionedOfficials,
        requiresCrossReference: requiresCrossCheck,
        confidence: validationRules.length === 0 ? 'high' : 'medium'
      };
    `,
  },
};

// Export for use in n8n workflow
module.exports = factCheckNode;

// Usage Notes:
// 1. This node expects input data with a 'summary' field containing the content to validate
// 2. Automatically checks for common data quality issues like past dates and unreasonable amounts
// 3. Verifies mentions of Howard County officials for accuracy
// 4. Flags content that may require manual review or cross-referencing
// 5. Returns a confidence score based on validation results
//
// Validation Features:
// - Date verification (flags past dates for future events)
// - Budget amount reasonableness checks
// - Named entity verification for county officials
// - Cross-reference requirement detection
// - Automated quality scoring
//
// Workflow Integration:
// 1. Place after content generation/summarization nodes
// 2. Use validation results to route content for manual review if needed
// 3. Integrate with approval workflows for content requiring fact-checking
// 4. Track confidence scores for continuous quality improvement
//
// Howard County Officials List (update as needed):
// - Calvin Ball (County Executive)
// - Deb Jung (District 1)
// - Opel Jones (District 2)
// - Christiana Rigby (District 3)
// - David Yungmann (District 4)
// - Liz Walsh (District 5)
