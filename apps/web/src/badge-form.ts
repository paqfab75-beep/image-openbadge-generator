/**
 * The badge form's shared state and the API payload built from it.
 *
 * Kept out of the route file so tests exercise the payload rules — the shape's "autre" resolution,
 * the pictos merge, the optional background — without rendering.
 */

export type BadgeShape =
  | "circle"
  | "square"
  | "rounded_square"
  | "hexagon"
  | "diamond";

export type TitlePlacement = "center" | "top" | "bottom" | "ring";
export type Arc = "top" | "bottom";

export interface BadgeFormState {
  colors: string[];
  chartePdf: File | null;
  siteUrl: string;
  shape: "circle" | "square" | "other";
  otherShape: Exclude<BadgeShape, "circle" | "square">;
  pictos: string[];
  pictoFree: string;
  title: string;
  titlePlacement: TitlePlacement;
  projectName: string;
  projectPosition: Arc;
  backgroundColor: string;
  backgroundEnabled: boolean;
  backgroundImage: File | null;
}

export const INITIAL_FORM: BadgeFormState = {
  colors: ["#1d4ed8", "#f4b41a"],
  chartePdf: null,
  siteUrl: "",
  shape: "circle",
  otherShape: "hexagon",
  pictos: [],
  pictoFree: "",
  title: "",
  titlePlacement: "center",
  projectName: "",
  projectPosition: "bottom",
  backgroundColor: "",
  backgroundEnabled: false,
  backgroundImage: null,
};

export const SHAPE_CHOICES: readonly {
  readonly value: BadgeFormState["shape"];
  readonly label: string;
  readonly hint: string;
}[] = [
  { value: "circle", label: "Rond", hint: "Le médaillon circulaire classique des Open Badges" },
  { value: "square", label: "Carré", hint: "Angles droits, plein cadre" },
  { value: "other", label: "Une autre forme", hint: "Carré arrondi, hexagone ou losange" },
];

export const OTHER_SHAPES: readonly { readonly value: BadgeFormState["otherShape"]; readonly label: string }[] = [
  { value: "rounded_square", label: "Carré arrondi" },
  { value: "hexagon", label: "Hexagone" },
  { value: "diamond", label: "Losange" },
];

export const TITLE_PLACEMENTS: readonly { readonly value: TitlePlacement; readonly label: string }[] = [
  { value: "center", label: "Centré" },
  { value: "top", label: "En haut" },
  { value: "bottom", label: "En bas" },
  { value: "ring", label: "Sur le pourtour" },
];

export const ARCS: readonly { readonly value: Arc; readonly label: string }[] = [
  { value: "top", label: "En haut" },
  { value: "bottom", label: "En bas" },
];

export const PICTOS: readonly { readonly value: string; readonly label: string }[] = [
  { value: "star", label: "Étoile" },
  { value: "check", label: "Coche" },
  { value: "medal", label: "Médaille" },
  { value: "trophy", label: "Trophée" },
  { value: "gear", label: "Engrenage" },
  { value: "flag", label: "Drapeau" },
  { value: "book", label: "Livre" },
  { value: "certificate", label: "Certificat" },
];

export const MAX_PNG_BYTES = 250 * 1024;

export const resolvedShape = (state: Pick<BadgeFormState, "shape" | "otherShape">): BadgeShape =>
  state.shape === "other" ? state.otherShape : state.shape;

export const mergedPictos = (state: Pick<BadgeFormState, "pictos" | "pictoFree">): string[] => {
  const free = state.pictoFree.trim();
  return [...state.pictos, ...(free && free.length <= 3 ? [free] : [])].slice(0, 3);
};

export const cleanColors = (state: Pick<BadgeFormState, "colors">): string[] =>
  state.colors.filter((color) => /^#[0-9a-fA-F]{6}$/u.test(color));

export const fileToBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result);
      resolve(dataUrl.slice(dataUrl.indexOf(",") + 1));
    };
    reader.onerror = () => reject(reader.error ?? new Error("Lecture du fichier impossible"));
    reader.readAsDataURL(file);
  });

export interface BuildGeneratePayloadInput
  extends Pick<BadgeFormState, "colors" | "shape" | "otherShape" | "pictos" | "pictoFree" | "title" | "titlePlacement" | "projectName" | "projectPosition" | "backgroundColor" | "backgroundEnabled" | "backgroundImage"> {}

export interface GeneratePayload {
  title: string;
  title_placement: TitlePlacement;
  shape: BadgeShape;
  pictos: string[];
  project_name: string | null;
  project_position: Arc;
  colors: string[];
  background_color: string | null;
  background_image_b64: string | null;
}

export const buildGeneratePayload = async (
  state: BuildGeneratePayloadInput
): Promise<GeneratePayload> => ({
  title: state.title.trim(),
  title_placement: state.titlePlacement,
  shape: resolvedShape(state),
  pictos: mergedPictos(state),
  project_name: state.projectName.trim() || null,
  project_position: state.projectPosition,
  colors: cleanColors(state),
  background_color:
    state.backgroundEnabled && /^#[0-9a-fA-F]{6}$/u.test(state.backgroundColor)
      ? state.backgroundColor
      : null,
  background_image_b64: state.backgroundEnabled && state.backgroundImage
    ? await fileToBase64(state.backgroundImage)
    : null,
});

export interface ChartePayload {
  pdf_b64?: string;
  url?: string;
}

export const buildChartePayload = async (
  state: Pick<BadgeFormState, "chartePdf" | "siteUrl">
): Promise<ChartePayload> => {
  if (state.chartePdf) {
    return { pdf_b64: await fileToBase64(state.chartePdf) };
  }
  const url = state.siteUrl.trim();
  return url ? { url: /^https?:\/\//iu.test(url) ? url : `https://${url}` } : {};
};
