#!/bin/bash

# A script to set up the content management environment on macOS

echo "Starting setup for the Website Content Manager..."
echo "This may ask for your password to install necessary tools."

# --- Helper function for printing status ---
function print_status() {
    echo "-----> $1"
}

# --- Step 1: Check for and install Homebrew ---
if ! command -v brew &> /dev/null; then
    print_status "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    print_status "Homebrew is already installed."
fi

# --- Step 2: Install Python and Git ---
print_status "Installing Python and Git (if not already installed)..."
brew install python git

# --- Step 3: Install Required Python Libraries ---
print_status "Installing required Python libraries (ttkbootstrap, gitpython)..."
pip3 install ttkbootstrap gitpython

# --- Final Message ---
echo ""
echo "✅ Kurulum Tamamlandı!"
echo ""
echo "Gerekli tüm araçlar yüklendi."
echo "Artık 'lawyer-website-content' klasöründeki 'manager.py' uygulamasını çalıştırabilirsiniz."
echo ""