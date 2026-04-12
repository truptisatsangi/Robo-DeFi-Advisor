import { useState } from "react";

// ---------------------------------------------------------------------------
// Inline markdown parser: **bold**, `code`, _italic_, [text](url)
// ---------------------------------------------------------------------------
function Inline({ text }) {
  if (!text) return null;
  const parts = [];
  let i = 0;
  let buf = "";
  let key = 0;

  const flush = () => {
    if (buf) { parts.push(<span key={key++}>{buf}</span>); buf = ""; }
  };

  while (i < text.length) {
    // **bold**
    if (text.slice(i, i + 2) === "**") {
      const end = text.indexOf("**", i + 2);
      if (end !== -1) {
        flush();
        parts.push(
          <strong key={key++} className="font-semibold text-slate-100">
            {text.slice(i + 2, end)}
          </strong>
        );
        i = end + 2;
        continue;
      }
    }
    // `code`
    if (text[i] === "`") {
      const end = text.indexOf("`", i + 1);
      if (end !== -1) {
        flush();
        parts.push(
          <code key={key++} className="rounded bg-slate-800 px-1 py-0.5 font-mono text-xs text-sky-300">
            {text.slice(i + 1, end)}
          </code>
        );
        i = end + 1;
        continue;
      }
    }
    // _italic_ (only when preceded by space/start)
    if (text[i] === "_" && (i === 0 || text[i - 1] === " ")) {
      const end = text.indexOf("_", i + 1);
      if (end !== -1) {
        flush();
        parts.push(
          <em key={key++} className="text-slate-500">
            {text.slice(i + 1, end)}
          </em>
        );
        i = end + 1;
        continue;
      }
    }
    // [link text](url)
    if (text[i] === "[") {
      const bracket = text.indexOf("]", i);
      if (bracket !== -1 && text[bracket + 1] === "(") {
        const paren = text.indexOf(")", bracket + 2);
        if (paren !== -1) {
          flush();
          const linkText = text.slice(i + 1, bracket);
          const linkUrl = text.slice(bracket + 2, paren);
          parts.push(
            <a
              key={key++}
              href={linkUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-400 hover:underline"
            >
              {linkText} ↗
            </a>
          );
          i = paren + 1;
          continue;
        }
      }
    }
    buf += text[i];
    i++;
  }
  flush();
  return <>{parts}</>;
}

// ---------------------------------------------------------------------------
// Markdown table renderer
// ---------------------------------------------------------------------------
function MdTable({ lines }) {
  if (lines.length < 3) return null; // need header + separator + at least one row
  const parseRow = (line) =>
    line
      .split("|")
      .map((c) => c.trim())
      .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);

  const headers = parseRow(lines[0]);
  const rows = lines.slice(2).map(parseRow); // skip `| --- |` separator row

  return (
    <div className="my-3 overflow-x-auto rounded-md border border-slate-700">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-800/60">
          <tr>
            {headers.map((h, i) => (
              <th
                key={i}
                className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-400"
              >
                <Inline text={h} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-t border-slate-700/60 hover:bg-slate-800/20">
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2 text-slate-300">
                  <Inline text={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Block-level markdown renderer
// ---------------------------------------------------------------------------
function renderMarkdown(markdown) {
  if (!markdown) return <p className="text-slate-500">No proposal draft yet.</p>;

  const lines = markdown.split("\n");
  const elements = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // ## Heading 2
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={key++} className="mb-2 mt-5 text-base font-bold text-slate-100">
          <Inline text={line.slice(3)} />
        </h2>
      );
      i++;
      continue;
    }

    // ### Heading 3
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={key++} className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wider text-sky-400">
          <Inline text={line.slice(4)} />
        </h3>
      );
      i++;
      continue;
    }

    // Table — collect consecutive | lines
    if (line.startsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      elements.push(<MdTable key={key++} lines={tableLines} />);
      continue;
    }

    // --- horizontal rule
    if (line.trim() === "---") {
      elements.push(<hr key={key++} className="my-3 border-slate-700" />);
      i++;
      continue;
    }

    // - Bullet list: collect consecutive "- " lines (with optional indented continuation)
    if (line.startsWith("- ")) {
      const listItems = [];
      let lk = 0;
      while (i < lines.length && lines[i].startsWith("- ")) {
        listItems.push(
          <li key={lk++} className="mb-0.5 leading-relaxed text-slate-300">
            <Inline text={lines[i].slice(2)} />
          </li>
        );
        i++;
        // Indented continuation (e.g. `  _Mandate: ...`)
        while (i < lines.length && lines[i].startsWith("  ") && !lines[i].startsWith("- ")) {
          const trimmed = lines[i].trimStart();
          if (trimmed) {
            listItems.push(
              <li key={lk++} className="ml-4 mt-0.5 text-xs text-slate-500">
                <Inline text={trimmed} />
              </li>
            );
          }
          i++;
        }
      }
      elements.push(
        <ul key={key++} className="my-1 list-none space-y-0 pl-0">
          {listItems}
        </ul>
      );
      continue;
    }

    // *Footer line* (starts and ends with *)
    if (line.startsWith("*") && line.endsWith("*") && line.length > 2) {
      elements.push(
        <p key={key++} className="mt-3 text-xs italic text-slate-500">
          {line.slice(1, -1)}
        </p>
      );
      i++;
      continue;
    }

    // Blank line
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Default paragraph
    elements.push(
      <p key={key++} className="my-1 leading-relaxed text-slate-300">
        <Inline text={line} />
      </p>
    );
    i++;
  }

  return elements;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
function ProposalPanel({ draft }) {
  const [copied, setCopied] = useState(false);

  async function copyDraft() {
    if (!draft) return;
    await navigator.clipboard.writeText(draft);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className="card">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Proposal Draft</h3>
          <p className="text-xs text-slate-500">Governance-ready — copy to Snapshot / Tally</p>
        </div>
        <button
          type="button"
          onClick={copyDraft}
          disabled={!draft}
          className="rounded-md border border-slate-700 px-3 py-1 text-xs text-slate-200 transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {copied ? "✓ Copied!" : "Copy Markdown"}
        </button>
      </div>
      <div className="max-h-[32rem] overflow-auto rounded-md border border-slate-800 bg-slate-900/40 px-5 py-4 text-sm">
        {renderMarkdown(draft)}
      </div>
    </section>
  );
}

export default ProposalPanel;
