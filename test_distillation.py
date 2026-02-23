import urllib.request
import json

url = "http://localhost:8000/api/v1/pipeline/definitions/generate"
data = {
    "intent": "Create a pipeline based on these recorded user actions:\n1. Action Type: slash_command\n   Description: Invoked /brainstorm on selected text\n   Context Payload: {\"command\":\"brainstorm\",\"selected_text\":\"The dark knight falls.\",\"context_length\":400}\n\nThe pipeline MUST use 'payload.selected_text' as the standard generalized input instead of the specific text seen in the context. Assemble the prompt, run it, and present the output for approval.",
    "title": "Test Recorded Workflow"
}

req = urllib.request.Request(url, json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
