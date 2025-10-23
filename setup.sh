# ============================================================================
# NEW LAPTOP SETUP - WSL + Dev Environment
# ============================================================================

# 1. Install WSL (PowerShell as Admin)
# wsl --install

# 2. Restart computer, then set up Ubuntu username/password

# 3. Update everything (inside WSL)
sudo apt update && sudo apt upgrade -y

# 4. Install essential tools
sudo apt install -y build-essential curl git wget

# 5. Install VS Code in Windows, then install WSL extension
# Download from: https://code.visualstudio.com/
# In VS Code: Install "WSL" extension

# 6. Enable 'code' command in WSL
# The WSL extension adds this automatically - test with:
code .

# 7. Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 8. Reload shell to get uv in PATH
source ~/.bashrc

# 9. Verify uv installation
uv --version

# 10. Configure git
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# 11. Install GitHub CLI (optional but helpful)
sudo apt install -y gh

# 12. Generate SSH key for GitHub (optional)
ssh-keygen -t ed25519 -C "your.email@company.com"
cat ~/.ssh/id_ed25519.pub  # Copy this to GitHub settings

# ============================================================================
# OPTIONAL BUT RECOMMENDED
# ============================================================================

# Install zsh + oh-my-zsh (better shell)
# Step 1: Install zsh first (wait for it to complete)
sudo apt install -y zsh

# Step 2: Then install oh-my-zsh (after zsh is installed)
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Step 3: Update .zshrc contents

# Install Node.js (if needed)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker (if needed)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# ============================================================================
# QUICK TEST
# ============================================================================

# Test your setup
cd ~
mkdir test-project && cd test-project
uv init
uv add pandas
code .

# ADDITIONAL INFO
# =================================================================
# Converting legacy code with only requirements.txt file to use uv.
# =================================================================
# Step 1: Initialize pyproject.toml
uv init --no-readme

# Step 2: Add packages from requirements.txt
# Read each line and add it
cat requirements.txt | xargs -I {} uv add {}


# If you want to switch between shells:
# Make bash or zsh default
chsh -s $(which bash)
chsh -s $(which zsh)
