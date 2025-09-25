#!/bin/bash

# Raspberry Pi Malayalam Voice Recognition Setup Script
# ===================================================
# This script automates the setup process for offline Malayalam
# speech recognition on Raspberry Pi

set -e  # Exit on error

echo "🚀 Raspberry Pi Malayalam Voice Recognition Setup"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running on Raspberry Pi
check_rpi() {
    echo "🔍 Checking system compatibility..."
    
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        print_status "Running on Raspberry Pi"
    elif grep -q "BCM" /proc/cpuinfo 2>/dev/null; then
        print_status "Running on BCM processor (likely Raspberry Pi)"
    else
        print_warning "Not detected as Raspberry Pi, but continuing..."
    fi
    
    # Check architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "armv"* ]] || [[ "$ARCH" == "aarch64" ]]; then
        print_status "ARM architecture detected: $ARCH"
    else
        print_warning "Non-ARM architecture detected: $ARCH"
    fi
}

# Update system
update_system() {
    echo "📦 Updating system packages..."
    sudo apt update
    sudo apt upgrade -y
    print_status "System updated"
}

# Install system dependencies
install_system_deps() {
    echo "🔧 Installing system dependencies..."
    
    PACKAGES=(
        "python3"
        "python3-pip"
        "python3-dev"
        "python3-pyaudio"
        "portaudio19-dev"
        "alsa-utils"
        "pulseaudio"
        "ffmpeg"
        "wget"
        "unzip"
        "git"
        "build-essential"
        "cmake"
        "pkg-config"
    )
    
    for package in "${PACKAGES[@]}"; do
        echo "Installing $package..."
        sudo apt install -y "$package" || print_warning "Failed to install $package"
    done
    
    print_status "System dependencies installed"
}

# Setup audio permissions
setup_audio() {
    echo "🔊 Setting up audio permissions..."
    
    # Add user to audio group
    sudo usermod -a -G audio "$USER"
    
    # Create basic ALSA config
    if [ ! -f ~/.asoundrc ]; then
        cat > ~/.asoundrc << EOF
pcm.!default {
    type asym
    playback.pcm "speaker"
    capture.pcm "mic"
}

pcm.speaker {
    type plug
    slave {
        pcm "hw:0,0"
    }
}

pcm.mic {
    type plug
    slave {
        pcm "hw:1,0"
    }
}
EOF
        print_status "Basic ALSA configuration created"
    fi
    
    print_status "Audio setup complete"
    print_warning "Please reboot or logout/login for audio group changes to take effect"
}

# Install Python dependencies
install_python_deps() {
    echo "🐍 Installing Python dependencies..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        print_status "Python dependencies installed from requirements.txt"
    else
        print_error "requirements.txt not found"
        return 1
    fi
}

# Download Vosk models
download_models() {
    echo "🤖 Downloading speech recognition models..."
    
    mkdir -p models
    cd models
    
    # English model (small for RPi)
    if [ ! -d "../vosk-en" ]; then
        echo "📥 Downloading English model..."
        wget -O vosk-model-small-en-us-0.15.zip \
            "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        unzip vosk-model-small-en-us-0.15.zip
        mv vosk-model-small-en-us-0.15 ../vosk-en
        rm vosk-model-small-en-us-0.15.zip
        print_status "English model downloaded"
    else
        print_status "English model already exists"
    fi
    
    # Malayalam model (if available)
    if [ ! -d "../vosk-ml" ]; then
        echo "📥 Attempting to download Malayalam model..."
        if wget -O vosk-model-ml-0.22.zip \
            "https://alphacephei.com/vosk/models/vosk-model-ml-0.22.zip" 2>/dev/null; then
            unzip vosk-model-ml-0.22.zip
            mv vosk-model-ml-* ../vosk-ml
            rm vosk-model-ml-0.22.zip
            print_status "Malayalam model downloaded"
        else
            print_warning "Malayalam model not available from Vosk repository"
            print_info "You can manually download and place Malayalam model in 'vosk-ml' directory"
        fi
    else
        print_status "Malayalam model already exists"
    fi
    
    cd ..
}

# Setup Whisper.cpp (optional, for better performance)
setup_whisper_cpp() {
    echo "🔧 Setting up Whisper.cpp (optional)..."
    
    if [ ! -d "whisper.cpp" ]; then
        echo "📥 Cloning Whisper.cpp..."
        git clone https://github.com/ggml-org/whisper.cpp.git
        
        cd whisper.cpp
        echo "🔨 Building Whisper.cpp (this may take a while)..."
        make -j$(nproc)
        
        echo "📥 Downloading small multilingual model..."
        ./models/download-ggml-model.sh small
        
        cd ..
        print_status "Whisper.cpp setup complete"
    else
        print_status "Whisper.cpp already exists"
    fi
}

# Create service file (optional)
create_service() {
    echo "🔧 Creating systemd service (optional)..."
    
    SERVICE_FILE="/etc/systemd/system/malayalam-stt.service"
    
    if [ ! -f "$SERVICE_FILE" ]; then
        sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Malayalam Speech Recognition Service
After=sound.target
Wants=sound.target

[Service]
Type=simple
User=$USER
Group=audio
WorkingDirectory=$(pwd)
Environment=PYTHONPATH=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/rpi_stt.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
        
        sudo systemctl daemon-reload
        print_status "Service file created at $SERVICE_FILE"
        print_info "Enable with: sudo systemctl enable malayalam-stt"
        print_info "Start with: sudo systemctl start malayalam-stt"
    else
        print_status "Service file already exists"
    fi
}

# Run tests
run_tests() {
    echo "🧪 Running basic tests..."
    
    # Test Python imports
    python3 -c "
import sys
try:
    import vosk
    print('✅ Vosk imported successfully')
except ImportError as e:
    print(f'❌ Vosk import failed: {e}')
    sys.exit(1)

try:
    import sounddevice
    print('✅ SoundDevice imported successfully')
except ImportError as e:
    print(f'❌ SoundDevice import failed: {e}')
    sys.exit(1)

print('✅ All Python dependencies working')
"
    
    # Test model loading
    if [ -d "vosk-en" ]; then
        python3 -c "
import os
if os.path.exists('vosk-en'):
    try:
        from vosk import Model
        model = Model('vosk-en')
        print('✅ English model loaded successfully')
    except Exception as e:
        print(f'❌ Model loading failed: {e}')
"
    fi
    
    print_status "Basic tests completed"
}

# Main setup function
main_setup() {
    echo "Starting setup process..."
    echo
    
    check_rpi
    
    # Ask for confirmation
    echo
    read -p "Continue with full setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled"
        exit 0
    fi
    
    update_system
    install_system_deps
    setup_audio
    install_python_deps
    download_models
    
    # Optional components
    echo
    read -p "Install Whisper.cpp for better performance? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_whisper_cpp
    fi
    
    read -p "Create systemd service? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_service
    fi
    
    run_tests
    
    echo
    echo "🎉 Setup Complete!"
    echo "================"
    echo "Available scripts:"
    echo "  • python3 test_audio.py - Test audio input/output"
    echo "  • python3 rpi_stt.py - Interactive speech recognition"
    echo "  • python3 main.py - Original project interface"
    echo
    echo "Next steps:"
    echo "1. Reboot the system (recommended for audio changes)"
    echo "2. Test audio: python3 test_audio.py"
    echo "3. Run speech recognition: python3 rpi_stt.py"
    echo
    print_warning "If audio doesn't work, check microphone connections and run 'alsamixer'"
}

# Check if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main_setup
fi