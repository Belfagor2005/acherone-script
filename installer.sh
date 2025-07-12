#!/bin/bash

## setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/acherone-script/main/installer.sh -O - | /bin/sh

## Only This 2 lines to edit with new version ######
version='1.3'
changelog='\nFix Security E2'
##############################################################
TMPPATH=/tmp/acherone-script-main
FILEPATH=/tmp/acherone-main.tar.gz

if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/Acherone
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/Acherone
fi

# Check OS type
if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
else
    STATUS=/var/lib/opkg/status
    OSTYPE=Dream
fi


# Install wget if missing
if ! command -v wget >/dev/null; then

    if [ "$OSTYPE" = "DreamOs" ]; then

        apt-get update && apt-get install -y wget
    else
        opkg update && opkg install wget
    fi || { echo "Failed to install wget"; exit 1; }
fi

# Check Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then

    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else

    PYTHON=PY2
    Packagerequests=python-requests
fi

# Install dependencies
install_pkg() {
    pkg="$1"
    if ! grep -qs "Package: $pkg" "$STATUS"; then
        echo "Installing $pkg..."
        if [ "$OSTYPE" = "DreamOs" ]; then
            apt-get update && apt-get install -y "$pkg" || return 1
        else
            opkg update && opkg install "$pkg" || return 1
        fi
    fi
    return 0
}

install_pkg "$Packagerequests" || { echo "Dependency installation failed"; exit 1; }
[ "$PYTHON" = "PY3" ] && install_pkg "$Packagesix"

# Cleanup and install
mkdir -p "$TMPPATH" || exit 1
cd "$TMPPATH" || exit 1

wget --no-check-certificate 'https://github.com/Belfagor2005/acherone-script/archive/refs/heads/main.tar.gz' -O "$FILEPATH" || {
    echo "Download failed"; exit 1;
}

tar -xzf "$FILEPATH" -C /tmp/ || {
    echo "Extraction failed"; exit 1;
}

cp -r /tmp/acherone-script-main/usr/ / || {
    echo "Copy failed"; exit 1;
}

# Verify installation
[ ! -d "$PLUGINPATH" ] && { echo "Installation failed: $PLUGINPATH missing"; exit 1; }

# Cleanup
[ -n "$TMPPATH" ] && rm -rf "$TMPPATH"
[ -f "$FILEPATH" ] && rm -f "$FILEPATH"


sync

# Success message
echo "#########################################################
#          Acherone $version INSTALLED SUCCESSFULLY         #
#########################################################"
# Graceful restart
if command -v systemctl >/dev/null; then
    systemctl restart enigma2
else
    init 4 && sleep 2 && init 3
fi
exit 0