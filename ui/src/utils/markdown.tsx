import { Fragment, type ReactNode } from "react";

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

interface InlinePart {
  text: string;
  code?: boolean;
  bold?: boolean;
  italic?: boolean;
  link?: string;
  image?: { url: string; alt: string };
}

const INLINE_RE =
  /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(!\[[^\]]*\]\([^)]+\))|(\[[^\]]+\]\([^)]+\))/g;

function parseInline(raw: string): InlinePart[] {
  const parts: InlinePart[] = [];
  let last = 0;
  for (const match of raw.matchAll(INLINE_RE)) {
    if (match.index !== undefined && match.index > last) {
      parts.push({ text: raw.slice(last, match.index) });
    }
    if (match[1]) parts.push({ text: match[1].slice(1, -1), code: true });
    else if (match[2]) parts.push({ text: match[2].slice(2, -2), bold: true });
    else if (match[3]) parts.push({ text: match[3].slice(1, -1), italic: true });
    else if (match[4]) {
      const inner = match[4];
      const close = inner.lastIndexOf("](");
      parts.push({
        text: inner,
        image: {
          alt: inner.slice(2, close),
          url: inner.slice(close + 2, -1)
        }
      });
    }
    else if (match[5]) {
      const inner = match[5];
      const close = inner.lastIndexOf("](");
      parts.push({
        text: inner.slice(1, close),
        link: inner.slice(close + 2, -1),
      });
    }
    last = match.index + match[0].length;
  }
  if (last < raw.length) parts.push({ text: raw.slice(last) });
  return parts;
}

function renderInline(text: string, keyPrefix: string): ReactNode {
  return parseInline(text).map((part, i) => {
    let node: ReactNode = part.text;
    if (part.code) node = <code key={i}>{escapeHtml(part.text)}</code>;
    else if (part.bold) node = <strong key={i}>{part.text}</strong>;
    else if (part.italic) node = <em key={i}>{part.text}</em>;
    else if (part.image) {
      const url = part.image.url.startsWith("artifact:") 
        ? `/api/v1/artifacts/${part.image.url.replace("artifact:", "")}` 
        : part.image.url;
      node = (
        <figure className="tool-screenshot" key={i}>
          <a href={url} target="_blank" rel="noopener noreferrer">
            <img src={url} alt={part.image.alt} loading="lazy" />
          </a>
        </figure>
      );
    }
    else if (part.link) node = <a key={i} href={part.link} target="_blank" rel="noreferrer">{part.text}</a>;
    else node = escapeHtml(part.text);
    return <Fragment key={`${keyPrefix}-${i}`}>{node}</Fragment>;
  });
}

export function Markdown({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/).filter((b) => b.trim().length > 0);
  const rendered: ReactNode[] = [];

  blocks.forEach((block, index) => {
    const trimmed = block.trim();
    if (trimmed.startsWith("```")) {
      const end = block.indexOf("```", 3);
      if (end !== -1) {
        const code = block.slice(3, end).replace(/^[^\n]*\n/, "");
        rendered.push(
          <pre key={index}>
            <code>{escapeHtml(code.trimEnd())}</code>
          </pre>,
        );
        return;
      }
    }
    if (/^#{1,4}\s/.test(trimmed)) {
      const match = trimmed.match(/^(#{1,4})\s+(.+)$/);
      const level = match ? match[1].length : 1;
      const content = match ? match[2] : trimmed;
      const HeadingTag = level === 1 ? "h1" : level === 2 ? "h2" : level === 3 ? "h3" : "h4";
      rendered.push(<HeadingTag key={index}>{renderInline(content, `h${index}`)}</HeadingTag>);
      return;
    }
    if (trimmed.startsWith("|")) {
      const rows = trimmed.split("\n").filter((l) => l.trim().startsWith("|"));
      const header = rows[0].split("|").slice(1, -1).map((c) => c.trim());
      const body = rows.slice(2).map((row) =>
        row.split("|").slice(1, -1).map((c) => c.trim()),
      );
      rendered.push(
        <div className="table-wrap" key={index}>
          <table>
            <thead>
              <tr>{header.map((h, i) => <th key={i}>{renderInline(h, `th${index}-${i}`)}</th>)}</tr>
            </thead>
            <tbody>
              {body.map((row, r) => (
                <tr key={r}>
                  {row.map((cell, c) => <td key={c}>{renderInline(cell, `td${index}-${r}-${c}`)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      return;
    }
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const items = trimmed.split("\n").map((l) => l.replace(/^[-*]\s+/, ""));
      rendered.push(
        <ul key={index}>
          {items.map((item, i) => <li key={i}>{renderInline(item, `li${index}-${i}`)}</li>)}
        </ul>,
      );
      return;
    }
    if (/^\d+\.\s/.test(trimmed)) {
      const items = trimmed.split("\n").map((l) => l.replace(/^\d+\.\s+/, ""));
      rendered.push(
        <ol key={index}>
          {items.map((item, i) => <li key={i}>{renderInline(item, `li${index}-${i}`)}</li>)}
        </ol>,
      );
      return;
    }
    if (trimmed.startsWith("> ")) {
      rendered.push(
        <blockquote key={index}>{renderInline(trimmed.replace(/^>\s?/, ""), `bq${index}`)}</blockquote>,
      );
      return;
    }
    const lines = block.split("\n");
    rendered.push(
      <p key={index}>
        {lines.map((line, i) => (
          <Fragment key={i}>
            {i > 0 ? <br /> : null}
            {renderInline(line, `p${index}-${i}`)}
          </Fragment>
        ))}
      </p>,
    );
  });

  return <div className="md">{rendered}</div>;
}
