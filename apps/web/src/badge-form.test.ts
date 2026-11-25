import { describe, expect, test } from "bun:test";

import {
  INITIAL_FORM,
  buildChartePayload,
  buildGeneratePayload,
  cleanColors,
  mergedPictos,
  resolvedShape,
} from "./badge-form";

describe("resolvedShape", () => {
  test("`autre` delegates to the picked shape", () => {
    expect(resolvedShape({ shape: "other", otherShape: "hexagon" })).toBe("hexagon");
    expect(resolvedShape({ shape: "circle", otherShape: "hexagon" })).toBe("circle");
  });
});

describe("mergedPictos", () => {
  test("caps at three and keeps a single free character", () => {
    expect(mergedPictos({ pictos: ["star", "check"], pictoFree: "★" })).toEqual(["star", "check", "★"]);
    expect(mergedPictos({ pictos: ["star", "check", "medal"], pictoFree: "★" })).toHaveLength(3);
  });

  test("ignores free text that is a word, not a glyph", () => {
    expect(mergedPictos({ pictos: [], pictoFree: "nova" })).toEqual([]);
  });
});

describe("cleanColors", () => {
  test("keeps only well-formed hex colors", () => {
    expect(cleanColors({ colors: ["#123abc", "bleu", "", "#abc"] })).toEqual(["#123abc"]);
  });
});

describe("buildGeneratePayload", () => {
  test("maps the form to the API spec", async () => {
    const payload = await buildGeneratePayload({
      ...INITIAL_FORM,
      title: " Data Scientist ",
      projectName: "Académie du numérique",
      backgroundColor: "#eeeeee",
      backgroundEnabled: true,
    });
    expect(payload).toMatchObject({
      title: "Data Scientist",
      title_placement: "center",
      shape: "circle",
      project_name: "Académie du numérique",
      project_position: "bottom",
      colors: INITIAL_FORM.colors,
      background_color: "#eeeeee",
      background_image_b64: null,
    });
  });

  test("an untouched background sends no color and no image", async () => {
    const payload = await buildGeneratePayload({ ...INITIAL_FORM, title: "X" });
    expect(payload.background_color).toBeNull();
    expect(payload.background_image_b64).toBeNull();
  });
});

describe("buildChartePayload", () => {
  test("prefers the PDF and qualifies a bare domain as https", async () => {
    expect(await buildChartePayload({ chartePdf: null, siteUrl: "exemple.org" })).toEqual({
      url: "https://exemple.org",
    });
  });

  test("an empty charte sends an empty object", async () => {
    expect(await buildChartePayload({ chartePdf: null, siteUrl: "  " })).toEqual({});
  });
});
