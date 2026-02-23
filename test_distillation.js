import { api } from "./src/web/src/lib/api";
import fetch from "node-fetch";

async function testGenerate() {
    const intentLines = [
        "Create a pipeline based on these recorded user actions:",
        "1. Action Type: slash_command",
        "   Description: Invoked /brainstorm on selected text",
        '   Context Payload: {"command":"brainstorm","selected_text":"The dark knight falls.","context_length":400}',
        "\nThe pipeline MUST use 'payload.selected_text' as the standard generalized input instead of the specific text seen in the context. Assemble the prompt, run it, and present the output for approval."
    ];

    const finalIntent = intentLines.join("\n");

    const response = await fetch("http://localhost:8000/api/v1/pipeline/definitions/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            intent: finalIntent,
            title: "Test Recorded Workflow"
        })
    });

    const json = await response.json();
    console.log(JSON.stringify(json, null, 2));
}

testGenerate().catch(console.error);
