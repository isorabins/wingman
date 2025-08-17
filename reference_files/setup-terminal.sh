#!/bin/bash
# Terminal Setup for Fridays at Four
# Run this once to add helpful aliases to your shell

echo "🔧 Setting up Fridays at Four terminal shortcuts..."

# Detect shell
if [[ "$SHELL" == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
    echo "📝 Detected zsh shell"
elif [[ "$SHELL" == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    echo "📝 Detected bash shell"
else
    echo "❓ Unknown shell: $SHELL"
    echo "Please manually add aliases to your shell config file"
    exit 1
fi

# Add aliases to shell config
echo ""
echo "# Fridays at Four shortcuts" >> "$SHELL_RC"
echo "alias faf='cd /Applications/fridays-at-four && source activate-env.sh'" >> "$SHELL_RC"
echo "alias faf-cd='cd /Applications/fridays-at-four'" >> "$SHELL_RC"
echo "alias faf-env='cd /Applications/fridays-at-four && source activate-env.sh'" >> "$SHELL_RC"

echo "✅ Added aliases to $SHELL_RC:"
echo "   faf       # Go to project and activate environment"
echo "   faf-cd    # Just go to project directory"
echo "   faf-env   # Go to project and activate environment"
echo ""
echo "🔄 Restart your terminal or run: source $SHELL_RC"
echo ""
echo "💡 After restart, you can just type 'faf' to get started!" 