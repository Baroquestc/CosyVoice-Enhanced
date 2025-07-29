#!/bin/bash

# CosyVoice API Docker Deployment Script
# This script helps deploy CosyVoice API with VLLM support

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Test Docker configuration validation
test_config() {
    print_status "Validating Docker configuration..."
    
    # Check if Dockerfile exists
    if [ -f "docker/Dockerfile" ]; then
        print_success "Dockerfile found"
    else
        print_error "Dockerfile not found at docker/Dockerfile"
        return 1
    fi
    
    # Check if docker-compose.yml exists  
    if [ -f "docker/docker-compose.yml" ]; then
        print_success "docker-compose.yml found"
    else
        print_error "docker-compose.yml not found at docker/docker-compose.yml"
        return 1
    fi
    
    # Validate docker-compose syntax (from docker directory)
    if (cd docker && docker-compose config >/dev/null 2>&1); then
        print_success "docker-compose.yml syntax is valid"
    else  
        print_error "docker-compose.yml syntax is invalid"
        return 1
    fi
    
    # Check if .env.example exists
    if [ -f "docker/.env.example" ]; then
        print_success ".env.example template found"
    else
        print_warning ".env.example template not found"
    fi
}

# Check if pretrained models exist
check_models() {
    local models_path="${1:-./pretrained_models}"
    
    if [ ! -d "$models_path" ]; then
        print_warning "Models directory '$models_path' not found."
        return 1
    fi
    
    # Check for common model directories
    local found_models=()
    for model in "CosyVoice2-0.5B" "CosyVoice-300M" "CosyVoice-300M-SFT" "CosyVoice-300M-Instruct"; do
        if [ -d "$models_path/$model" ]; then
            found_models+=("$model")
        fi
    done
    
    if [ ${#found_models[@]} -eq 0 ]; then
        print_warning "No valid model directories found in '$models_path'"
        return 1
    fi
    
    print_success "Found models: ${found_models[*]}"
    return 0
}

# Main function
main() {
    local action="${1:-check}"
    
    case "$action" in
        "check")
            print_status "Running Docker configuration checks..."
            check_docker
            test_config
            
            # Check models (warning only)
            if ! check_models "./pretrained_models"; then
                print_warning "No models found - you'll need to download them before deployment"
            fi
            
            print_success "Configuration validation completed!"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [check|help]"
            echo "  check - Validate Docker configuration"
            echo "  help  - Show this help"
            ;;
        *)
            print_error "Unknown action: $action (simplified version - only 'check' available)"
            ;;
    esac
}

main "$@"