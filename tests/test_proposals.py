import pytest
import yaml

from rss_gov import proposals

VALID = dict(
    name="My Idea!", budget_ada=2_500_000, alpha=0.5, cap_ada=None, hypothesis="why", author="me"
)


def test_a_valid_proposal_becomes_a_scheme():
    scheme, meta = proposals.parse(VALID)
    assert scheme.name == "my_idea"
    assert scheme.budget_ada == 2_500_000 and scheme.alpha == 0.5 and scheme.paid
    assert meta == {"hypothesis": "why", "author": "me"}


@pytest.mark.parametrize(
    "change, message",
    [
        (dict(budget_ada=1e12), "between"),
        (dict(alpha="0.5"), "number"),
        (dict(alpha=float("nan")), "between"),
        (dict(min_delegators=2.5), "whole"),
        (dict(hard_cap=1), "true or false"),
        (dict(delegator_mode="weird"), "one of"),
        (dict(surprise=1), "unknown fields"),
        (dict(hard_cap=True, pledge_leverage=0.0), "pledge_leverage"),
        (dict(author="x" * 81), "longer than"),
    ],
)
def test_bad_values_are_refused_with_a_reason(change, message):
    with pytest.raises(ValueError, match=message):
        proposals.parse({**VALID, **change})


def test_a_budget_is_required():
    with pytest.raises(ValueError, match="budget_ada"):
        proposals.parse({"name": "x"})


def test_names_are_safe_and_never_collide_with_existing_designs():
    assert proposals.slug("../../etc/passwd") == "etc_passwd"
    assert proposals.slug("g3_7") == "p_g3_7"  # looks like a search design
    assert proposals.slug("proportional") == "p_proportional"  # a named scheme
    assert proposals.slug("42 ideas") == "p_42_ideas"
    assert proposals.slug("") == "proposal"
    scheme, _ = proposals.parse(VALID, taken={"my_idea", "my_idea_2"})
    assert scheme.name == "my_idea_3"


def test_control_characters_are_dropped_from_text():
    _, meta = proposals.parse({**VALID, "hypothesis": "line one\nline\x07 two\x00"})
    assert meta["hypothesis"] == "line one\nline two"


def test_a_stored_submission_is_a_valid_try_input(tmp_path):
    scheme, meta = proposals.parse(VALID)
    path = proposals.submit(tmp_path, scheme, meta, "web")
    rows = yaml.safe_load(path.read_text())
    row, kept = proposals.split(rows[0])
    assert row == scheme.to_dict()
    assert kept["hypothesis"] == "why" and kept["source"] == "web"
    listing = proposals.listing(tmp_path)
    assert [(p["name"], p["state"]) for p in listing] == [("my_idea", "queued")]
    assert listing[0]["rule"] == scheme.label()


def test_a_recorded_result_is_listed_as_done(tmp_path):
    (tmp_path / "calibration.json").write_text("{}")
    scheme, meta = proposals.parse(VALID)
    proposals.submit(tmp_path, scheme, meta, "web")
    proposals.record(tmp_path, scheme, dict(accepted=False, reason="no clear gain"), None, meta)
    (row,) = proposals.listing(tmp_path)
    assert row["state"] == "done" and row["reason"] == "no clear gain"
    (tmp_path / "calibration.json").write_text('{"changed": true}')
    assert proposals.listing(tmp_path)[0]["state"] == "stale"
