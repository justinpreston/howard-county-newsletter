// Test setup and configuration
require('dotenv').config();

// Global test timeout
jest.setTimeout(30000);

// Mock console methods for cleaner test output
const originalConsole = { ...console };

beforeAll(() => {
  // Suppress console.warn in tests unless explicitly needed
  console.warn = jest.fn((message) => {
    if (process.env.TEST_VERBOSE === 'true') {
      originalConsole.warn(message);
    }
  });
});

afterAll(() => {
  // Restore console methods
  Object.assign(console, originalConsole);
});

// Global test helpers
global.testHelpers = {
  delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),
  
  generateTestId: () => `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
  
  validateResponse: (response, expectedStatus = 200) => {
    expect(response).toBeDefined();
    expect(response.status).toBe(expectedStatus);
    return response;
  },

  skipIfMissing: (envVar, testName) => {
    if (!process.env[envVar]) {
      console.warn(`Skipping ${testName} - ${envVar} not configured`);
      return true;
    }
    return false;
  }
};

// Environment validation
const criticalEnvVars = ['NODE_ENV'];
const missingCritical = criticalEnvVars.filter(envVar => !process.env[envVar]);

if (missingCritical.length > 0) {
  console.warn(`Missing critical environment variables: ${missingCritical.join(', ')}`);
}

// Set test environment if not specified
if (!process.env.NODE_ENV) {
  process.env.NODE_ENV = 'test';
}