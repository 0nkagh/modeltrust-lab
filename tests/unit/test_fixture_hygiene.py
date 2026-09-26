import pytest
import re
from pathlib import Path

def test_fixture_hygiene():
    fixtures_dir = Path("tests/fixtures")
    readme = fixtures_dir / "README.md"
    
    assert readme.exists()
    readme_content = readme.read_text(encoding="utf-8")
    
    for p in fixtures_dir.iterdir():
        if not p.is_file() or p.name == "README.md" or p.name.startswith("."):
            continue
            
        assert p.name in readme_content, f"Fixture {p.name} not documented in tests/fixtures/README.md"
        
        raw_bytes = p.read_bytes()
        
        if p.name == "turkish_bom_semicolon.csv":
            assert raw_bytes.startswith(b"\xef\xbb\xbf")
            assert "BOM" in readme_content
            # Check for LF
            text_no_bom = raw_bytes[3:]
            assert b"\r\n" not in text_no_bom, f"Fixture {p.name} contains CRLF"
            # check valid utf8
            text_no_bom.decode("utf-8")
        else:
            assert not raw_bytes.startswith(b"\xef\xbb\xbf"), f"Fixture {p.name} has unexpected BOM"
            assert b"\r\n" not in raw_bytes, f"Fixture {p.name} contains CRLF"
            raw_bytes.decode("utf-8")
