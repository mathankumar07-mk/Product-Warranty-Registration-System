"""Minimal dependency-free PDF invoice renderer (stdlib only).

Builds a valid single-page PDF 1.4 using Helvetica so invoice downloads are
real PDF files without extra packages (pip is unavailable in some envs).
"""

from __future__ import annotations


def _escape(text: str) -> str:
    cleaned = text.encode("latin-1", errors="replace").decode("latin-1")
    return cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def render_invoice_pdf(title_lines: list[str], item_lines: list[str], total_lines: list[str]) -> bytes:
    lines = [*title_lines, "", *item_lines, "", *total_lines][:60]
    ops = ["BT /F1 12 Tf 50 770 Td"]
    for i, line in enumerate(lines):
        if i:
            ops.append("0 -18 Td")
        ops.append(f"({_escape(line)}) Tj")
    ops.append("ET")
    content = "\n".join(ops).encode("latin-1")

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF".encode()
    )
    return bytes(out)
