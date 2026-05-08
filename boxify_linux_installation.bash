#!/bin/bash

# ==========================================
#         Boxify Universal Installer
# ==========================================

echo "=========================================="
echo "    Welcome to Boxify, AI Annotator"
echo "        Thanks for choosing us"
echo "=========================================="
echo "System is preparing your environment..."
echo "=========================================="
sleep 1

# ──────────────────────────────────────────
# DETECT OS
# ──────────────────────────────────────────
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "[ERROR] Unsupported OS"
    exit 1
fi

echo "[*] Detecting OS: $OS"

PYTHON_BIN="python3.12"

# ──────────────────────────────────────────
# DEBIAN / UBUNTU / MINT
# ──────────────────────────────────────────
if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS" == "linuxmint" ]]; then

    if $PYTHON_BIN --version &> /dev/null; then
        echo "[OK] Python 3.12 already installed."
    else
        echo "[*] Installing Python 3.12..."

        sudo apt update
        sudo apt install -y software-properties-common

        # Ubuntu lama butuh deadsnakes
        if [[ "$OS" == "ubuntu" || "$OS" == "linuxmint" ]]; then
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt update
        fi

        sudo apt install -y \
            python3.12 \
            python3.12-venv \
            python3.12-dev \
            python3.12-tk
    fi
fi

# ──────────────────────────────────────────
# ARCH / MANJARO
# ──────────────────────────────────────────
if [[ "$OS" == "arch" || "$OS" == "manjaro" ]]; then

    if $PYTHON_BIN --version &> /dev/null; then
        echo "[OK] Python 3.12 already installed."
    else
        echo "[*] Installing Python 3.12..."
        sudo pacman -S --noconfirm python tk mesa libcanberra

        # Arch biasanya python = latest stable
        PYTHON_BIN="python"
    fi

    sudo pacman -S --noconfirm tk mesa libcanberra
fi

# ──────────────────────────────────────────
# FEDORA / RHEL / CENTOS
# ──────────────────────────────────────────
if [[ "$OS" == "fedora" || "$OS" == "rhel" || "$OS" == "centos" ]]; then

    if $PYTHON_BIN --version &> /dev/null; then
        echo "[OK] Python 3.12 already installed."
    else
        echo "[*] Installing Python 3.12..."
        sudo dnf install -y \
            python3.12 \
            python3.12-devel \
            python3.12-tkinter
    fi

    sudo dnf install -y mesa-libGL libglvnd-glx
fi

# ──────────────────────────────────────────
# CREATE VENV
# ──────────────────────────────────────────
echo "[*] Creating Virtual Environment with $PYTHON_BIN..."

$PYTHON_BIN -m venv boxify || {
    echo "[ERROR] Failed creating venv"
    exit 1
}

source boxify/bin/activate

# ──────────────────────────────────────────
# INSTALL PYTHON PACKAGES
# ──────────────────────────────────────────
echo "[*] Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel
echo "[*] Installing Streamlit..."
python -m pip install streamlit yt-dlp
ARCH=$(uname -m)

if [[ "$ARCH" == "aarch64" ]]; then
    echo "[!] ARM detected"
    pip install torch torchvision torchaudio

else
    if command -v nvidia-smi &> /dev/null; then
        echo "[OK] NVIDIA GPU detected"
        pip install torch torchvision torchaudio \
            --index-url https://download.pytorch.org/whl/cu121
    else
        echo "[!] Installing CPU version"
        pip install torch torchvision torchaudio
    fi
fi

echo "[*] Installing application dependencies..."
pip install ultralytics pyinstaller

# ──────────────────────────────────────────
# CREATE DESKTOP ENTRY
# ──────────────────────────────────────────
APP_PATH=$(pwd)

cat <<EOF > "Boxify.desktop"
[Desktop Entry]
Name=Boxify
Exec=bash -c "source $APP_PATH/boxify/bin/activate && python -u $APP_PATH/utils/Annotator.py; exec bash"
Icon=$APP_PATH/assets/boxify.png
Type=Application
Path=$APP_PATH
Terminal=true
Categories=Development;
EOF

chmod +x Boxify.desktop

# ──────────────────────────────────────────
# DONE
# ──────────────────────────────────────────
echo ""
echo "=========================================="
echo "      INSTALLATION COMPLETED!"
echo "=========================================="
echo "Run with:"
echo "./Boxify.desktop"
echo "=========================================="