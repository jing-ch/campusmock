"""
Integration tests for cv_parser.py — requires a real ANTHROPIC_API_KEY.

Run with:
    pytest tests/test_cv_parser.py -v -m integration
"""
import pytest
from pathlib import Path

from cv_parser import _pdf_to_png_bytes, _parse_png, parse_cv

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.integration
@pytest.mark.parametrize("filename", ["resume1.pdf", "resume2.pdf"])
def test_cv_parse_pipeline(filename):
    pdf_bytes = (FIXTURES / filename).read_bytes()

    # 1. PDF → PNG
    png_bytes = _pdf_to_png_bytes(pdf_bytes)
    assert png_bytes is not None
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # valid PNG header

    # 2. PNG → Claude → non-empty JSON
    result = _parse_png(png_bytes)
    print(f"\n{filename} → {result}")
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) > 0
