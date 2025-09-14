// Example: Video Embed Generator Node
// This node creates embeddable video players for Howard County meeting recordings
// Generates HTML embed codes for newsletter integration with Granicus video platform

const embedNode = {
  name: "Generate Video Embeds",
  type: "n8n-nodes-base.code",
  parameters: {
    code: `
      // Generate embeddable video players for newsletter
      const videos = $json.recent_videos;
      const embeds = [];
      
      videos.forEach(video => {
        // Granicus embed format
        const embedCode = \`
          <div style="position: relative; padding-bottom: 56.25%; height: 0;">
            <iframe 
              src="https://howardcounty.granicus.com/player/clip/\${video.clip_id}?view_id=2"
              style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"
              frameborder="0"
              allowfullscreen>
            </iframe>
          </div>
          <p><a href="https://howardcounty.granicus.com/MediaPlayer.php?clip_id=\${video.clip_id}">
            Watch: \${video.title}
          </a></p>
        \`;
        
        embeds.push({
          title: video.title,
          date: video.date,
          embed_code: embedCode,
          direct_link: video.url
        });
      });
      
      return embeds;
    `,
  },
};

// Export for use in n8n workflow
module.exports = embedNode;

// Usage Notes:
// 1. This node expects input with 'recent_videos' field containing video data
// 2. Generates responsive HTML embed codes for Granicus video platform
// 3. Creates both embedded players and direct links for accessibility
// 4. Optimized for email newsletter HTML templates
// 5. Follows Howard County's Granicus integration standards
//
// Input Data Structure:
// recent_videos: [
//   {
//     clip_id: "12345",
//     title: "County Council Meeting - September 14, 2025",
//     date: "2025-09-14",
//     url: "https://howardcounty.granicus.com/MediaPlayer.php?clip_id=12345"
//   }
// ]
//
// Output Structure:
// [
//   {
//     title: "County Council Meeting - September 14, 2025",
//     date: "2025-09-14",
//     embed_code: "<div style=\"...\">...</div>",
//     direct_link: "https://howardcounty.granicus.com/MediaPlayer.php?clip_id=12345"
//   }
// ]
//
// Howard County Video Sources:
// - County Council Meetings
// - Planning Board Sessions
// - Board of Education Meetings
// - Public Hearings
// - Community Forums
// - Department Presentations
// - Special Events and Ceremonies
//
// Granicus Platform Features:
// - Responsive video player design
// - Mobile-friendly viewing experience
// - Accessibility compliance (WCAG 2.1)
// - Automatic transcription capabilities
// - Chapter navigation for long meetings
// - Multiple quality options for bandwidth
//
// Email Integration Tips:
// 1. Test embed codes in major email clients (Gmail, Outlook, Apple Mail)
// 2. Provide fallback links for clients that don't support iframes
// 3. Consider thumbnail images for better visual appeal
// 4. Include meeting agendas and timestamps for key discussions
// 5. Add captions and transcription links for accessibility
//
// Responsive Design:
// - 16:9 aspect ratio maintained across devices
// - Padding-bottom: 56.25% creates responsive container
// - Absolute positioning ensures proper scaling
// - Works on desktop, tablet, and mobile devices
//
// Accessibility Considerations:
// - Provide text descriptions for video content
// - Include links to official transcripts
// - Offer multiple viewing options
// - Ensure keyboard navigation compatibility
//
// Performance Optimization:
// - Lazy loading for multiple videos
// - Thumbnail previews to reduce initial load
// - CDN delivery through Granicus platform
// - Bandwidth-adaptive streaming
//
// Integration Examples:
//
// Newsletter Section:
// <h2>Recent Meetings</h2>
// <div class="video-section">
//   {embed_code}
//   <div class="video-info">
//     <h3>{title}</h3>
//     <p>Meeting Date: {date}</p>
//     <p><a href="{direct_link}">View Full Recording</a></p>
//   </div>
// </div>
//
// Common Granicus URLs:
// - Player: https://howardcounty.granicus.com/player/clip/{clip_id}
// - MediaPlayer: https://howardcounty.granicus.com/MediaPlayer.php?clip_id={clip_id}
// - Archive: https://howardcounty.granicus.com/ViewPublisher.php?view_id=2
//
// Workflow Integration:
// 1. Fetch recent videos from Granicus API or web scraping
// 2. Filter videos by date range and relevance
// 3. Generate embed codes using this node
// 4. Include in newsletter template compilation
// 5. Test embed functionality before sending
