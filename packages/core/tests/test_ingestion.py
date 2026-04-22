import plistlib
import zipfile
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
    assert detect_source_type(Path("spreadsheet.xlsx")) == "spreadsheet"
    assert detect_source_type(Path("saved.html")) == "html"
    assert detect_source_type(Path("saved.htm")) == "html"
    assert detect_source_type(Path("saved.webarchive")) == "web-archive"
    assert detect_source_type(Path("saved.mhtml")) == "web-archive"


def _write_minimal_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="/xl/workbook.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Signals" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="/xl/worksheets/sheet1.xml"/>
</Relationships>
""",
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>Overview</t></is></c>
      <c r="B1" t="inlineStr"><is><t>Taiwan Strait warning</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>Details</t></is></c>
      <c r="B2" t="inlineStr"><is><t>Chief executive response</t></is></c>
    </row>
  </sheetData>
</worksheet>
""",
        )


def test_markdown_ingestion_uses_heading_locations(tmp_path: Path) -> None:
    path = tmp_path / "brief.md"
    path.write_text("# Overview\nAlpha\n\n## Constraints\nBeta\n", encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "markdown"
    assert [chunk.location for chunk in document.chunks] == [
        "heading:Overview",
        "heading:Overview > Constraints",
    ]


def test_xlsx_ingestion_uses_sheet_and_cell_ranges(tmp_path: Path) -> None:
    path = tmp_path / "signals.xlsx"
    _write_minimal_xlsx(path)

    document = ingest_file(path)

    assert document.source_type == "spreadsheet"
    assert [chunk.location for chunk in document.chunks] == [
        "sheet:Signals!A1:B1",
        "sheet:Signals!A2:B2",
    ]
    assert "Taiwan Strait warning" in document.chunks[0].content


def test_html_ingestion_preserves_metadata_and_heading_locations(tmp_path: Path) -> None:
    path = tmp_path / "saved.html"
    path.write_text(
        """<!doctype html>
<html>
  <head>
    <title>Saved Page</title>
    <meta property="article:published_time" content="2026-04-20">
  </head>
  <body>
    <h1>Overview</h1>
    <p>The chief executive stabilized messaging quickly.</p>
  </body>
</html>
""",
        encoding="utf-8",
    )

    document = ingest_file(path)

    assert document.source_type == "html"
    assert document.title == "Saved Page"
    assert document.published_at == "2026-04-20"
    assert [chunk.location for chunk in document.chunks] == ["heading:Overview > paragraph:1"]
    assert "chief executive" in document.chunks[0].content


def test_html_ingestion_handles_cp1252_encoded_pages(tmp_path: Path) -> None:
    path = tmp_path / "legacy.html"
    path.write_bytes(
        b"""<!doctype html>
<html>
  <head>
    <title>Legacy Page</title>
  </head>
  <body>
    <p>caf\xe9</p>
  </body>
</html>
"""
    )

    document = ingest_file(path)

    assert document.source_type == "html"
    assert document.chunks[0].content == "café"


def test_html_ingestion_accepts_heading_only_pages(tmp_path: Path) -> None:
    path = tmp_path / "heading-only.html"
    path.write_text("<html><body><h1>Headline only</h1></body></html>", encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "html"
    assert [chunk.location for chunk in document.chunks] == ["heading:Headline only"]
    assert document.chunks[0].content == "Headline only"


def test_html_ingestion_preserves_multiple_heading_only_headings(tmp_path: Path) -> None:
    path = tmp_path / "outline.html"
    path.write_text("<html><body><h1>Alpha</h1><h2>Beta</h2><h2>Gamma</h2></body></html>", encoding="utf-8")

    document = ingest_file(path)

    assert document.source_type == "html"
    assert [chunk.location for chunk in document.chunks] == [
        "heading:Alpha",
        "heading:Alpha > Beta",
        "heading:Alpha > Gamma",
    ]
    assert [chunk.content for chunk in document.chunks] == ["Alpha", "Beta", "Gamma"]


def test_web_archive_ingestion_uses_saved_page_metadata_and_chunk_locations(tmp_path: Path) -> None:
    path = tmp_path / "saved.webarchive"
    archive_html = """<!doctype html>
<html>
  <head>
    <title>Archived Page</title>
    <meta name="published_time" content="2026-04-19">
  </head>
  <body>
    <h1>Signals</h1>
    <p>Chief executive response stabilized quickly.</p>
  </body>
</html>
"""
    plistlib.dump(
        {
            "WebMainResource": {
                "WebResourceData": archive_html.encode("utf-8"),
                "WebResourceMIMEType": "text/html",
                "WebResourceTextEncodingName": "utf-8",
                "WebResourceURL": "https://example.com/archived-page",
            }
        },
        path.open("wb"),
    )

    document = ingest_file(path)

    assert document.source_type == "web-archive"
    assert document.title == "Archived Page"
    assert document.published_at == "2026-04-19"
    assert [chunk.location for chunk in document.chunks] == ["heading:Signals > paragraph:1"]
    assert "Chief executive response" in document.chunks[0].content


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
