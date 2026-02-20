"use client";

import type { CharacterDetail } from "@/lib/api";

interface CharacterInspectorProps {
  character: CharacterDetail;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-4">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
        {title}
      </h3>
      {children}
    </div>
  );
}

function Tags({ items }: { items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((item) => (
        <span
          key={item}
          className="px-2 py-0.5 rounded-full bg-gray-800 text-gray-300 text-xs"
        >
          {item}
        </span>
      ))}
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="text-sm mb-1">
      <span className="text-gray-500">{label}:</span>{" "}
      <span className="text-gray-300">{value}</span>
    </div>
  );
}

export function CharacterInspector({ character }: CharacterInspectorProps) {
  const { personality, dna, arc, relationships } = character;

  return (
    <div className="space-y-1">
      {/* Identity */}
      <Section title="Identity">
        <Field label="Role" value={character.role} />
        <Field label="One-line" value={character.one_line} />
        {character.aliases.length > 0 && (
          <Field label="Aliases" value={character.aliases.join(", ")} />
        )}
      </Section>

      {/* Backstory */}
      {character.backstory && (
        <Section title="Backstory">
          <p className="text-sm text-gray-300 leading-relaxed">
            {character.backstory}
          </p>
        </Section>
      )}

      {/* Personality */}
      {personality && (
        <Section title="Personality">
          {personality.traits.length > 0 && (
            <div className="mb-2">
              <span className="text-xs text-gray-500">Traits</span>
              <Tags items={personality.traits} />
            </div>
          )}
          <Field label="Speech" value={personality.speech_pattern} />
          {personality.verbal_tics.length > 0 && (
            <Field label="Tics" value={personality.verbal_tics.join(", ")} />
          )}
          <Field label="Conflict" value={personality.internal_conflict} />
          {personality.fears.length > 0 && (
            <div className="mt-1">
              <span className="text-xs text-gray-500">Fears</span>
              <Tags items={personality.fears} />
            </div>
          )}
          {personality.desires.length > 0 && (
            <div className="mt-1">
              <span className="text-xs text-gray-500">Desires</span>
              <Tags items={personality.desires} />
            </div>
          )}
        </Section>
      )}

      {/* Character DNA */}
      {dna && (
        <Section title="Character DNA">
          <div className="text-xs text-gray-400 space-y-1">
            <div>
              <span className="text-gray-500">Face:</span>{" "}
              {dna.face.face_shape}, {dna.face.eye_color} eyes, {dna.face.skin_tone}
            </div>
            <div>
              <span className="text-gray-500">Hair:</span>{" "}
              {dna.hair.color} {dna.hair.style}, {dna.hair.length}
            </div>
            <div>
              <span className="text-gray-500">Body:</span>{" "}
              {dna.body.height}, {dna.body.build}
            </div>
            <div>
              <span className="text-gray-500">Age:</span> {dna.age_appearance}
            </div>
            {dna.default_outfit && (
              <div>
                <span className="text-gray-500">Outfit:</span>{" "}
                {dna.default_outfit.description}
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Arc */}
      {arc && (
        <Section title="Character Arc">
          <Field label="Type" value={arc.arc_type.replace(/_/g, " ")} />
          <Field label="Start" value={arc.starting_state} />
          <Field label="Catalyst" value={arc.catalyst} />
          <Field label="End" value={arc.ending_state} />
          {arc.progression.length > 0 && (
            <div className="mt-1">
              <span className="text-xs text-gray-500">Progression</span>
              <ol className="text-xs text-gray-400 list-decimal list-inside mt-0.5 space-y-0.5">
                {arc.progression.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
        </Section>
      )}

      {/* Relationships */}
      {relationships.length > 0 && (
        <Section title="Relationships">
          <div className="space-y-2">
            {relationships.map((rel) => (
              <div key={rel.target_character_id} className="text-sm">
                <div className="font-medium text-gray-300">
                  {rel.target_character_name}
                </div>
                <div className="text-xs text-gray-500">
                  {rel.relationship_type} · {rel.dynamic}
                </div>
                {rel.description && (
                  <div className="text-xs text-gray-400 mt-0.5">
                    {rel.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Tags */}
      {character.tags.length > 0 && (
        <Section title="Tags">
          <Tags items={character.tags} />
        </Section>
      )}
    </div>
  );
}
