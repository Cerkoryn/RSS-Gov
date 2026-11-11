import math
import re

import numpy as np

from rss_gov import website


def test_every_page_and_asset_ships_with_the_package():
    for name in [*website.PAGES, "methods.html"]:
        assert (website.WEB / name).exists(), name
    page = (website.WEB / "methods.html").read_text()
    assert all(page.count(mark) == 1 for mark in ("<!--TOC-->", "<!--METHODS-->", "<!--EDIT-->"))


def test_pages_load_only_local_files():
    for name in ("index.html", "methods.html", "propose.html"):
        page = (website.WEB / name).read_text()
        sources = re.findall(r'(?:src|href)="([^"#]+)"', page)
        assert sources and all("//" not in s for s in sources), (name, sources)


def test_values_become_plain_json():
    out = website._plain(
        {"a": np.float64(0.123456789), "b": math.nan, "c": [np.int64(3), np.bool_(True)], 4: None}
    )
    assert out == {"a": 0.123457, "b": None, "c": [3, True], "4": None}


def test_methods_page_renders_tables_and_contents(tmp_path):
    source = tmp_path / "METHODS.md"
    source.write_text(
        "# Methods\n\n## The axes\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n### Detail\n\nText.\n"
    )
    toc, body = website.methods(source)
    assert 'href="#the-axes"' in toc and 'href="#detail"' in toc
    assert '<div class="tablewrap"><table>' in body and "<td>2</td>" in body


def test_generated_designs_get_short_distinct_names():
    from rss_gov import mechanisms

    schemes = {
        "g1_1": mechanisms.scheme(alpha=1.0, delegator_share=0.5, cap_ada=2e6, budget_ada=1e7),
        "g1_2": mechanisms.scheme(
            alpha=1.0, delegator_share=0.5, cap_ada=2e6, pledge_leverage=100, budget_ada=1e7
        ),
        "g1_3": mechanisms.scheme(alpha=0.0, k_exclude=20, n_pay=400, budget_ada=1e6),
    }
    names = website.titles(schemes)
    assert names["g1_1"] == "Proportional, half to delegators, 10M ADA"
    assert names["g1_2"] == "Proportional, half to delegators, ≤100× own stake, 10M ADA"
    assert names["g1_3"] == "Equal, ranks 21–420, 1M ADA"
    assert len(set(names.values())) == len(names)
