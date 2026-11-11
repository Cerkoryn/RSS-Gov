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


ISSUE = """### Hypothesis

Paying the middle ranks should spread power.

### Rule

```yaml
- name: "middle ranks"
  author: ""
  budget_ada: 2500000
  alpha: 0.5
  k_exclude: 20
```
"""


def test_a_github_issue_body_becomes_a_submission():
    row = proposals.from_text(ISSUE)
    assert row["hypothesis"] == "Paying the middle ranks should spread power."
    scheme, meta = proposals.parse(row)
    assert scheme.name == "middle_ranks" and scheme.k_exclude == 20
    assert proposals.from_text("budget_ada: 1000000\n")["budget_ada"] == 1_000_000
    empty = ISSUE.replace("Paying the middle ranks should spread power.", "_No response_")
    assert "hypothesis" not in proposals.from_text(empty)
    for text in ("just words", "```yaml\n- a\n- b\n```"):
        with pytest.raises(ValueError, match="one proposal"):
            proposals.from_text(text)


def test_accept_refuses_a_rule_that_is_already_listed(tmp_path):
    config = dict(
        results=str(tmp_path),
        programme=dict(budget_ada=5_000_000),
        experiment=dict(schemes=["proportional"]),
        search=dict(allow_hard_fork=False),
    )
    with pytest.raises(ValueError, match="already listed as proportional"):
        proposals.accept(config, dict(name="copy", budget_ada=5_000_000, alpha=1.0))
    with pytest.raises(ValueError, match="hard-fork"):
        proposals.accept(config, {**VALID, "pledge_leverage": 10, "hard_cap": True})
    scheme, _ = proposals.accept(config, VALID)
    proposals.submit(tmp_path, scheme, {}, "issue #1")
    with pytest.raises(ValueError, match="already listed as my_idea"):
        proposals.accept(config, {**VALID, "name": "again"})
