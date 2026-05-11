import importlib.util
import sys
import types
from pathlib import Path


def load_sort_table(monkeypatch):
    fake_requests = types.SimpleNamespace(
        exceptions=types.SimpleNamespace(RequestException=Exception)
    )
    monkeypatch.setitem(sys.modules, "requests", fake_requests)
    module_path = Path(__file__).resolve().parents[1] / "sort_table.py"
    spec = importlib.util.spec_from_file_location("sort_table", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_markdown():
    return (
        "Intro text\n"
        "|<ins>#</ins>|Repo|Repo_Stars|Category|Notes|\n"
        "|---|---|---|---|---|\n"
        "|1|[Low](https://github.com/org/low)|"
        '<img src="https://custom-icon-badges.herokuapp.com/github/stars/org/low?style=social">|Tools|a|\n'
        "|2|[High](https://github.com/org/high)|"
        '<img src="https://custom-icon-badges.herokuapp.com/github/stars/org/high?style=social">|Tools|b|\n'
        "\n"
        "## Next section\n"
        "Tail text\n"
    )


def test_sort_markdown_table_sorts_rows_by_fetched_stars(monkeypatch):
    sort_table = load_sort_table(monkeypatch)
    monkeypatch.setattr(sort_table.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        sort_table,
        "get_github_stars",
        lambda slug: {"org/low": 10, "org/high": 50}[slug],
    )

    updated = sort_table.sort_markdown_table(sample_markdown())

    assert "|1|[High](https://github.com/org/high)|" in updated
    assert "|2|[Low](https://github.com/org/low)|" in updated
    assert updated.index("[High]") < updated.index("[Low]")
    assert "Intro text\n|<ins>#</ins>|Repo|Repo_Stars|Category|Notes|" in updated
    assert "## Next section\nTail text" in updated


def test_sort_markdown_table_uses_repo_link_when_badge_slug_is_missing(monkeypatch):
    sort_table = load_sort_table(monkeypatch)
    monkeypatch.setattr(sort_table.time, "sleep", lambda seconds: None)
    seen = []

    def fake_stars(slug):
        seen.append(slug)
        return {"org/fallback-high": 99, "org/fallback-low": 1}[slug]

    monkeypatch.setattr(sort_table, "get_github_stars", fake_stars)
    markdown = (
        "|<ins>#</ins>|Repo|Repo_Stars|Category|Notes|\n"
        "|---|---|---|---|---|\n"
        "|1|[Fallback Low](https://github.com/org/fallback-low)|stars unavailable|Tools|a|\n"
        "|2|[Fallback High](https://github.com/org/fallback-high)|stars unavailable|Tools|b|\n"
    )

    updated = sort_table.sort_markdown_table(markdown)

    assert seen == ["org/fallback-low", "org/fallback-high"]
    assert updated.index("Fallback High") < updated.index("Fallback Low")


def test_sort_markdown_table_returns_original_when_table_is_missing(monkeypatch, capsys):
    sort_table = load_sort_table(monkeypatch)
    markdown = "No ranking table here."

    assert sort_table.sort_markdown_table(markdown) == markdown

    out = capsys.readouterr().out
    assert "Table header or separator not found." in out


def test_sort_markdown_table_skips_malformed_rows(monkeypatch, capsys):
    sort_table = load_sort_table(monkeypatch)
    monkeypatch.setattr(sort_table.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(sort_table, "get_github_stars", lambda slug: 5)
    markdown = (
        "|<ins>#</ins>|Repo|Repo_Stars|Category|Notes|\n"
        "|---|---|---|---|---|\n"
        "not enough columns\n"
        "|1|[Valid](https://github.com/org/valid)|stars unavailable|Tools|a|\n"
    )

    updated = sort_table.sort_markdown_table(markdown)

    assert "not enough columns" not in updated
    assert "[Valid]" in updated
    assert "Skipping malformed row" in capsys.readouterr().out


def test_main_rewrites_file_with_sorted_table(monkeypatch, tmp_path):
    sort_table = load_sort_table(monkeypatch)
    monkeypatch.setattr(sort_table.time, "sleep", lambda seconds: None)
    monkeypatch.setattr(
        sort_table,
        "get_github_stars",
        lambda slug: {"org/low": 10, "org/high": 50}[slug],
    )
    readme = tmp_path / "README.md"
    readme.write_text(sample_markdown(), encoding="utf-8")

    assert sort_table.main(str(readme)) is None

    updated = readme.read_text(encoding="utf-8")
    assert updated.index("[High]") < updated.index("[Low]")
