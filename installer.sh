#!/bin/bash

## setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/acherone-script/main/installer.sh -O - | /bin/sh

## Only This 2 lines to edit with new version ######
version='1.3'
changelog='Fix Security E2'
##############################################################

TMPPATH=/tmp/acherone-install
FILEPATH=/tmp/acherone-main.tar.gz

echo "Starting Acherone installation..."

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/Acherone
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/Acherone
fi

# Cleanup function
cleanup() {
    echo "Cleaning up temporary files..."
    [ -d "$TMPPATH" ] && rm -rf "$TMPPATH"
    [ -f "$FILEPATH" ] && rm -f "$FILEPATH"
}

# Detect OS type
detect_os() {
    if [ -f /var/lib/dpkg/status ]; then
        OSTYPE="DreamOs"
        STATUS="/var/lib/dpkg/status"
    elif [ -f /etc/opkg/opkg.conf ] || [ -f /var/lib/opkg/status ]; then
        OSTYPE="OE"
        STATUS="/var/lib/opkg/status"
    else
        OSTYPE="Unknown"
        STATUS=""
    fi
    echo "Detected OS type: $OSTYPE"
}

detect_os

# Cleanup before starting
cleanup
mkdir -p "$TMPPATH"

# Install wget if missing
if ! command -v wget >/dev/null 2>&1; then
    echo "Installing wget..."
    case "$OSTYPE" in
        "DreamOs")
            apt-get update && apt-get install -y wget || { echo "Failed to install wget"; exit 1; }
            ;;
        "OE")
            opkg update && opkg install wget || { echo "Failed to install wget"; exit 1; }
            ;;
        *)
            echo "Unsupported OS type. Cannot install wget."
            exit 1
            ;;
    esac
fi

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "Python3 image detected"
    PYTHON="PY3"
    Packagesix="python3-six"
    Packagerequests="python3-requests"
else
    echo "Python2 image detected"
    PYTHON="PY2"
    Packagerequests="python-requests"
    Packagesix="python-six"
fi

# Install required packages
install_pkg() {
    local pkg=$1
    if [ -z "$STATUS" ] || ! grep -qs "Package: $pkg" "$STATUS" 2>/dev/null; then
        echo "Installing $pkg..."
        case "$OSTYPE" in
            "DreamOs")
                apt-get update && apt-get install -y "$pkg" || { echo "Could not install $pkg, continuing anyway..."; }
                ;;
            "OE")
                opkg update && opkg install "$pkg" || { echo "Could not install $pkg, continuing anyway..."; }
                ;;
            *)
                echo "Cannot install $pkg on unknown OS type, continuing..."
                ;;
        esac
    else
        echo "$pkg already installed"
    fi
}

# Install Python dependencies
[ "$PYTHON" = "PY3" ] && install_pkg "$Packagesix"
install_pkg "$Packagerequests"

# Download and extract
echo "Downloading Acherone..."
wget --no-check-certificate 'https://github.com/Belfagor2005/acherone-script/archive/refs/heads/main.tar.gz' -O "$FILEPATH"
if [ $? -ne 0 ]; then
    echo "Failed to download Acherone package!"
    cleanup
    exit 1
fi

echo "Extracting package..."
tar -xzf "$FILEPATH" -C "$TMPPATH"
if [ $? -ne 0 ]; then
    echo "Failed to extract Acherone package!"
    cleanup
    exit 1
fi

# Install plugin files
echo "Installing plugin files..."
mkdir -p "$PLUGINPATH"

# Find correct directory in extracted structure
if [ -d "$TMPPATH/acherone-script-main/usr/lib/enigma2/python/Plugins/Extensions/Acherone" ]; then
    cp -r "$TMPPATH/acherone-script-main/usr/lib/enigma2/python/Plugins/Extensions/Acherone"/* "$PLUGINPATH/" 2>/dev/null
    echo "Copied from standard plugin directory"
elif [ -d "$TMPPATH/acherone-script-main/usr/lib64/enigma2/python/Plugins/Extensions/Acherone" ]; then
    cp -r "$TMPPATH/acherone-script-main/usr/lib64/enigma2/python/Plugins/Extensions/Acherone"/* "$PLUGINPATH/" 2>/dev/null
    echo "Copied from lib64 plugin directory"
elif [ -d "$TMPPATH/acherone-script-main/usr" ]; then
    # Copy entire usr tree
    cp -r "$TMPPATH/acherone-script-main/usr"/* /usr/ 2>/dev/null
    echo "Copied entire usr structure"
else
    echo "Could not find plugin files in extracted archive"
    echo "Available directories in tmp:"
    find "$TMPPATH" -type d | head -10
    cleanup
    exit 1
fi

sync

# Verify installation
echo "Verifying installation..."
if [ -d "$PLUGINPATH" ] && [ -n "$(ls -A "$PLUGINPATH" 2>/dev/null)" ]; then
    echo "Plugin directory found and not empty: $PLUGINPATH"
    echo "Contents:"
    ls -la "$PLUGINPATH/" | head -10
    
    echo ""
    echo "#########################################################"
    echo "#          Acherone $version INSTALLED SUCCESSFULLY         #"
    echo "#########################################################"
else
    echo "Plugin installation failed or directory is empty!"
    cleanup
    exit 1
fi

# Cleanup
cleanup
sync

# Graceful restart
echo "Restarting enigma2..."
sleep 2

if command -v systemctl >/dev/null 2>&1; then
    systemctl restart enigma2
elif command -v init >/dev/null 2>&1; then
    init 4 && sleep 2 && init 3
else
    killall -9 enigma2
fi

exit 0