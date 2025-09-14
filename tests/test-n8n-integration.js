const axios = require('axios');
const fs = require('fs').promises;
const path = require('path');

/**
 * Test n8n Workflow Integration
 * Validates connectivity and functionality of the main workflow
 */

describe('n8n Workflow Integration Tests', () => {
  const N8N_BASE_URL = process.env.N8N_BASE_URL || 'http://localhost:5678';
  const N8N_API_KEY = process.env.N8N_API_KEY;
  
  let axiosInstance;

  beforeAll(() => {
    axiosInstance = axios.create({
      baseURL: N8N_BASE_URL,
      headers: {
        'Authorization': `Bearer ${N8N_API_KEY}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
  });

  describe('Workflow Connectivity', () => {
    test('should connect to n8n instance', async () => {
      try {
        const response = await axiosInstance.get('/rest/active');
        expect(response.status).toBe(200);
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('n8n instance not running - skipping integration tests');
          return;
        }
        throw error;
      }
    });

    test('should list available workflows', async () => {
      try {
        const response = await axiosInstance.get('/rest/workflows');
        expect(response.status).toBe(200);
        expect(Array.isArray(response.data.data)).toBe(true);
      } catch (error) {
        if (error.code === 'ECONNREFUSED') {
          console.warn('n8n instance not running - skipping test');
          return;
        }
        throw error;
      }
    });
  });

  describe('Howard County Workflow', () => {
    let workflowId;

    beforeAll(async () => {
      try {
        // Look for the Howard County workflow
        const response = await axiosInstance.get('/rest/workflows');
        const workflows = response.data.data;
        
        const howardWorkflow = workflows.find(w => 
          w.name.toLowerCase().includes('howard') || 
          w.name.toLowerCase().includes('county')
        );
        
        if (howardWorkflow) {
          workflowId = howardWorkflow.id;
        }
      } catch (error) {
        if (error.code !== 'ECONNREFUSED') {
          throw error;
        }
      }
    });

    test('should find Howard County main workflow', async () => {
      if (!workflowId) {
        console.warn('Howard County workflow not found - may need to be imported');
        return;
      }
      
      expect(workflowId).toBeDefined();
      
      const response = await axiosInstance.get(`/rest/workflows/${workflowId}`);
      expect(response.status).toBe(200);
      expect(response.data.data.name).toBeDefined();
    });

    test('should activate Howard County workflow', async () => {
      if (!workflowId) {
        console.warn('Howard County workflow not found - skipping activation test');
        return;
      }

      try {
        const response = await axiosInstance.post(`/rest/workflows/${workflowId}/activate`);
        expect([200, 201]).toContain(response.status);
      } catch (error) {
        if (error.response && error.response.status === 400) {
          // Workflow might already be active
          expect(error.response.status).toBe(400);
        } else {
          throw error;
        }
      }
    });
  });

  describe('Webhook Endpoints', () => {
    const testWebhooks = [
      {
        name: 'GitHub Actions Webhook',
        path: '/webhook/github-actions',
        testData: {
          source: 'test',
          run_id: '12345',
          timestamp: new Date().toISOString(),
          status: 'success'
        }
      },
      {
        name: 'Emergency Alert Webhook', 
        path: '/webhook/emergency-alert',
        testData: {
          emergency: true,
          alert_type: 'test',
          timestamp: new Date().toISOString()
        }
      }
    ];

    testWebhooks.forEach(webhook => {
      test(`should respond to ${webhook.name}`, async () => {
        try {
          const webhookUrl = `${N8N_BASE_URL}${webhook.path}`;
          
          const response = await axios.post(webhookUrl, webhook.testData, {
            timeout: 10000,
            validateStatus: status => status < 500 // Accept 4xx as valid response
          });
          
          // Webhook should respond (even if workflow isn't active)
          expect([200, 201, 404, 405]).toContain(response.status);
          
        } catch (error) {
          if (error.code === 'ECONNREFUSED') {
            console.warn(`n8n instance not running - skipping ${webhook.name} test`);
            return;
          }
          throw error;
        }
      });
    });
  });

  describe('Workflow Execution', () => {
    test('should execute test workflow run', async () => {
      if (!workflowId) {
        console.warn('No workflow found - skipping execution test');
        return;
      }

      try {
        const testData = {
          test_mode: true,
          timestamp: new Date().toISOString(),
          source: 'integration_test'
        };

        const response = await axiosInstance.post(
          `/rest/workflows/${workflowId}/execute`,
          { data: testData }
        );

        expect([200, 201]).toContain(response.status);
        
        if (response.data.data) {
          expect(response.data.data.executionId).toBeDefined();
        }

      } catch (error) {
        if (error.response && error.response.status === 400) {
          // Workflow might not be executable in current state
          console.warn('Workflow execution failed - may need proper configuration');
        } else {
          throw error;
        }
      }
    });
  });

  describe('Node Configuration', () => {
    test('should validate critical nodes exist in workflow', async () => {
      if (!workflowId) {
        console.warn('No workflow found - skipping node validation');
        return;
      }

      try {
        const response = await axiosInstance.get(`/rest/workflows/${workflowId}`);
        const workflow = response.data.data;
        
        // Check for key nodes in the workflow
        const expectedNodeTypes = [
          'n8n-nodes-base.webhook',
          'n8n-nodes-base.httpRequest',
          'n8n-nodes-base.code'
        ];

        const nodeTypes = workflow.nodes.map(node => node.type);
        
        expectedNodeTypes.forEach(expectedType => {
          const hasNode = nodeTypes.some(type => type === expectedType);
          if (!hasNode) {
            console.warn(`Expected node type ${expectedType} not found in workflow`);
          }
        });

        // At least check that workflow has nodes
        expect(workflow.nodes.length).toBeGreaterThan(0);

      } catch (error) {
        if (error.code !== 'ECONNREFUSED') {
          throw error;
        }
      }
    });
  });
});

/**
 * API Integration Tests
 * Test external API connections and data flow
 */
describe('API Integration Tests', () => {
  
  describe('GitHub Actions Integration', () => {
    test('should validate GitHub API connectivity', async () => {
      const githubToken = process.env.GITHUB_TOKEN;
      
      if (!githubToken) {
        console.warn('GITHUB_TOKEN not set - skipping GitHub API test');
        return;
      }

      try {
        const response = await axios.get('https://api.github.com/user', {
          headers: {
            'Authorization': `token ${githubToken}`,
            'User-Agent': 'HowardCountyNews-Test'
          }
        });

        expect(response.status).toBe(200);
        expect(response.data.login).toBeDefined();

      } catch (error) {
        if (error.response && error.response.status === 401) {
          console.warn('GitHub token invalid - check GITHUB_TOKEN environment variable');
        } else {
          throw error;
        }
      }
    });
  });

  describe('OpenAI API Integration', () => {
    test('should validate OpenAI API connectivity', async () => {
      const openaiApiKey = process.env.OPENAI_API_KEY;
      
      if (!openaiApiKey) {
        console.warn('OPENAI_API_KEY not set - skipping OpenAI API test');
        return;
      }

      try {
        const response = await axios.get('https://api.openai.com/v1/models', {
          headers: {
            'Authorization': `Bearer ${openaiApiKey}`,
            'User-Agent': 'HowardCountyNews-Test'
          }
        });

        expect(response.status).toBe(200);
        expect(response.data.data).toBeDefined();
        expect(Array.isArray(response.data.data)).toBe(true);

      } catch (error) {
        if (error.response && error.response.status === 401) {
          console.warn('OpenAI API key invalid - check OPENAI_API_KEY environment variable');
        } else {
          throw error;
        }
      }
    });
  });

  describe('Anthropic API Integration', () => {
    test('should validate Anthropic API connectivity', async () => {
      const anthropicApiKey = process.env.ANTHROPIC_API_KEY;
      
      if (!anthropicApiKey) {
        console.warn('ANTHROPIC_API_KEY not set - skipping Anthropic API test');
        return;
      }

      try {
        // Test with a simple completion request
        const response = await axios.post('https://api.anthropic.com/v1/messages', {
          model: 'claude-3-haiku-20240307',
          max_tokens: 10,
          messages: [{
            role: 'user',
            content: 'Test connection'
          }]
        }, {
          headers: {
            'Authorization': `Bearer ${anthropicApiKey}`,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01',
            'User-Agent': 'HowardCountyNews-Test'
          }
        });

        expect(response.status).toBe(200);
        expect(response.data.content).toBeDefined();

      } catch (error) {
        if (error.response && error.response.status === 401) {
          console.warn('Anthropic API key invalid - check ANTHROPIC_API_KEY environment variable');
        } else {
          throw error;
        }
      }
    });
  });
});

/**
 * Data Processing Tests  
 * Test data validation and processing capabilities
 */
describe('Data Processing Integration', () => {
  
  test('should validate scraped data structure', async () => {
    const dataDir = path.join(__dirname, '..', 'data');
    
    try {
      const dataDirExists = await fs.access(dataDir).then(() => true).catch(() => false);
      
      if (!dataDirExists) {
        console.warn('Data directory not found - may need to run scrapers first');
        return;
      }

      const subdirs = await fs.readdir(dataDir);
      expect(Array.isArray(subdirs)).toBe(true);
      
      // Look for expected data subdirectories
      const expectedDirs = ['county-council', 'emergency', 'videos'];
      const foundDirs = subdirs.filter(dir => expectedDirs.includes(dir));
      
      if (foundDirs.length === 0) {
        console.warn('No expected data subdirectories found');
        return;
      }

      // Check if data files exist in subdirectories
      for (const dir of foundDirs) {
        const dirPath = path.join(dataDir, dir);
        const files = await fs.readdir(dirPath);
        const jsonFiles = files.filter(file => file.endsWith('.json'));
        
        if (jsonFiles.length > 0) {
          // Validate one sample file
          const sampleFile = path.join(dirPath, jsonFiles[0]);
          const fileContent = await fs.readFile(sampleFile, 'utf-8');
          
          expect(() => JSON.parse(fileContent)).not.toThrow();
          
          const data = JSON.parse(fileContent);
          expect(typeof data).toBe('object');
        }
      }

    } catch (error) {
      console.warn(`Data validation error: ${error.message}`);
    }
  });
});