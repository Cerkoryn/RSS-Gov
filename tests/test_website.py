import json
import math
import re
import shutil
import subprocess

import numpy as np
import pytest

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


def test_a_design_close_to_a_named_one_is_named_after_it():
    from rss_gov import mechanisms, proposals

    base = {
        name: {**mechanisms.PRESETS[name], "budget_ada": 5e6} for name in ("middle_out", "capped")
    }
    schemes = {name: mechanisms.scheme(name=name, **rule) for name, rule in base.items()}
    near = {**base["middle_out"], "k_exclude": 20, "budget_ada": 1e6}
    far = {**near, "min_delegators": 50}
    schemes["g1_1"] = mechanisms.scheme(name="g1_1", **near)
    schemes["g1_2"] = mechanisms.scheme(name="g1_2", **far)
    family = website.lineage(schemes, ["middle_out", "capped"])
    assert family == {"g1_1": ("middle_out", ["budget_ada", "k_exclude"])}
    assert [proposals.tag(f, near[f]) for f in family["g1_1"][1]] == ["1M ADA", "skip 20"]
    assert proposals.tag("cap_ada", None) == "no cap"
    assert proposals.tag("roll_down", False) == "no roll-down"
    assert proposals.tag("min_share", 0.005) == "≥0.5% of power"
    assert proposals.tag("budget_ada", 0) == "no budget"
    assert proposals.tag("fee_ada", 25_000) == "25k ADA per action"
    assert all(f["short"] and f["tag"] for f in proposals.FIELDS)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js")
def test_the_browser_tags_settings_like_python():
    from rss_gov import proposals

    source = (website.WEB / "common.js").read_text()
    functions = re.search(r"^const minus = .*$", source, re.M).group(0) + "\n"
    functions += "\n".join(
        re.search(rf"^function {name}\(.*?^}}$", source, re.S | re.M).group(0)
        for name in ("num", "tag")
    )
    cases = [
        ("cap_ada", None), ("alpha", 0.0), ("alpha", 0.5), ("budget_ada", 1e6),
        ("budget_ada", 2.5e6), ("min_share", 0.005), ("pledge_leverage", 10000.0),
        ("roll_down", False), ("roll_down", True), ("min_delegators", 50), ("n_pay", 1200),
        ("activity_gate", 0.7), ("basis", "delegators"), ("per_vote_ada", 10.0),
        ("min_stake_ada", 10000.0), ("delegator_mode", "flat"), ("rationale_bonus", 1.0),
        ("fee_ada", 25000.0), ("fee_ada", 0.0), ("budget_ada", 0.0),
    ]  # fmt: skip
    script = (
        f"{functions}\nconst F = {json.dumps(proposals.BY_NAME)};"
        f"console.log(JSON.stringify({json.dumps(cases)}.map(([k, v]) => tag(F[k], v))));"
    )
    out = json.loads(subprocess.run(["node", "-e", script], capture_output=True, check=True).stdout)
    assert out == [proposals.tag(k, v) for k, v in cases]


def test_designs_link_to_where_their_idea_comes_from():
    from rss_gov import mechanisms

    named = mechanisms.preset("middle_out", 5e6)
    assert website.references("middle_out", named)[0]["url"].endswith(
        "ExcludeKPayN/blob/main/paper.md"
    )
    fee = mechanisms.from_config(dict(preset="capped", budget_ada=0, fee_ada=5e4), 5e6)
    titles = [r["title"] for r in website.references("capped_fee_50k", fee, "capped")]
    assert titles == [website._CIP1117[0], website._FEE[0]]
    pledge = mechanisms.preset("pledge_soft", 5e6)
    assert website.references("pledge_soft_1m", pledge, "pledge_soft") == website.references(
        "pledge_soft", pledge
    )
    assert website.references("g1_2", named) == []
    assert all(
        r[1].startswith(("https://", "methods.html#"))
        for v in website.REFERENCES.values()
        for r in v
    )


def test_every_diagram_in_the_methods_page_exists(tmp_path):
    source = (website.WEB.parents[2] / "METHODS.md").read_text()
    names = website.FIGURE.findall(source)
    assert names and all((website.WEB / "figures" / f"{n}.svg").exists() for n in names)
    page = tmp_path / "METHODS.md"
    page.write_text(f"# M\n\nText.\n\n<!--FIGURE:{names[0]}-->\n\n*Caption.*\n")
    body = website.methods(page)[1]
    assert '<figure class="diagram"><svg' in body and "<!--FIGURE" not in body
