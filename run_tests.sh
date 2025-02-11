#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to run tests for a lambda
run_lambda_tests() {
    local lambda_name=$1
    echo -e "${GREEN}Running tests for ${lambda_name}...${NC}"
    
    cd lambda/${lambda_name}
    
    # Create and activate virtual environment
    python -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    pip install pytest pytest-cov pytest-mock
    
    # Run tests
    pytest tests/ -v --cov=src --cov-report=term-missing
    
    # Deactivate virtual environment
    deactivate
    cd ../..
}

# Run tests for each lambda
for lambda in video_processor upload_handler notification_handler; do
    run_lambda_tests $lambda
done

# Run integration tests if enabled
if [ "$RUN_INTEGRATION_TESTS" = "true" ]; then
    echo -e "${GREEN}Running integration tests...${NC}"
    pytest -v -m integration
fi