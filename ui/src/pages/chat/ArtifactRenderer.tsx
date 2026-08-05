import { memo } from "react";
export interface ScreenshotMeta {
  url: string | null;
  caption: string | null;
}

export function parseScreenshotMeta(content: string): ScreenshotMeta {
  try {
    const data = JSON.parse(content) as Record<string, unknown>;
    const artifactId = typeof data?.artifact_id === "string" ? data.artifact_id : null;
    if (artifactId) {
      return {
        url: `/api/v1/artifacts/${encodeURIComponent(artifactId)}`,
        caption: typeof data?.filename === "string" ? data.filename : "Screenshot",
      };
    }
    const path = typeof data?.screenshot_path === "string" ? data.screenshot_path : "";
    const filename = path ? String(path.split(/[\\/]/).pop()) : "";
    const url = filename ? `/api/v1/screenshots/${encodeURIComponent(filename)}` : null;
    const title = typeof data?.title === "string" && data.title ? data.title : null;
    const pageUrl = typeof data?.url === "string" && data.url ? data.url : null;
    return {
      url,
      caption: title ?? pageUrl ?? `Screenshot${data?.format ? ` (${data.format})` : ""}`,
    };
  } catch {
    return { url: null, caption: null };
  }
}

export const ArtifactRenderer = memo(({ content }: { content: string }) => {
  const meta = parseScreenshotMeta(content);
  if (!meta.url) return null;

  return (
    <figure className="artifact-card fade-in">
      <a href={meta.url} target="_blank" rel="noopener noreferrer" title="Open full-size screenshot in a new tab">
        <img className="artifact-screenshot" loading="lazy" src={meta.url} alt={meta.caption ?? "Screenshot"} />
      </a>
      {meta.caption && (
        <figcaption className="artifact-caption">
          <span>{meta.caption}</span>
        </figcaption>
      )}
    </figure>
  );
});
