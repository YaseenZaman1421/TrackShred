#!/bin/bash
# TrackShred Installation Script
# Installs TrackShred and its dependencies on Linux systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root for security reasons."
    print_status "Run without sudo - the script will ask for permissions when needed."
    exit 1
fi

# Detect Linux distribution
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        print_error "Cannot detect Linux distribution"
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y coreutils python3 curl
            # Optional: install exiftool for advanced metadata cleaning
            if command -v apt-cache >/dev/null 2>&1; then
                if apt-cache show exiftool >/dev/null 2>&1; then
                    sudo apt install -y exiftool
                    print_success "Installed exiftool for metadata cleaning"
                else
                    print_warning "exiftool not available in repositories"
                fi
            fi
            ;;
        rhel|centos|fedora)
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y coreutils python3 curl
                sudo dnf install -y perl-Image-ExifTool 2>/dev/null || print_warning "exiftool not available"
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y coreutils python3 curl
                sudo yum install -y perl-Image-ExifTool 2>/dev/null || print_warning "exiftool not available"
            fi
            ;;
        arch|manjaro)
            sudo pacman -Sy --noconfirm coreutils python curl
            sudo pacman -S --noconfirm perl-image-exiftool 2>/dev/null || print_warning "exiftool not available"
            ;;
        *)
            print_warning "Unsupported distribution: $DISTRO"
            print_status "Please install coreutils, python3, and exiftool manually"
            ;;
    esac
}

# Create necessary directories
create_directories() {
    print_status "Creating configuration directories..."
    
    # Create config directory
    mkdir -p ~/.config/trackshred
    
    # Create local bin directory if it doesn't exist
    mkdir -p ~/.local/bin
    
    print_success "Created directories"
}

# Download and install TrackShred
install_trackshred() {
    print_status "Installing TrackShred..."
    
    # Download the main script
    if [[ -f "trackshred.py" ]]; then
        # If running from source directory
        cp trackshred.py ~/.local/bin/trackshred
    else
        # Download from repository (replace with actual URL)
        print_status "Downloading TrackShred..."
        curl -L -o ~/.local/bin/trackshred https://raw.githubusercontent.com/yourusername/trackshred/main/trackshred.py
    fi
    
    # Make executable
    chmod +x ~/.local/bin/trackshred
    
    # Create default config if it doesn't exist
    if [[ ! -f ~/.config/trackshred/config.json ]]; then
        cat > ~/.config/trackshred/config.json << 'EOF'
{
  "shred_passes": 3,
  "log_level": "INFO",
  "log_file": "/tmp/trackshred.log",
  "clean_thumbnails": true,
  "clean_recent_files": true,
  "clean_trash": true,
  "clean_shell_history": false
}
EOF
        print_success "Created default configuration"
    fi
    
    print_success "TrackShred installed to ~/.local/bin/trackshred"
}

# Update PATH if needed
update_path() {
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        print_status "Adding ~/.local/bin to PATH..."
        
        # Add to .bashrc if it exists
        if [[ -f ~/.bashrc ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            print_success "Added to ~/.bashrc"
        fi
        
        # Add to .zshrc if it exists
        if [[ -f ~/.zshrc ]]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
            print_success "Added to ~/.zshrc"
        fi
        
        # Export for current session
        export PATH="$HOME/.local/bin:$PATH"
        
        print_warning "Please restart your terminal or run: source ~/.bashrc"
    fi
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    if command -v trackshred >/dev/null 2>&1; then
        print_success "TrackShred is available in PATH"
        trackshred --version
    elif [[ -f ~/.local/bin/trackshred ]]; then
        print_success "TrackShred installed successfully"
        ~/.local/bin/trackshred --version
        print_warning "Run 'source ~/.bashrc' or restart terminal to use 'trackshred' command"
    else
        print_error "Installation failed"
        exit 1
    fi
}

# Main installation process
main() {
    echo "🔐 TrackShred Installation Script"
    echo "================================"
    echo
    
    detect_distro
    print_status "Detected distribution: $DISTRO"
    
    install_dependencies
    create_directories
    install_trackshred
    update_path
    verify_installation
    
    echo
    print_success "Installation completed successfully!"
    echo
    echo "Usage examples:"
    echo "  trackshred --target ~/secret.pdf"
    echo "  trackshred --deep --dry-run"
    echo "  trackshred --help"
    echo
    echo "Configuration file: ~/.config/trackshred/config.json"
    echo "Documentation: https://github.com/yourusername/trackshred"
}

# Run main function
main "$@"
