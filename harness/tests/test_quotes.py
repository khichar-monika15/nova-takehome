from audit.quotes import line_with, locate

PAGES = ["Header line\n1 TE56915687 2031-12-25 Air freight USE2-INE2 241 kg 6.69 1612.29\nTotal USD 1937.33",
         "AWB | Event | Date\nTE56915687 | PICKED_UP | 2031-12-25 | USE2 | -"]


def test_locate_exact_quote_on_cited_page():
    assert locate(PAGES, 1, "Air freight USE2-INE2 241 kg") == (1, "Air freight USE2-INE2 241 kg")


def test_locate_moves_to_the_right_page():
    assert locate(PAGES, 1, "TE56915687 | PICKED_UP | 2031-12-25") == (2, "TE56915687 | PICKED_UP | 2031-12-25")


def test_locate_repairs_small_differences_to_exact_page_text():
    page, quote = locate(PAGES, 1, "1 TE56915687 2031-12-25 Air  freight USE2-INE2 241kg 6.69 1612.29")
    assert page == 1
    assert quote == "1 TE56915687 2031-12-25 Air freight USE2-INE2 241 kg 6.69 1612.29"


def test_locate_gives_none_for_text_that_is_not_there():
    assert locate(PAGES, 1, "Completely different sentence about cargo") is None


def test_line_with_finds_the_row_holding_every_needle():
    assert line_with(PAGES, "TE56915687", "PICKED_UP") == (2, "TE56915687 | PICKED_UP | 2031-12-25 | USE2 | -")
