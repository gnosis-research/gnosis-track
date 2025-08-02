#!/bin/bash

# Gnosis Track Deployment Script
# This script helps deploy SeaweedFS and start the UI server

set -e  # Exit on error

echo "🚀 Gnosis Track Deployment Script"
echo "=================================="

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "It's recommended to run: source venv/bin/activate"
    echo ""
fi

# Check if package is installed
if ! python -c "import gnosis_track" 2>/dev/null; then
    echo "❌ gnosis-track package not found"
    echo "Please install it first: pip install -e ."
    exit 1
fi

echo "✅ Package found"

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start SeaweedFS
start_seaweedfs() {
    echo ""
    echo "📦 Starting SeaweedFS..."
    echo "This will:"
    echo "  - Download SeaweedFS binary if needed"
    echo "  - Start local cluster (Master, Volume, Filer, S3)"
    echo "  - Use ports: 9333, 8080, 8888, 8333"
    echo ""
    
    # Check if ports are available
    ports=(9333 8080 8888 8333)
    occupied_ports=()
    
    for port in "${ports[@]}"; do
        if check_port $port; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        echo "⚠️  Warning: The following ports are in use: ${occupied_ports[*]}"
        echo "SeaweedFS needs these ports. Please stop other services or choose different ports."
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Start SeaweedFS installation
    gnosis-track install seaweedfs
    
    # Start the cluster
    echo "Starting SeaweedFS cluster..."
    gnosis-track install start
}

# Function to start UI server
start_ui() {
    echo ""
    echo "🌐 Starting Web UI..."
    echo "This will start the Flask web server on http://localhost:8080"
    echo ""
    
    if check_port 8080; then
        echo "⚠️  Port 8080 is already in use"
        read -p "Use port 8081 instead? (Y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            exit 1
        fi
        UI_PORT=8081
    else
        UI_PORT=8080
    fi
    
    echo "Starting UI server on port $UI_PORT..."
    gnosis-track ui --port $UI_PORT --debug
}

# Function to run health check
health_check() {
    echo ""
    echo "🏥 Running Health Check..."
    gnosis-track health
}

# Function to show help
show_help() {
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  install     Start SeaweedFS cluster only"
    echo "  ui          Start web UI only (requires SeaweedFS running)"
    echo "  health      Run health check"
    echo "  full        Full deployment (SeaweedFS + UI)"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 full         # Deploy everything"
    echo "  $0 install      # Just start SeaweedFS"
    echo "  $0 ui           # Just start UI"
    echo ""
}

# Main deployment logic
case "${1:-full}" in
    "install")
        start_seaweedfs
        echo ""
        echo "✅ SeaweedFS deployment complete!"
        echo "S3 endpoint available at: http://localhost:8333"
        echo ""
        echo "Next steps:"
        echo "1. Run './deploy.sh ui' to start the web interface"
        echo "2. Or use 'python examples/basic_usage.py' to test"
        ;;
    
    "ui")
        echo "Checking SeaweedFS connection..."
        if ! gnosis-track health >/dev/null 2>&1; then
            echo "❌ SeaweedFS not accessible. Please run './deploy.sh install' first"
            exit 1
        fi
        echo "✅ SeaweedFS is running"
        start_ui
        ;;
    
    "health")
        health_check
        ;;
    
    "full")
        start_seaweedfs
        echo ""
        echo "✅ SeaweedFS started successfully!"
        echo ""
        echo "Waiting 5 seconds for services to stabilize..."
        sleep 5
        
        health_check
        
        echo ""
        echo "🎉 Deployment complete!"
        echo ""
        echo "Services running:"
        echo "  📦 SeaweedFS S3: http://localhost:8333"
        echo "  🌐 Web UI: http://localhost:8080"
        echo ""
        echo "Next steps:"
        echo "1. Open http://localhost:8080 in your browser"
        echo "2. Try examples: python examples/basic_usage.py"
        echo "3. Run health check: gnosis-track health"
        echo ""
        echo "To stop services:"
        echo "  - Press Ctrl+C in this terminal"
        echo "  - Or kill processes: pkill -f seaweedfs"
        
        # Start UI in the same process (will block)
        start_ui
        ;;
    
    "help"|"--help"|"-h")
        show_help
        ;;
    
    *)
        echo "❌ Unknown option: $1"
        show_help
        exit 1
        ;;
esac