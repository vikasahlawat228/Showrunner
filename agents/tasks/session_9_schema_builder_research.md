# Task: Schema Builder UX & Validation Layer (Phase 6)

**Context:** We are building "Showrunner", a node-based AI co-writer powered by Generic Containers. While we have coded the backend to accept dynamic schemas (using Pydantic `create_model`) and the frontend graph to display "GenericNode"s, the user currently cannot *create* custom types (e.g., "Spell", "Spaceship") without writing YAML by hand. We need an intuitive Schema Builder.

**Your Objective (Outsourced Research & Skill Prompt Definition):**
1. **Architectural & UX Analysis:** Propose the best UX for defining dynamic schemas in a Next.js/Tailwind application. Look at how Notion lets users add "Properties" to a database page, or how Strapi builds content types. How should we map these frontend fields (String, List[String], Boolean, RichText) to our established `ContainerSchema` Pydantic generator?
2. **Schema Wizard Skill Prompt Definition:** Many users won't want to click buttons to add fields. They will just say: *"Create a spaceship schema that tracks fuel, hull integrity, and captain."* Write a comprehensive System Prompt (Skill) for a "Schema Wizard Agent." This agent's job is to take a natural language request and output a strict JSON array of `FieldDefinition` objects (name, field_type, description, required) that matches our backend `ContainerSchema` model.
3. **Output:** Provide your architectural/UX recommendation for the React Schema Builder, and the exact Markdown text for the `schema_wizard.md` skill file.
