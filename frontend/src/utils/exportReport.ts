import { jsPDF } from 'jspdf';
import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  BorderStyle,
  Footer,
  Header,
  PageNumber,
} from 'docx';

export interface ExportReportOptions {
  markdown: string;
  query: string;
  reviewId: string;
  title?: string;
}

export type ExportFormat = 'pdf' | 'docx' | 'md' | 'html' | 'txt' | 'print';

/**
 * Helper to download a Blob as a file with a given filename
 */
function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Sanitize filename from query/id
 */
export function getBaseFilename(query: string, reviewId: string): string {
  const sanitized = (query || '')
    .toLowerCase()
    .replace(/[^a-z0-9]/g, '_')
    .replace(/_+/g, '_')
    .slice(0, 36);
  return `literature_review_${sanitized || reviewId}`;
}

/**
 * Extract clean title from markdown or fallback to query
 */
export function extractReportTitle(markdown: string, fallback: string): string {
  const match = markdown.match(/^#\s+(.+)$/m);
  if (match && match[1]) {
    return match[1].trim();
  }
  return fallback || 'Literature Review';
}

/**
 * Export report as Markdown (.md)
 */
export function exportToMarkdown({ markdown, query, reviewId }: ExportReportOptions): void {
  const filename = `${getBaseFilename(query, reviewId)}.md`;
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8;' });
  downloadBlob(blob, filename);
}

/**
 * Export report as Plain Text (.txt)
 */
export function exportToPlainText({ markdown, query, reviewId }: ExportReportOptions): void {
  const filename = `${getBaseFilename(query, reviewId)}.txt`;

  // Clean markdown tokens into pleasant plaintext
  const plainText = markdown
    .replace(/^#+\s+/gm, '') // Remove heading hashes
    .replace(/\*\*(.+?)\*\*/g, '$1') // Remove bold asterisks
    .replace(/\*(.+?)\*/g, '$1') // Remove italic asterisks
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1 ($2)') // Format links as "Title (url)"
    .replace(/^[-*]\s+/gm, '• ') // Uniform bullets
    .replace(/^---+$/gm, '------------------------------------------------------------');

  const blob = new Blob([plainText], { type: 'text/plain;charset=utf-8;' });
  downloadBlob(blob, filename);
}

/**
 * Export report as Standalone HTML (.html)
 */
export function exportToHtml({ markdown, query, reviewId, title }: ExportReportOptions): void {
  const filename = `${getBaseFilename(query, reviewId)}.html`;
  const reportTitle = title || extractReportTitle(markdown, query);
  const now = new Date().toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  // Basic HTML parser for markdown
  const lines = markdown.split('\n');
  const htmlBodyLines: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      continue;
    }

    if (trimmed.startsWith('# ')) {
      htmlBodyLines.push(`<h1>${escapeHtml(trimmed.slice(2))}</h1>`);
    } else if (trimmed.startsWith('## ')) {
      htmlBodyLines.push(`<h2>${escapeHtml(trimmed.slice(3))}</h2>`);
    } else if (trimmed.startsWith('### ')) {
      htmlBodyLines.push(`<h3>${escapeHtml(trimmed.slice(4))}</h3>`);
    } else if (trimmed.startsWith('---')) {
      htmlBodyLines.push('<hr />');
    } else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      const content = parseInlineHtml(trimmed.slice(2));
      htmlBodyLines.push(`<li>${content}</li>`);
    } else {
      const content = parseInlineHtml(trimmed);
      htmlBodyLines.push(`<p>${content}</p>`);
    }
  }

  const htmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(reportTitle)}</title>
  <style>
    :root {
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    body {
      font-family: var(--font-sans);
      line-height: 1.75;
      color: #1e293b;
      background-color: #f8fafc;
      margin: 0;
      padding: 40px 20px;
    }
    .container {
      max-width: 840px;
      margin: 0 auto;
      background: #ffffff;
      padding: 48px 56px;
      border-radius: 16px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .header-meta {
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 24px;
      margin-bottom: 32px;
    }
    .badge {
      display: inline-block;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      padding: 4px 10px;
      border-radius: 6px;
      background: #eef2ff;
      color: #4f46e5;
      margin-bottom: 12px;
    }
    .query-text {
      color: #64748b;
      font-size: 14px;
      margin-top: 6px;
    }
    h1 {
      font-size: 26px;
      font-weight: 800;
      color: #0f172a;
      margin: 12px 0 6px 0;
      line-height: 1.3;
    }
    h2 {
      font-size: 20px;
      font-weight: 700;
      color: #1e293b;
      margin-top: 36px;
      margin-bottom: 14px;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 8px;
    }
    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #334155;
      margin-top: 24px;
      margin-bottom: 10px;
    }
    p {
      margin: 12px 0;
      font-size: 15px;
      color: #334155;
    }
    li {
      margin: 6px 0;
      font-size: 15px;
      color: #334155;
    }
    hr {
      border: none;
      border-top: 1px solid #e2e8f0;
      margin: 32px 0;
    }
    .citation {
      font-family: monospace;
      font-size: 12px;
      background: #f1f5f9;
      color: #4338ca;
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
      font-weight: 600;
    }
    .conflict-badge {
      font-weight: 700;
      background: #fef2f2;
      color: #dc2626;
      border: 1px solid #fecaca;
      padding: 2px 6px;
      border-radius: 4px;
    }
    .agree-badge {
      font-weight: 700;
      background: #f0fdf4;
      color: #16a34a;
      border: 1px solid #bbf7d0;
      padding: 2px 6px;
      border-radius: 4px;
    }
    .footer-note {
      margin-top: 48px;
      padding-top: 20px;
      border-top: 1px solid #e2e8f0;
      font-size: 13px;
      color: #94a3b8;
      font-style: italic;
    }
    @media print {
      body { background: #fff; padding: 0; }
      .container { border: none; box-shadow: none; padding: 0; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header-meta">
      <span class="badge">Synthesized Literature Review</span>
      <div class="query-text"><strong>Research Question:</strong> ${escapeHtml(query)}</div>
      <div class="query-text">Generated: ${now} • Review ID: <code>${escapeHtml(reviewId)}</code></div>
    </div>
    <div class="report-content">
      ${htmlBodyLines.join('\n      ')}
    </div>
    <div class="footer-note">
      Grounded in empirical source papers with page-level citations. Produced by Agentic Literature Review.
    </div>
  </div>
</body>
</html>`;

  const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8;' });
  downloadBlob(blob, filename);
}

/**
 * Export report as Word Document (.docx)
 */
export async function exportToDocx({
  markdown,
  query,
  reviewId,
  title,
}: ExportReportOptions): Promise<void> {
  const filename = `${getBaseFilename(query, reviewId)}.docx`;
  const reportTitle = title || extractReportTitle(markdown, query);
  const now = new Date().toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const lines = markdown.split('\n');
  const paragraphs: Paragraph[] = [];

  // Header Title block
  paragraphs.push(
    new Paragraph({
      text: reportTitle,
      heading: HeadingLevel.TITLE,
      spacing: { after: 120 },
    })
  );

  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({ text: 'Research Question: ', bold: true, color: '475569' }),
        new TextRun({ text: query, italics: true, color: '1E293B' }),
      ],
      spacing: { after: 80 },
    })
  );

  paragraphs.push(
    new Paragraph({
      children: [
        new TextRun({
          text: `Generated on ${now} • Multi-Agent Literature Review Pipeline (${reviewId})`,
          size: 18, // 9pt
          color: '64748B',
        }),
      ],
      border: {
        bottom: {
          color: 'CBD5E1',
          space: 8,
          style: BorderStyle.SINGLE,
          size: 12,
        },
      },
      spacing: { after: 240 },
    })
  );

  // Parse lines
  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      continue;
    }

    if (trimmed.startsWith('# ')) {
      // Top level header
      paragraphs.push(
        new Paragraph({
          text: trimmed.slice(2).trim(),
          heading: HeadingLevel.HEADING_1,
          spacing: { before: 280, after: 120 },
        })
      );
    } else if (trimmed.startsWith('## ')) {
      // Heading 2
      paragraphs.push(
        new Paragraph({
          text: trimmed.slice(3).trim(),
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 240, after: 100 },
        })
      );
    } else if (trimmed.startsWith('### ')) {
      // Heading 3
      paragraphs.push(
        new Paragraph({
          text: trimmed.slice(4).trim(),
          heading: HeadingLevel.HEADING_3,
          spacing: { before: 180, after: 80 },
        })
      );
    } else if (trimmed.startsWith('---')) {
      // Divider
      paragraphs.push(
        new Paragraph({
          border: {
            bottom: {
              color: 'E2E8F0',
              space: 4,
              style: BorderStyle.SINGLE,
              size: 6,
            },
          },
          spacing: { before: 180, after: 180 },
        })
      );
    } else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      // Bullet list item
      const itemText = trimmed.slice(2).trim();
      paragraphs.push(
        new Paragraph({
          children: parseInlineDocx(itemText),
          bullet: { level: 0 },
          spacing: { before: 40, after: 60 },
        })
      );
    } else {
      // Regular paragraph
      paragraphs.push(
        new Paragraph({
          children: parseInlineDocx(trimmed),
          spacing: { before: 60, after: 100 },
        })
      );
    }
  }

  // Document structure
  const doc = new Document({
    title: reportTitle,
    description: `Synthesized literature review for: ${query}`,
    creator: 'Agentic Literature Review Assistant',
    sections: [
      {
        properties: {
          page: {
            margin: {
              top: 1440, // 1 inch
              bottom: 1440,
              left: 1440,
              right: 1440,
            },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [
                  new TextRun({
                    text: 'Agentic Literature Review',
                    size: 16,
                    color: '94A3B8',
                  }),
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({
                    text: 'Page ',
                    size: 16,
                    color: '94A3B8',
                  }),
                  new TextRun({
                    children: [PageNumber.CURRENT],
                    size: 16,
                    color: '94A3B8',
                  }),
                  new TextRun({
                    text: ' of ',
                    size: 16,
                    color: '94A3B8',
                  }),
                  new TextRun({
                    children: [PageNumber.TOTAL_PAGES],
                    size: 16,
                    color: '94A3B8',
                  }),
                ],
              }),
            ],
          }),
        },
        children: paragraphs,
      },
    ],
  });

  const blob = await Packer.toBlob(doc);
  downloadBlob(blob, filename);
}

/**
 * Export report as a clean academic PDF (.pdf) via jsPDF
 */
export function exportToPdf({
  markdown,
  query,
  reviewId,
  title,
}: ExportReportOptions): void {
  const filename = `${getBaseFilename(query, reviewId)}.pdf`;
  const reportTitle = title || extractReportTitle(markdown, query);
  const now = new Date().toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  // A4 portrait: 210mm x 297mm
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = 210;
  const pageHeight = 297;
  const marginLeft = 18;
  const marginRight = 18;
  const marginTop = 20;
  const marginBottom = 20;
  const contentWidth = pageWidth - marginLeft - marginRight; // 174mm

  let cursorY = marginTop + 4;

  // Helper to add page breaks
  const checkPageBreak = (neededHeight: number) => {
    if (cursorY + neededHeight > pageHeight - marginBottom) {
      doc.addPage();
      cursorY = marginTop + 4;
    }
  };

  // Header banner on first page
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8);
  doc.setTextColor(99, 102, 241); // Indigo
  doc.text('AGENTIC LITERATURE REVIEW REPORT', marginLeft, cursorY);
  cursorY += 6;

  // Title
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(15);
  doc.setTextColor(15, 23, 42); // slate-900
  const titleLines = doc.splitTextToSize(reportTitle, contentWidth);
  for (const tLine of titleLines) {
    checkPageBreak(7);
    doc.text(tLine, marginLeft, cursorY);
    cursorY += 6.5;
  }
  cursorY += 1;

  // Query and metadata
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9.5);
  doc.setTextColor(71, 85, 105); // slate-600
  const queryLines = doc.splitTextToSize(`Research Question: ${query}`, contentWidth);
  for (const qLine of queryLines) {
    checkPageBreak(5);
    doc.text(qLine, marginLeft, cursorY);
    cursorY += 4.5;
  }
  cursorY += 1;

  doc.setFontSize(8.5);
  doc.setTextColor(148, 163, 184); // slate-400
  doc.text(`Generated on ${now} • Review ID: ${reviewId}`, marginLeft, cursorY);
  cursorY += 5;

  // Separator bar
  doc.setDrawColor(226, 232, 240);
  doc.setLineWidth(0.4);
  doc.line(marginLeft, cursorY, marginLeft + contentWidth, cursorY);
  cursorY += 6;

  // Parse markdown lines
  const lines = markdown.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      cursorY += 2;
      continue;
    }

    if (trimmed.startsWith('# ')) {
      // H1
      cursorY += 3;
      checkPageBreak(12);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(13);
      doc.setTextColor(15, 23, 42);
      const text = trimmed.slice(2).trim();
      const splitted = doc.splitTextToSize(text, contentWidth);
      for (const line of splitted) {
        checkPageBreak(6);
        doc.text(line, marginLeft, cursorY);
        cursorY += 6;
      }
      cursorY += 2;
    } else if (trimmed.startsWith('## ')) {
      // H2
      cursorY += 3;
      checkPageBreak(10);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11.5);
      doc.setTextColor(30, 41, 59);
      const text = trimmed.slice(3).trim();
      const splitted = doc.splitTextToSize(text, contentWidth);
      for (const line of splitted) {
        checkPageBreak(5.5);
        doc.text(line, marginLeft, cursorY);
        cursorY += 5.5;
      }
      cursorY += 2;
    } else if (trimmed.startsWith('### ')) {
      // H3
      cursorY += 2;
      checkPageBreak(8);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(10.5);
      doc.setTextColor(51, 65, 85);
      const text = trimmed.slice(4).trim();
      const splitted = doc.splitTextToSize(text, contentWidth);
      for (const line of splitted) {
        checkPageBreak(5);
        doc.text(line, marginLeft, cursorY);
        cursorY += 5;
      }
      cursorY += 1.5;
    } else if (trimmed.startsWith('---')) {
      // Divider
      checkPageBreak(6);
      doc.setDrawColor(226, 232, 240);
      doc.setLineWidth(0.3);
      doc.line(marginLeft, cursorY, marginLeft + contentWidth, cursorY);
      cursorY += 5;
    } else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
      // Bullet list item
      const itemRaw = trimmed.slice(2).trim();

      // Clean markdown tags for PDF rendering
      const cleanItem = itemRaw
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/\*(.+?)\*/g, '$1');

      doc.setFontSize(9.5);
      const bulletIndent = 6;
      const bulletWidth = contentWidth - bulletIndent;
      const splitted = doc.splitTextToSize(cleanItem, bulletWidth);

      for (let j = 0; j < splitted.length; j++) {
        checkPageBreak(5);
        if (j === 0) {
          doc.setFont('helvetica', 'bold');
          doc.setTextColor(99, 102, 241);
          doc.text('•', marginLeft + 1.5, cursorY);
        }

        // Highlight conflict prefix if present
        if (cleanItem.startsWith('CONFLICT:')) {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(185, 28, 28); // red-700
        } else if (cleanItem.startsWith('AGREE:')) {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(21, 128, 61); // green-700
        } else {
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(51, 65, 85);
        }

        doc.text(splitted[j], marginLeft + bulletIndent, cursorY);
        cursorY += 4.5;
      }
      cursorY += 1.5;
    } else {
      // Normal paragraph
      const cleanPara = trimmed
        .replace(/\*\*(.+?)\*\*/g, '$1')
        .replace(/\*(.+?)\*/g, '$1');

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9.5);
      doc.setTextColor(51, 65, 85);
      const splitted = doc.splitTextToSize(cleanPara, contentWidth);
      for (const line of splitted) {
        checkPageBreak(5);
        doc.text(line, marginLeft, cursorY);
        cursorY += 4.5;
      }
      cursorY += 2;
    }
  }

  // Running headers and footers across all pages
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);

    // Header on pages > 1
    if (i > 1) {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(148, 163, 184);
      doc.text('Agentic Literature Review', marginLeft, 10);
      doc.text(now, pageWidth - marginRight, 10, { align: 'right' });
      doc.setDrawColor(241, 245, 249);
      doc.setLineWidth(0.2);
      doc.line(marginLeft, 12, pageWidth - marginRight, 12);
    }

    // Footer on all pages
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(148, 163, 184);
    doc.text(
      'Grounded in empirical PDF citations • Verified by AI Pipeline',
      marginLeft,
      pageHeight - 10
    );
    doc.text(
      `Page ${i} of ${totalPages}`,
      pageWidth - marginRight,
      pageHeight - 10,
      { align: 'right' }
    );
  }

  doc.save(filename);
}

/**
 * Trigger native browser print dialog
 */
export function printReport(): void {
  window.print();
}

/* =========================================================================
 * Internal Helpers for parsing markdown into DOCX TextRuns / HTML elements
 * ========================================================================= */

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function parseInlineHtml(text: string): string {
  let escaped = escapeHtml(text);

  // Bold **text**
  escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Italics *text*
  escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Conflict highlights
  escaped = escaped.replace(
    /\b(conflict|contradiction)s?\b/gi,
    '<span class="conflict-badge">$&</span>'
  );

  // Agree highlights
  escaped = escaped.replace(
    /\b(agree|consensus)s?\b/gi,
    '<span class="agree-badge">$&</span>'
  );

  // Citations like (Author et al., 2024, p. 5)
  escaped = escaped.replace(
    /\([A-Za-z\s]+et\sal\.,?\s\d{4}(?:,\sp\.\s\d+)?\)/g,
    '<span class="citation">$&</span>'
  );

  return escaped;
}

function parseInlineDocx(text: string): TextRun[] {
  // Regex to split on bold tokens **...**
  const parts = text.split(/(\*\*.*?\*\*)/g);
  const runs: TextRun[] = [];

  for (const part of parts) {
    if (!part) continue;

    if (part.startsWith('**') && part.endsWith('**')) {
      const boldContent = part.slice(2, -2);
      const isConflict = /conflict|contradiction/i.test(boldContent);
      const isAgree = /agree/i.test(boldContent);

      runs.push(
        new TextRun({
          text: boldContent,
          bold: true,
          color: isConflict ? 'DC2626' : isAgree ? '16A34A' : '0F172A',
        })
      );
    } else {
      // Check for inline citations like (Author et al., 2024, p. 5)
      const subParts = part.split(/(\([A-Za-z\s]+(?:et\sal\.)?,?\s\d{4}(?:,\sp\.\s\d+)?\))/g);
      for (const sub of subParts) {
        if (!sub) continue;
        if (/^\([A-Za-z\s]+(?:et\sal\.)?,?\s\d{4}(?:,\sp\.\s\d+)?\)$/.test(sub)) {
          runs.push(
            new TextRun({
              text: sub,
              font: 'Consolas',
              size: 19, // 9.5pt
              color: '4338CA', // Indigo
            })
          );
        } else {
          runs.push(
            new TextRun({
              text: sub,
              color: '334155',
            })
          );
        }
      }
    }
  }

  return runs;
}
