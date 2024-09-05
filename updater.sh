#!/bin/bash

# Configuration
REPO_USER="ammar0xff"
REPO_NAME="Mbedly"
REPO_URL="https://github.com/$REPO_USER/$REPO_NAME"
LOCAL_VERSION_FILE="current_version.txt"
SCRIPT_TO_RUN="./mbedly.sh"

# Function to get the latest release version from GitHub
get_latest_version() {
    curl -s "https://api.github.com/repos/$REPO_USER/$REPO_NAME/releases/latest" | jq -r .tag_name
}

# Function to get the currently deployed version
get_current_version() {
    if [ -f "$LOCAL_VERSION_FILE" ]; then
        cat "$LOCAL_VERSION_FILE"
    else
        echo "none"
    fi
}

# Function to update the local repo
update_repo() {
    echo "Pulling latest changes from the repository..."
    git pull origin main || { echo "Failed to pull updates from GitHub."; exit 1; }
}

# Main script
LATEST_VERSION=$(get_latest_version)
CURRENT_VERSION=$(get_current_version)

if [ "$LATEST_VERSION" != "$CURRENT_VERSION" ]; then
    echo "New version available: $LATEST_VERSION"
    echo "Updating repository..."

    # Update the repository by pulling latest changes
    update_repo

    # Update the version file
    echo "$LATEST_VERSION" > "$LOCAL_VERSION_FILE"
    echo "Update complete. Now running version $LATEST_VERSION"
else
    echo "No updates available. Current version ($CURRENT_VERSION) is up-to-date."
fi

