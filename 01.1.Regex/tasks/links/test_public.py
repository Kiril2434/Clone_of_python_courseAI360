import re

from links import RE_A_HREF, f_link


def extract_links(s, regexp, f_repr):
    return [f_repr(m) for m in re.finditer(regexp, s)]


def test_empty():
    links = extract_links("", RE_A_HREF, None)
    assert links == []


def test_blank():
    for i in range(1, 20):
        s = i * " "
        links = extract_links(s, RE_A_HREF, None)
        assert links == []


def test_just_angles():
    for i in range(1, 20):
        s = "<" + i * " " + ">"
        links = extract_links(s, RE_A_HREF, None)
        assert links == []


def test_a_and_angles():
    for i in range(1, 20):
        for c in "aA":
            s = "<{c}" + i * " " + ">"
            links = extract_links(s, RE_A_HREF, None)
            assert links == []


def test_a_href_no_quotes():
    s = "<a href=https://ya.ru />"
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_a_other_attr_no_quotes():
    s = "<a abc=https://ya.ru />"
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == []


def test_a_href_with_quotes():
    s = '<a href="https://ya.ru" />'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_a_two_href_other_attr():
    s = '<a href="https://ya.ru" abc=https://abc.ru/>'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_a_two_href_other_attr_rev():
    s = '<a abc=https://abc.ru/ href="https://ya.ru" />'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_double_href():
    s = '<a href=https://abc.ru/ href="https://ya.ru" />'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_double_href_no_space_right():
    s = '<a href=https://abc.ru/ href="https://ya.ru"/>'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_double_href_no_space_right_no_quotes():
    s = "<a href=https://abc.ru/ href=https://ya.ru/>"
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_double_tag():
    s = "<a href=https://abc.ru /><a href=https://ya.ru/>"
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://abc.ru", "https://ya.ru"]


def test_double_tag_empty_value():
    s = '<a href=https://abc.ru /><a href="">'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://abc.ru"]


def test_double_tag_no_close_quote():
    s = '<a href="https://abc.ru /><a href=https://ya.ru/>'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == ["https://ya.ru"]


def test_misc_chars():
    for c in "#@!$%^&*()[]":
        s = f'<a href="https://abc.ru{c}" />'
    links = extract_links(s, RE_A_HREF, f_link)
    assert links == [f"https://abc.ru{c}"]


def test_misc_case():
    for attr in ("href", "HREF", "hReF", "HRef")[:1]:
        for c in "#@!$%^&*()[]":
            s = f'<a {attr}="https://abc.ru{c}" />'
            links = extract_links(s, RE_A_HREF, f_link)
            assert links == [f"https://abc.ru{c}"]
