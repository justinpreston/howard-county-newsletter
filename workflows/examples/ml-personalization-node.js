// Example: Machine Learning-Based Content Personalization Node
// This node uses ML algorithms to personalize newsletter content for each subscriber
// Creates tailored content recommendations based on preferences and engagement history

const mlPersonalizationNode = {
  name: "ML Personalization",
  type: "n8n-nodes-base.code",
  parameters: {
    code: `
      const subscriber = $json.subscriber;
      const allContent = $json.available_content;
      
      // Calculate relevance scores
      const scoredContent = allContent.map(item => {
        let score = 0;
        
        // Geographic relevance (0-40 points)
        if (item.neighborhoods.includes(subscriber.neighborhood)) {
          score += 40;
        } else if (item.neighborhoods.includes('county_wide')) {
          score += 20;
        }
        
        // Topic preference match (0-30 points)
        const topicMatch = item.topics.filter(topic => 
          subscriber.preferences.topics.includes(topic)
        ).length;
        score += (topicMatch * 10);
        
        // Engagement history (0-20 points)
        const previousEngagement = subscriber.engagement_history
          .filter(h => h.topic === item.primary_topic);
        if (previousEngagement.length > 0) {
          const avgEngagement = previousEngagement
            .reduce((sum, e) => sum + e.score, 0) / previousEngagement.length;
          score += (avgEngagement * 20);
        }
        
        // Recency bonus (0-10 points)
        const hoursSincePublished = 
          (Date.now() - new Date(item.created_at)) / (1000 * 60 * 60);
        if (hoursSincePublished < 24) {
          score += 10;
        } else if (hoursSincePublished < 72) {
          score += 5;
        }
        
        return {
          ...item,
          relevance_score: score,
          explanation: \`Neighborhood: \${item.neighborhoods.includes(subscriber.neighborhood) ? 'Yes' : 'No'}, Topics: \${topicMatch}/\${item.topics.length}\`
        };
      });
      
      // Sort by relevance and select top stories
      const personalizedContent = scoredContent
        .sort((a, b) => b.relevance_score - a.relevance_score)
        .slice(0, 10);
      
      // Group by section
      const sections = {
        top_stories: personalizedContent.slice(0, 3),
        your_neighborhood: personalizedContent
          .filter(item => item.neighborhoods.includes(subscriber.neighborhood))
          .slice(0, 3),
        your_interests: personalizedContent
          .filter(item => item.topics.some(t => subscriber.preferences.topics.includes(t)))
          .slice(0, 4)
      };
      
      return {
        subscriber_email: subscriber.email,
        personalized_sections: sections,
        personalization_metadata: {
          total_articles: allContent.length,
          selected_articles: personalizedContent.length,
          avg_relevance_score: personalizedContent
            .reduce((sum, item) => sum + item.relevance_score, 0) / personalizedContent.length
        }
      };
    `,
  },
};

// Export for use in n8n workflow
module.exports = mlPersonalizationNode;

// Usage Notes:
// 1. This node expects input with 'subscriber' and 'available_content' fields
// 2. Implements a scoring algorithm based on multiple relevance factors
// 3. Creates personalized content sections for each subscriber
// 4. Returns structured data ready for email template rendering
// 5. Includes metadata for analytics and continuous improvement
//
// Input Data Structure:
// subscriber: {
//   email: string,
//   neighborhood: string,
//   preferences: {
//     topics: string[]
//   },
//   engagement_history: [
//     { topic: string, score: number }
//   ]
// }
//
// available_content: [
//   {
//     id: string,
//     title: string,
//     content: string,
//     topics: string[],
//     neighborhoods: string[],
//     primary_topic: string,
//     created_at: timestamp
//   }
// ]
//
// Scoring Algorithm:
// 1. Geographic Relevance (0-40 points):
//    - 40 points: Content specifically for subscriber's neighborhood
//    - 20 points: County-wide content applicable to all areas
//    - 0 points: Content for other specific neighborhoods
//
// 2. Topic Preference Match (0-30 points):
//    - 10 points per matching topic between content and subscriber preferences
//    - Maximum 30 points for highly relevant content
//
// 3. Engagement History (0-20 points):
//    - Based on subscriber's past engagement with similar topics
//    - Uses average engagement score for the content's primary topic
//    - Helps predict future interest based on behavior
//
// 4. Recency Bonus (0-10 points):
//    - 10 points: Content published within 24 hours
//    - 5 points: Content published within 72 hours
//    - 0 points: Older content
//
// Howard County Neighborhoods:
// - Columbia
// - Ellicott City
// - Laurel
// - Jessup
// - Savage
// - Fulton
// - Clarksville
// - Dayton
// - Glenelg
// - Highland
// - Lisbon
// - Marriottsville
// - Mount Airy
// - Sykesville
// - West Friendship
// - Woodbine
// - county_wide (for general Howard County news)
//
// Common Topics:
// - local_government
// - public_safety
// - education
// - transportation
// - environment
// - community_events
// - business_development
// - parks_recreation
// - public_health
// - zoning_development
//
// Output Sections:
// - top_stories: 3 highest-scoring articles regardless of category
// - your_neighborhood: 3 articles specific to subscriber's neighborhood
// - your_interests: 4 articles matching subscriber's topic preferences
//
// Integration Tips:
// 1. Run this node for each subscriber before email generation
// 2. Use output sections to populate email template sections
// 3. Track engagement metrics to improve future personalization
// 4. A/B test different scoring weights to optimize engagement
// 5. Store personalization metadata for analytics and reporting
