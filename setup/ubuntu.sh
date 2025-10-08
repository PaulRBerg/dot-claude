#!/usr/bin/env bash

set -euo pipefail

# ==============================================================================
# Ubuntu Setup Script for Claude Code Dependencies
# ==============================================================================
# Installs all CLI tools and dependencies required by this Claude Code setup
#
# Requirements:
# - Ubuntu 24.04 LTS
# - sudo privileges
# - internet connection
#
# Usage:
#   sudo ./setup/ubuntu.sh
# ==============================================================================

readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly LOG_PREFIX="[${SCRIPT_NAME}]"

# Prevent interactive prompts during package installation
export DEBIAN_FRONTEND=noninteractive

# ==============================================================================
# Utilities
# ==============================================================================

log_info() {
  echo "${LOG_PREFIX} INFO: $*" >&2
}

log_error() {
  echo "${LOG_PREFIX} ERROR: $*" >&2
}

log_success() {
  echo "${LOG_PREFIX} ✓ $*" >&2
}

check_root() {
  if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
  fi
}

# ==============================================================================
# Detect Ubuntu Version
# ==============================================================================

detect_ubuntu_version() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    source /etc/os-release
    if [[ "${ID}" == "ubuntu" ]]; then
      echo "${VERSION_ID}"
    else
      log_error "This script is designed for Ubuntu only"
      exit 1
    fi
  else
    log_error "Cannot detect OS version"
    exit 1
  fi
}

# ==============================================================================
# Install System Dependencies
# ==============================================================================

install_system_packages() {
  log_info "Updating package manager..."
  apt-get update

  log_info "Installing core system packages..."
  apt-get install -y \
    git \
    curl \
    wget \
    tar \
    gzip \
    unzip \
    python3 \
    python3-pip \
    sqlite3 \
    software-properties-common

  log_success "System packages installed"
}

# ==============================================================================
# Install Modern CLI Tools via APT
# ==============================================================================

install_apt_tools() {
  log_info "Installing modern CLI tools from default repositories..."

  apt-get install -y \
    ripgrep \
    fd-find \
    bat \
    fzf \
    jq \
    git-delta \
    just \
    rsync

  # Create symlinks for fd and bat if needed (Ubuntu uses different names)
  if [[ ! -f /usr/local/bin/fd ]] && [[ -f /usr/bin/fdfind ]]; then
    ln -sf /usr/bin/fdfind /usr/local/bin/fd
    log_info "Created symlink: fd -> fdfind"
  fi

  if [[ ! -f /usr/local/bin/bat ]] && [[ -f /usr/bin/batcat ]]; then
    ln -sf /usr/bin/batcat /usr/local/bin/bat
    log_info "Created symlink: bat -> batcat"
  fi

  log_success "APT tools installed"
}

# ==============================================================================
# Install GitHub CLI
# ==============================================================================

install_gh() {
  log_info "Installing GitHub CLI (gh)..."

  # Add GitHub CLI repository
  if [[ ! -f /etc/apt/sources.list.d/github-cli.list ]]; then
    mkdir -p -m 755 /etc/apt/keyrings
    wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    apt-get update
  fi

  apt-get install -y gh

  log_success "gh installed: $(gh --version | head -n1)"
}

# ==============================================================================
# Install Eza (modern ls replacement)
# ==============================================================================

install_eza() {
  log_info "Installing eza..."

  # Add eza repository
  if [[ ! -f /etc/apt/sources.list.d/gierens.list ]]; then
    mkdir -p -m 755 /etc/apt/keyrings
    wget -qO- https://raw.githubusercontent.com/eza-community/eza/main/deb.asc | gpg --dearmor -o /etc/apt/keyrings/gierens.gpg
    chmod 644 /etc/apt/keyrings/gierens.gpg
    echo "deb [signed-by=/etc/apt/keyrings/gierens.gpg] http://deb.gierens.de stable main" | tee /etc/apt/sources.list.d/gierens.list > /dev/null
    apt-get update
  fi

  apt-get install -y eza

  log_success "eza installed: $(eza --version | head -n1)"
}

# ==============================================================================
# Install yq (YAML processor)
# ==============================================================================

install_yq() {
  log_info "Installing yq..."
  snap install yq
  log_success "yq installed: $(yq --version)"
}

# ==============================================================================
# Install Bun
# ==============================================================================

install_bun() {
  log_info "Installing Bun..."

  # Bun installation script - install as regular user, not root
  if [[ -n "${SUDO_USER:-}" ]]; then
    su - "${SUDO_USER}" -c 'curl -fsSL https://bun.sh/install | bash'
    log_success "Bun installed for user ${SUDO_USER}"
  else
    log_error "Cannot determine regular user for Bun installation"
    log_error "Please install Bun manually: curl -fsSL https://bun.sh/install | bash"
  fi
}

# ==============================================================================
# Install @antfu/ni
# ==============================================================================

install_ni() {
  log_info "Installing @antfu/ni..."

  if command -v npm &> /dev/null; then
    npm install -g @antfu/ni
    log_success "ni installed: $(ni --version 2>/dev/null || echo 'installed')"
  else
    log_error "npm not found - cannot install @antfu/ni"
    log_error "Install Node.js first, then run: npm install -g @antfu/ni"
  fi
}

# ==============================================================================
# Install Prettier (optional, for justfile)
# ==============================================================================

install_prettier() {
  log_info "Installing Prettier (optional)..."

  if command -v npm &> /dev/null; then
    npm install -g prettier
    log_success "Prettier installed"
  else
    log_info "Skipping Prettier - npm not available"
  fi
}

# ==============================================================================
# Main Installation
# ==============================================================================

main() {
  log_info "Starting Ubuntu setup for Claude Code dependencies..."

  check_root

  local ubuntu_version
  ubuntu_version="$(detect_ubuntu_version)"
  log_info "Detected Ubuntu ${ubuntu_version}"

  # Install system packages
  install_system_packages

  # Install tools available via APT
  install_apt_tools

  # Install tools requiring manual installation
  install_gh
  install_eza
  install_yq

  # Install Node.js tools
  install_ni
  install_bun
  install_prettier

  log_success "Installation complete!"
  echo ""
  log_info "Installed tools:"
  echo "  - rg (ripgrep): $(command -v rg)"
  echo "  - fd: $(command -v fd || command -v fdfind)"
  echo "  - bat: $(command -v bat || command -v batcat)"
  echo "  - eza: $(command -v eza)"
  echo "  - jq: $(command -v jq)"
  echo "  - yq: $(command -v yq)"
  echo "  - fzf: $(command -v fzf)"
  echo "  - delta: $(command -v delta)"
  echo "  - gh: $(command -v gh)"
  echo "  - just: $(command -v just)"
  echo "  - rsync: $(command -v rsync)"
  echo ""
  log_info "Note: Bun and ni may require a new shell session to be available in PATH"
  log_info "Python 3 is installed for hook scripts (ccnotify.py, cleanup.py)"
}

main "$@"
