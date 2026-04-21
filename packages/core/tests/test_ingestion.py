from pathlib import Path

import pytest

from forecasting_harness.retrieval.ingest import detect_source_type, ingest_file


SIMPLE_TEXT_PDF = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Count 1 /Kids [3 0 R] >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 54 >>
stream
BT
/F1 18 Tf
72 96 Td
(Taiwan Strait warning) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000241 00000 n 
0000000345 00000 n 
trailer
<< /Root 1 0 R /Size 6 >>
startxref
415
%%EOF
"""


def test_detect_source_type_maps_supported_suffixes() -> None:
    assert detect_source_type(Path("notes.md")) == "markdown"
    assert detect_source_type(Path("notes.txt")) == "markdown"
    assert detect_source_type(Path("table.csv")) == "csv"
    assert detect_source_type(Path("facts.json")) == "json"
    assert detect_source_type(Path("report.pdf")) == "pdf"


def test_markdown_ingestion_uses_heading_locations(tmp_path: Path) -> None:
    path = tmp_path / "brief.md"
    path.write_text("# Overview\nAlpha\n\n## Constraints\nBeta\n", encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "markdown"
    assert [chunk.location for chunk in document.chunks] == [
        "heading:Overview",
        "heading:Overview > Constraints",
    ]


def test_csv_ingestion_uses_row_locations(tmp_path: Path) -> None:
    path = tmp_path / "table.csv"
    path.write_text("country,posture\nJapan,heightened\nChina,signaling\n", encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "csv"
    assert [chunk.location for chunk in document.chunks] == ["row:1", "row:2"]
    assert document.chunks[0].content == "country=Japan, posture=heightened"


def test_json_ingestion_uses_structural_locations(tmp_path: Path) -> None:
    path = tmp_path / "facts.json"
    path.write_text('{"constraints": ["sanctions"], "actors": ["Japan", "China"]}', encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "json"
    assert [chunk.location for chunk in document.chunks] == ["key:actors", "key:constraints"]


def test_pdf_ingestion_uses_page_locations(tmp_path: Path) -> None:
    path = tmp_path / "report.pdf"
    path.write_bytes(SIMPLE_TEXT_PDF)

    document = ingest_file(path)

    assert document.source_type == "pdf"
    assert [chunk.location for chunk in document.chunks] == ["page:1"]
    assert "Taiwan Strait warning" in document.chunks[0].content


def test_detect_source_type_rejects_unsupported_suffixes() -> None:
    with pytest.raises(ValueError, match="unsupported source type"):
        detect_source_type(Path("archive.zip"))
