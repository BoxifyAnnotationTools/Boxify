#!/bin/bash
set -Eeuo pipefail

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

# Ask for the sudo password before changing the system.
echo "[*] Sudo access is required to install system packages."
sudo -v || {
    echo "[ERROR] Sudo authentication failed."
    exit 1
}

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

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_PATH="$SCRIPT_DIR"
PYTHON_VERSION="3.11.9"
PYTHON_BIN="python3.11"
VENV_DIR="$APP_PATH/boxify"

# ──────────────────────────────────────────
# DEBIAN / UBUNTU / MINT
# ──────────────────────────────────────────
if [[ "$OS" == "ubuntu" || "$OS" == "debian" || "$OS" == "linuxmint" ]]; then
    echo "[*] Installing Python $PYTHON_VERSION and Tkinter packages..."
    sudo apt update
    sudo apt install -y software-properties-common

    if [[ "$OS" == "ubuntu" || "$OS" == "linuxmint" ]]; then
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
    fi

    sudo apt install -y \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3.11-tk
fi

# ──────────────────────────────────────────
# ARCH / MANJARO
# ──────────────────────────────────────────
if [[ "$OS" == "arch" || "$OS" == "manjaro" ]]; then
    echo "[*] Installing Python, Tkinter, and virtual environment dependencies..."
    sudo pacman -S --noconfirm python tk mesa libcanberra
    PYTHON_BIN="python"
fi

# ──────────────────────────────────────────
# FEDORA / RHEL / CENTOS
# ──────────────────────────────────────────
if [[ "$OS" == "fedora" || "$OS" == "rhel" || "$OS" == "centos" ]]; then
    echo "[*] Installing Python $PYTHON_VERSION and Tkinter packages..."
    sudo dnf install -y \
        python3.11 \
        python3.11-devel \
        python3.11-tkinter
    sudo dnf install -y mesa-libGL libglvnd-glx
fi

if ! command -v "$PYTHON_BIN" &> /dev/null; then
    echo "[ERROR] Python interpreter $PYTHON_BIN was not found."
    exit 1
fi

PYTHON_ACTUAL_VERSION="$($PYTHON_BIN -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
echo "[OK] Python $PYTHON_ACTUAL_VERSION detected."

if [[ "$PYTHON_ACTUAL_VERSION" != "$PYTHON_VERSION" ]]; then
    echo "[ERROR] Boxify requires Python $PYTHON_VERSION exactly."
    echo "[ERROR] The detected interpreter is $PYTHON_ACTUAL_VERSION."
    exit 1
fi

# ──────────────────────────────────────────
# CREATE VENV
# ──────────────────────────────────────────
echo "[*] Creating Virtual Environment with $PYTHON_BIN..."

$PYTHON_BIN -m venv "$VENV_DIR" || {
    echo "[ERROR] Failed creating venv"
    exit 1
}

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    echo "[ERROR] Virtual environment was not created correctly."
    exit 1
fi

source "$VENV_DIR/bin/activate"

python -c 'import tkinter' || {
    echo "[ERROR] Tkinter is unavailable. Install the matching python3.11-tk package."
    exit 1
}

# ──────────────────────────────────────────
# INSTALL PYTHON PACKAGES
# ──────────────────────────────────────────
echo "[*] Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel
echo "[*] Installing Streamlit..."
python -m pip install streamlit yt-dlp
python -m pip install pycocotools
MACHINE_ARCH=$(uname -m)

if [[ "$MACHINE_ARCH" == "aarch64" ]]; then
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
LAUNCHER_PATH="$APP_PATH/Boxify-launcher.sh"
DESKTOP_FILE="$APP_PATH/Boxify.desktop"

cat <<EOF > "$LAUNCHER_PATH"
#!/bin/bash
cd "$APP_PATH"
source "$VENV_DIR/bin/activate"
exec python -u "$APP_PATH/utils/Annotator.py"
EOF

chmod +x "$LAUNCHER_PATH"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=Boxify
Exec=$LAUNCHER_PATH
Icon=$APP_PATH/assets/boxify.png
Type=Application
Path=$APP_PATH
Terminal=true
Categories=Development;
EOF

chmod +x "$DESKTOP_FILE"

# Mark the launcher as trusted where the desktop environment supports it.
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
if [[ -n "$DESKTOP_DIR" && -d "$DESKTOP_DIR" ]]; then
    cp "$DESKTOP_FILE" "$DESKTOP_DIR/Boxify.desktop"
    chmod +x "$DESKTOP_DIR/Boxify.desktop"
    if command -v gio &> /dev/null; then
        gio set "$DESKTOP_DIR/Boxify.desktop" metadata::trusted true 2>/dev/null || true
    fi
    echo "[OK] Desktop shortcut created at $DESKTOP_DIR/Boxify.desktop"
else
    echo "[NOTICE] Desktop folder was not detected. Use $DESKTOP_FILE to launch Boxify."
fi

# ──────────────────────────────────────────
# DONE
# ──────────────────────────────────────────
echo ""
echo "=========================================="
echo "      INSTALLATION COMPLETED!"
echo "=========================================="
echo "Run with:"
echo "$DESKTOP_FILE"
echo "=========================================="