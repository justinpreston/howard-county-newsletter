#!/usr/bin/env python3
"""
Data Validation Script for Scraped Government Data
Validates data quality and completeness
"""

import os
import json
import sys
import argparse
from datetime import datetime
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self, source: str):
        self.source = source
        self.data_dir = f"data/{source}"
        self.validation_results = {
            'source': source,
            'validation_timestamp': datetime.utcnow().isoformat(),
            'files_validated': 0,
            'errors': [],
            'warnings': [],
            'data_quality_score': 0.0
        }

    def validate_source_data(self) -> Dict[str, Any]:
        """Validate all data files for the specified source"""
        
        if not os.path.exists(self.data_dir):
            logger.error(f"Data directory not found: {self.data_dir}")
            self.validation_results['errors'].append(f"Data directory not found: {self.data_dir}")
            return self.validation_results

        # Get all JSON files in the data directory
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        
        if not json_files:
            self.validation_results['warnings'].append("No JSON data files found")
            return self.validation_results

        logger.info(f"Validating {len(json_files)} files for {self.source}")

        for filename in json_files:
            file_path = os.path.join(self.data_dir, filename)
            try:
                self.validate_json_file(file_path)
                self.validation_results['files_validated'] += 1
            except Exception as e:
                error_msg = f"Error validating {filename}: {str(e)}"
                logger.error(error_msg)
                self.validation_results['errors'].append(error_msg)

        # Calculate quality score
        self.calculate_quality_score()
        
        return self.validation_results

    def validate_json_file(self, file_path: str):
        """Validate individual JSON file"""
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        filename = os.path.basename(file_path)
        
        # Basic structure validation
        if not isinstance(data, dict):
            raise ValueError(f"{filename}: Root data must be a dictionary")

        # Check for required fields based on source
        if self.source == 'county-council':
            self.validate_council_data(data, filename)
        elif self.source == 'emergency':
            self.validate_emergency_data(data, filename)
        elif self.source == 'videos':
            self.validate_video_data(data, filename)
        else:
            self.validate_generic_data(data, filename)

    def validate_council_data(self, data: Dict[str, Any], filename: str):
        """Validate county council data structure"""
        
        required_fields = ['scrape_timestamp', 'source', 'data']
        for field in required_fields:
            if field not in data:
                self.validation_results['errors'].append(f"{filename}: Missing required field '{field}'")

        if 'data' in data:
            council_data = data['data']
            
            # Check for expected data sections
            expected_sections = ['upcoming_meetings', 'recent_minutes', 'council_members']
            for section in expected_sections:
                if section not in council_data:
                    self.validation_results['warnings'].append(f"{filename}: Missing data section '{section}'")
                elif not isinstance(council_data[section], list):
                    self.validation_results['errors'].append(f"{filename}: '{section}' should be a list")

            # Validate meeting data quality
            meetings = council_data.get('upcoming_meetings', [])
            for i, meeting in enumerate(meetings):
                if not meeting.get('title'):
                    self.validation_results['warnings'].append(f"{filename}: Meeting {i} missing title")
                if not meeting.get('date'):
                    self.validation_results['warnings'].append(f"{filename}: Meeting {i} missing date")

    def validate_emergency_data(self, data: Dict[str, Any], filename: str):
        """Validate emergency alert data structure"""
        
        if 'alerts' in filename:
            required_fields = ['check_timestamp']
        else:
            required_fields = ['all_alerts', 'critical_alerts', 'feed_statuses']

        for field in required_fields:
            if field not in data:
                self.validation_results['errors'].append(f"{filename}: Missing required field '{field}'")

        # Validate alert structure
        if 'all_alerts' in data:
            alerts = data['all_alerts']
            if not isinstance(alerts, list):
                self.validation_results['errors'].append(f"{filename}: 'all_alerts' should be a list")
            else:
                for i, alert in enumerate(alerts):
                    if not alert.get('title'):
                        self.validation_results['warnings'].append(f"{filename}: Alert {i} missing title")
                    if not alert.get('source'):
                        self.validation_results['warnings'].append(f"{filename}: Alert {i} missing source")

    def validate_video_data(self, data: Dict[str, Any], filename: str):
        """Validate video processing data structure"""
        
        required_fields = ['discovery_timestamp', 'videos_discovered', 'processing_results']
        for field in required_fields:
            if field not in data:
                self.validation_results['errors'].append(f"{filename}: Missing required field '{field}'")

        # Validate video processing results
        if 'processing_results' in data:
            results = data['processing_results']
            if not isinstance(results, list):
                self.validation_results['errors'].append(f"{filename}: 'processing_results' should be a list")
            else:
                for i, result in enumerate(results):
                    if 'status' not in result:
                        self.validation_results['warnings'].append(f"{filename}: Processing result {i} missing status")
                    if result.get('status') == 'success' and not result.get('transcript_path'):
                        self.validation_results['warnings'].append(f"{filename}: Successful processing {i} missing transcript path")

    def validate_generic_data(self, data: Dict[str, Any], filename: str):
        """Validate generic data structure"""
        
        # Check for timestamp
        timestamp_fields = ['timestamp', 'scraped_at', 'created_at', 'updated_at']
        has_timestamp = any(field in data for field in timestamp_fields)
        
        if not has_timestamp:
            self.validation_results['warnings'].append(f"{filename}: No timestamp field found")

        # Check for empty data
        if not data:
            self.validation_results['errors'].append(f"{filename}: File contains empty data")

    def calculate_quality_score(self):
        """Calculate overall data quality score (0-100)"""
        
        total_files = self.validation_results['files_validated']
        if total_files == 0:
            self.validation_results['data_quality_score'] = 0.0
            return

        error_count = len(self.validation_results['errors'])
        warning_count = len(self.validation_results['warnings'])
        
        # Score calculation: Start at 100, subtract points for issues
        score = 100.0
        score -= (error_count * 20)  # Errors are more serious
        score -= (warning_count * 5)  # Warnings are less serious
        
        # Ensure score doesn't go below 0
        score = max(0.0, score)
        
        self.validation_results['data_quality_score'] = round(score, 2)

    def print_validation_summary(self):
        """Print validation results summary"""
        
        results = self.validation_results
        
        print(f"\n=== Data Validation Summary for {self.source} ===")
        print(f"Files validated: {results['files_validated']}")
        print(f"Errors: {len(results['errors'])}")
        print(f"Warnings: {len(results['warnings'])}")
        print(f"Quality Score: {results['data_quality_score']}/100")
        
        if results['errors']:
            print(f"\nErrors:")
            for error in results['errors']:
                print(f"  - {error}")
        
        if results['warnings']:
            print(f"\nWarnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")
        
        print()

def main():
    parser = argparse.ArgumentParser(description='Validate scraped government data')
    parser.add_argument('--source', required=True, 
                       help='Data source to validate (county-council, emergency, videos, etc.)')
    
    args = parser.parse_args()
    
    validator = DataValidator(args.source)
    results = validator.validate_source_data()
    validator.print_validation_summary()
    
    # Save validation results
    results_file = f"data/{args.source}/validation_results.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Validation results saved to {results_file}")
    
    # Exit with error code if there are validation errors
    if results['errors']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()