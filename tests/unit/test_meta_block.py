import pytest

from clutch.meta import Malformed, digest, parse


@pytest.mark.parametrize(
    "suffix,block",
    [
        (".md", "<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: doc\npurpose: hello\nrelates: []\nowner: engine\nverified: abcdef12\nhash: abc\n-->\n"),
        (".py", "# clutch:meta\n# schema: clutch.meta/1.0\n# kind: test\n# purpose: hello\n# relates: []\n# owner: engine\n# verified: abcdef12\n# hash: abc\n"),
    ],
)
def test_parse_and_hash(suffix, block):
    fields, body, _ = parse(block + "body\n", suffix)
    assert fields["schema"] == "clutch.meta/1.0"
    assert set(fields) == {"schema", "kind", "purpose", "relates", "owner", "verified", "hash"}
    assert digest(body) == digest("body\n")
    assert digest(parse(block.replace("hello", "different") + "body\n", suffix)[1]) == digest(body)
    assert digest(body + "changed") != digest(body)


def test_extra_markdown_key_is_malformed():
    with pytest.raises(Malformed):
        parse("<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: doc\npurpose: x\nrelates: []\nowner: engine\nverified: a\nhash: b\nextra: c\n-->\n", ".md")


@pytest.mark.parametrize(
    "text,suffix",
    [
        ("<!-- clutch:meta\nno end", ".md"),
        ("# clutch:meta\n# schema: clutch.meta/1.0\n", ".py"),
        ("<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: doc\npurpose: x\nrelates: []\nowner: engine\nverified: a\nextra: b\n-->\n", ".md"),
        ("<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: wrong\npurpose: x\nrelates: []\nowner: engine\nverified: a\nhash: b\n-->\n", ".md"),
        ("<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: doc\npurpose: x\nrelates: [\nowner: engine\nverified: a\nhash: b\n-->\n", ".md"),
        ("<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: doc\npurpose: x\nrelates: text\nowner: engine\nverified: a\nhash: b\n-->\n", ".md"),
    ],
)
def test_malformed_blocks(text, suffix):
    with pytest.raises(Malformed):
        parse(text, suffix)
