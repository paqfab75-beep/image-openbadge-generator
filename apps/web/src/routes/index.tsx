import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";

import {
  ARCS,
  INITIAL_FORM,
  OTHER_SHAPES,
  PICTOS,
  SHAPE_CHOICES,
  TITLE_PLACEMENTS,
  buildChartePayload,
  buildGeneratePayload,
} from "../badge-form";
import type { BadgeFormState } from "../badge-form";
import { extractCharte, generateBadge, generatedBadgeToDataUrl } from "../api/badges";
import type { GeneratedBadge } from "../api/badges";

const HEX = /^#[0-9a-fA-F]{6}$/u;
const MAX_PNG_BYTES = 250 * 1024;

const HexColorField = ({
  value,
  onChange,
  onRemove,
  removable,
}: {
  value: string;
  onChange: (value: string) => void;
  onRemove: () => void;
  removable: boolean;
}) => {
  const valid = HEX.test(value);
  return (
    <div className="flex items-center gap-2">
      <input
        type="color"
        aria-label="Choisir une couleur"
        value={valid ? value : "#000000"}
        onChange={(event) => onChange(event.target.value)}
        className="h-9 w-9 shrink-0 cursor-pointer rounded border border-neutral-300 bg-transparent p-0"
      />
      <input
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={`w-24 rounded border px-2 py-1.5 text-sm ${valid ? "border-neutral-300" : "border-red-400"}`}
        dir="ltr"
      />
      {removable && (
        <button type="button" onClick={onRemove} className="text-sm text-neutral-500 hover:text-red-600">
          Retirer
        </button>
      )}
    </div>
  );
};

const CharteSection = ({
  form,
  setForm,
}: {
  form: BadgeFormState;
  setForm: (update: Partial<BadgeFormState>) => void;
}) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [charteError, setCharteError] = useState<string | null>(null);

  const onPdf = (event: ChangeEvent<HTMLInputElement>) => {
    setCharteError(null);
    setForm({ chartePdf: event.target.files?.[0] ?? null });
  };

  const analyze = async () => {
    setAnalyzing(true);
    setCharteError(null);
    try {
      const { colors } = await extractCharte(await buildChartePayload(form));
      setForm({ colors });
    } catch (error) {
      setCharteError(error instanceof Error ? error.message : "L'analyse a échoué.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <section className="rounded-lg border border-neutral-200 p-5">
      <h2 className="mb-1 text-lg font-semibold">1 · Charte graphique</h2>
      <p className="mb-4 text-sm text-neutral-600">
        Un PDF de charte, un site web de référence, et/ou vos couleurs (la première est la couleur
        principale du badge, la suivante sert de contour et de pictos).
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block font-medium">PDF de charte</span>
          <input
            type="file"
            accept="application/pdf"
            onChange={onPdf}
            className="w-full text-sm file:mr-2 file:rounded file:border-0 file:bg-neutral-100 file:px-3 file:py-1.5 file:text-sm"
          />
          {form.chartePdf && (
            <span className="mt-1 block text-neutral-500">
              {form.chartePdf.name} ({Math.round(form.chartePdf.size / 1024)} Ko)
            </span>
          )}
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium">Site web de référence</span>
          <input
            type="url"
            value={form.siteUrl}
            onChange={(event) => setForm({ siteUrl: event.target.value })}
            placeholder="https://exemple.org"
            className="w-full rounded border border-neutral-300 px-3 py-1.5 text-sm"
          />
        </label>
      </div>

      <div className="mt-3">
        <button
          type="button"
          onClick={analyze}
          disabled={analyzing || (!form.chartePdf && !form.siteUrl.trim())}
          className="rounded bg-neutral-800 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
        >
          {analyzing ? "Analyse…" : "Extraire les couleurs de la charte"}
        </button>
        {charteError && <p className="mt-2 text-sm text-red-600">{charteError}</p>}
      </div>

      <div className="mt-4">
        <span className="mb-2 block text-sm font-medium">Couleurs à utiliser</span>
        <div className="flex flex-wrap items-center gap-3">
          {form.colors.map((color, index) => (
            <HexColorField
              key={index}
              value={color}
              removable={form.colors.length > 1}
              onChange={(value) =>
                setForm({ colors: form.colors.map((c, i) => (i === index ? value : c)) })
              }
              onRemove={() => setForm({ colors: form.colors.filter((_, i) => i !== index) })}
            />
          ))}
          {form.colors.length < 8 && (
            <button
              type="button"
              onClick={() => setForm({ colors: [...form.colors, "#888888"] })}
              className="text-sm text-blue-700 hover:underline"
            >
              + Ajouter une couleur
            </button>
          )}
        </div>
      </div>
    </section>
  );
};

const ShapeSection = ({
  form,
  setForm,
}: {
  form: BadgeFormState;
  setForm: (update: Partial<BadgeFormState>) => void;
}) => (
  <section className="rounded-lg border border-neutral-200 p-5">
    <h2 className="mb-1 text-lg font-semibold">2 · Forme du badge</h2>
    <p className="mb-4 text-sm text-neutral-600">
      Le graphisme exclusivement. Le PNG reste carré 1000 × 1000.
    </p>
    <div className="flex flex-col gap-2">
      {SHAPE_CHOICES.map((choice) => (
        <label key={choice.value} className="flex items-start gap-2 text-sm">
          <input
            type="radio"
            name="shape"
            value={choice.value}
            checked={form.shape === choice.value}
            onChange={() => setForm({ shape: choice.value })}
            className="mt-0.5"
          />
          <span>
            <span className="font-medium">{choice.label}</span>
            <span className="text-neutral-500"> — {choice.hint}</span>
          </span>
        </label>
      ))}
      {form.shape === "other" && (
        <div className="ml-6 flex flex-wrap gap-4 rounded bg-neutral-50 p-3">
          {OTHER_SHAPES.map((option) => (
            <label key={option.value} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="otherShape"
                value={option.value}
                checked={form.otherShape === option.value}
                onChange={() => setForm({ otherShape: option.value })}
              />
              {option.label}
            </label>
          ))}
        </div>
      )}
    </div>
  </section>
);

const PictosSection = ({
  form,
  setForm,
}: {
  form: BadgeFormState;
  setForm: (update: Partial<BadgeFormState>) => void;
}) => {
  const toggle = (value: string) =>
    setForm({
      pictos: form.pictos.includes(value)
        ? form.pictos.filter((picto) => picto !== value)
        : form.pictos.length < 3
          ? [...form.pictos, value]
          : form.pictos,
    });

  return (
    <section className="rounded-lg border border-neutral-200 p-5">
      <h2 className="mb-1 text-lg font-semibold">3 · Pictogrammes</h2>
      <p className="mb-4 text-sm text-neutral-600">
        Question 3 : y a-t-il des pictos à faire figurer ? Trois au maximum ; un caractère simple
        (★, ✓, ⚡) marche aussi.
      </p>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {PICTOS.map((picto) => (
          <label key={picto.value} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.pictos.includes(picto.value)}
              disabled={!form.pictos.includes(picto.value) && form.pictos.length >= 3}
              onChange={() => toggle(picto.value)}
            />
            {picto.label}
          </label>
        ))}
      </div>
      <label className="mt-4 block text-sm">
        <span className="mb-1 block font-medium">Picto en caractère libre (1 à 3 caractères, ex. ★)</span>
        <input
          type="text"
          value={form.pictoFree}
          maxLength={3}
          onChange={(event) => setForm({ pictoFree: event.target.value })}
          className="w-40 rounded border border-neutral-300 px-3 py-1.5 text-sm"
        />
      </label>
    </section>
  );
};

const TitleSection = ({
  form,
  setForm,
}: {
  form: BadgeFormState;
  setForm: (update: Partial<BadgeFormState>) => void;
}) => (
  <section className="rounded-lg border border-neutral-200 p-5">
    <h2 className="mb-1 text-lg font-semibold">4 · Titre du badge</h2>
    <p className="mb-4 text-sm text-neutral-600">Question 4 : quel titre, et où doit-il se placer ?</p>
    <label className="block text-sm">
      <span className="mb-1 block font-medium">Titre</span>
      <input
        type="text"
        value={form.title}
        maxLength={80}
        onChange={(event) => setForm({ title: event.target.value })}
        placeholder="Ex. Data Scientist"
        className="w-full rounded border border-neutral-300 px-3 py-1.5 text-sm"
      />
    </label>
    <fieldset className="mt-4">
      <legend className="mb-2 text-sm font-medium">Placement du titre</legend>
      <div className="flex flex-wrap gap-x-5 gap-y-2">
        {TITLE_PLACEMENTS.map((placement) => (
          <label key={placement.value} className="flex items-center gap-2 text-sm">
            <input
              type="radio"
              name="titlePlacement"
              value={placement.value}
              checked={form.titlePlacement === placement.value}
              onChange={() => setForm({ titlePlacement: placement.value })}
            />
            {placement.label}
          </label>
        ))}
      </div>
    </fieldset>
  </section>
);

const ProjectSection = ({
  form,
  setForm,
}: {
  form: BadgeFormState;
  setForm: (update: Partial<BadgeFormState>) => void;
}) => (
  <section className="rounded-lg border border-neutral-200 p-5">
    <h2 className="mb-1 text-lg font-semibold">5 · Nom de projet autour du badge</h2>
    <p className="mb-4 text-sm text-neutral-600">
      Question 5 : optionnel — il suivra le pourtour, sur l'arc choisi.
    </p>
    <div className="grid gap-4 md:grid-cols-[2fr_1fr]">
      <label className="block text-sm">
        <span className="mb-1 block font-medium">Nom du projet</span>
        <input
          type="text"
          value={form.projectName}
          maxLength={80}
          onChange={(event) => setForm({ projectName: event.target.value })}
          placeholder="Ex. Académie du numérique"
          className="w-full rounded border border-neutral-300 px-3 py-1.5 text-sm"
        />
      </label>
      <fieldset className="text-sm">
        <legend className="mb-2 font-medium">Position</legend>
        <div className="flex gap-4">
          {ARCS.map((arc) => (
            <label key={arc.value} className="flex items-center gap-2">
              <input
                type="radio"
                name="projectPosition"
                value={arc.value}
                disabled={!form.projectName.trim()}
                checked={form.projectPosition === arc.value}
                onChange={() => setForm({ projectPosition: arc.value })}
              />
              {arc.label}
            </label>
          ))}
        </div>
      </fieldset>
    </div>
  </section>
);

const BackgroundSection = ({
  form,
  setForm,
}: {
  form: BadgeFormState;
  setForm: (update: Partial<BadgeFormState>) => void;
}) => (
  <section className="rounded-lg border border-neutral-200 p-5">
    <h2 className="mb-1 text-lg font-semibold">6 · Fond (optionnel)</h2>
    <p className="mb-4 text-sm text-neutral-600">
      Question 6 : sans fond, le reste du PNG est transparent. Une couleur ou une image peut
      remplir le carré derrière la forme du badge.
    </p>
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={form.backgroundEnabled}
        onChange={(event) => setForm({ backgroundEnabled: event.target.checked })}
      />
      Utiliser un fond
    </label>
    {form.backgroundEnabled && (
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Couleur de fond</span>
          <HexColorField
            value={form.backgroundColor || "#f5f5f4"}
            onChange={(value) => setForm({ backgroundColor: value })}
            onRemove={() => setForm({ backgroundColor: "" })}
            removable={false}
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block font-medium">Ou une image de fond</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(event) => setForm({ backgroundImage: event.target.files?.[0] ?? null })}
            className="w-full text-sm file:mr-2 file:rounded file:border-0 file:bg-neutral-100 file:px-3 file:py-1.5 file:text-sm"
          />
          {form.backgroundImage && (
            <span className="mt-1 block text-neutral-500">
              {form.backgroundImage.name} ({Math.round(form.backgroundImage.size / 1024)} Ko)
            </span>
          )}
        </label>
      </div>
    )}
  </section>
);

const Home = () => {
  const [form, setFormState] = useState<BadgeFormState>(INITIAL_FORM);
  const setForm = (update: Partial<BadgeFormState>) =>
    setFormState((previous) => ({ ...previous, ...update }));
  const [badge, setBadge] = useState<GeneratedBadge | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const canGenerate = form.title.trim().length > 0;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setGenerating(true);
    setError(null);
    try {
      setBadge(await generateBadge(await buildGeneratePayload(form)));
    } catch (caught) {
      setBadge(null);
      setError(caught instanceof Error ? caught.message : "La génération a échoué.");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-full max-w-3xl flex-col gap-5 p-8">
      <header>
        <p className="text-sm text-neutral-500">Générateur d'images d'Open Badges</p>
        <h1 className="text-3xl font-semibold">Créer le visuel d'un Open Badge</h1>
        <p className="mt-1 text-sm text-neutral-600">
          Vous obtenez un PNG carré de 1000 × 1000 pixels, 250 Ko maximum, prêt à émettre.
        </p>
      </header>

      <form onSubmit={submit} className="flex flex-col gap-5" noValidate>
        <CharteSection form={form} setForm={setForm} />
        <ShapeSection form={form} setForm={setForm} />
        <PictosSection form={form} setForm={setForm} />
        <TitleSection form={form} setForm={setForm} />
        <ProjectSection form={form} setForm={setForm} />
        <BackgroundSection form={form} setForm={setForm} />

        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={!canGenerate || generating}
            className="rounded bg-blue-700 px-6 py-2 font-medium text-white disabled:opacity-40"
          >
            {generating ? "Génération…" : "Générer le badge"}
          </button>
          {!canGenerate && (
            <span className="text-sm text-neutral-500">Renseignez d'abord le titre.</span>
          )}
        </div>
      </form>

      {error && (
        <p role="alert" className="rounded border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          {error}
        </p>
      )}

      {badge && (
        <section className="rounded-lg border border-neutral-200 p-5" aria-label="Badge généré">
          <h2 className="mb-3 text-lg font-semibold">Votre badge</h2>
          <div className="flex flex-col items-start gap-4 md:flex-row md:items-center">
            <img
              src={generatedBadgeToDataUrl(badge)}
              alt="Aperçu du badge généré"
              width={240}
              height={240}
              className="rounded border border-neutral-200"
            />
            <div className="text-sm">
              <p>
                PNG {badge.width} × {badge.height} px — {(badge.size_bytes / 1024).toFixed(0)} Ko
                {badge.size_bytes <= MAX_PNG_BYTES ? (
                  <span className="ml-2 rounded bg-green-100 px-2 py-0.5 text-green-800">
                    ≤ 250 Ko ✓
                  </span>
                ) : (
                  <span className="ml-2 rounded bg-red-100 px-2 py-0.5 text-red-800">trop lourd</span>
                )}
              </p>
              <a
                href={generatedBadgeToDataUrl(badge)}
                download="open-badge.png"
                className="mt-3 inline-block rounded bg-neutral-800 px-4 py-1.5 font-medium text-white"
              >
                Télécharger le PNG
              </a>
            </div>
          </div>
        </section>
      )}

      <footer className="pb-4 text-xs text-neutral-400">
        L'analyse de charte reste facultative : vos couleurs saisies à la main ont le dernier mot.
      </footer>
    </main>
  );
};

export const Route = createFileRoute("/")({
  component: Home,
});
