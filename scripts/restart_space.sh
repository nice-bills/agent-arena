#!/bin/bash
# Restart HuggingFace Space after code push

SPACE_ID="nice-bill/agent-arena"

echo "Restarting HF Space: $SPACE_ID"

# Using HF CLI to restart the Space
if command -v hf &> /dev/null; then
    hf space restart "$SPACE_ID"
    echo "Space restart requested via HF CLI"
elif [ -n "$HF_TOKEN" ]; then
    # Using curl to call HF API
    curl -X POST "https://huggingface.co/api/spaces/$SPACE_ID/submit" \
        -H "Authorization: Bearer $HF_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"action": "restart"}'
    echo "Space restart requested via API"
else
    echo "No HF CLI or HF_TOKEN found."
    echo "Please restart manually: https://huggingface.co/spaces/$SPACE_ID"
fi

echo "Done!"
