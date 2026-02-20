# Coding Task: Schema Builder UI (Phase 6 Frontend)

**Context:** We are building "Showrunner", an AI co-writer. We need a dedicated `/schemas` page where users can create, edit, and manage custom Container types (like Notion's database property editor). The backend will expose a CRUD API at `/api/v1/schemas/`.

**Your Objective: Write the React Frontend Code**

Create these components under `src/web/src/components/schema-builder/`:

### 1. `SchemaBuilderPanel.tsx` — Main Layout
A full-width panel with:
- **Left sidebar** (`SchemaList`): Lists existing schemas fetched from `GET /api/v1/schemas/`. Clicking selects one for editing. Has a "+ New Schema" button at the bottom.
- **Right panel** (`SchemaEditor`): Displays the editor for the selected schema.

### 2. `SchemaEditor.tsx` — Schema Edit Form
- Header inputs: `display_name` (text), auto-derived `name` (lower_snake_case, read-only), `description` (textarea)
- Field list: Renders an array of `FieldRow` components
- "Add Field" button at the bottom
- "Save Schema" button that POSTs/PUTs to the backend

### 3. `FieldRow.tsx` — Single Property Row
Renders as: `[name input] [type badge ▾] [required ★/○ toggle] [description input] [🗑 delete]`
- Clicking the type badge opens `FieldTypeSelector`
- If type is `enum`, show an additional tag input for `options[]`
- If type is `reference`, show a dropdown for `target_type` (populated from schema names)

### 4. `FieldTypeSelector.tsx` — Type Picker Popover
A grid of clickable cards showing all 8 field types: Text, Number, Decimal, Toggle, Tags, Rich Data, Dropdown, Link. Each card has an icon and label.

### 5. `NLWizardInput.tsx` — Natural Language Input
A text input + "✨ Generate Fields" button. On click, POSTs to `/api/v1/schemas/generate` and populates the FieldRow list with the AI-generated draft.

### 6. `SchemaPreview.tsx` — Live YAML Preview
Shows a read-only code block of the current schema serialized as YAML, updating live as the user edits fields.

### 7. Page Route: `src/web/src/app/schemas/page.tsx`
A Next.js App Router page that renders `SchemaBuilderPanel`.

**Design Requirements:**
- Use Tailwind CSS v4 with a dark theme matching the existing Showrunner aesthetic (slate-900/950 backgrounds, sky/emerald accents)
- Premium feel: smooth transitions, hover states, glassmorphism panels
- All components are `"use client"`

**Output:** Provide the exact, production-ready TypeScript code for all 7 files.
