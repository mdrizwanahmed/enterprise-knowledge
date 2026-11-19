import pytest
from app.chunking import split_text

def test_empty_text():
    assert split_text("  ") == []

def test_short_text():
    assert split_text("hello world", 20, 3) == ["hello world"]

def test_long_text_splits():
    text = " ".join(f"word{i}" for i in range(100))
    chunks = split_text(text, 80, 15)
    assert len(chunks) > 1
    assert all(chunks)
    assert all(len(c) <= 80 for c in chunks)

def test_invalid_overlap():
    with pytest.raises(ValueError):
        split_text("hello", 10, 10)
