"""The AI research loop, `rss-gov research`: an agent proposes designs, the evaluator judges.

Nothing else starts it: not `rss-gov all`, not any workflow. Each round runs the agent
command in `config.yaml` (`research.agent`) with `program.md` as its instructions. The
agent proposes designs and tests them with `rss-gov try --source agent`, so they are
judged exactly like the search's own designs, on the holdout seeds (`rss-gov try`
replaces them once they are used up). Accepted designs join the search's finalists and
are shown with them; every attempt is in results/ledger.jsonl.
"""

import os
from pathlib import Path
import subprocess

from rss_gov import proposals, search


def run(study, rounds, log=print, processes=None):
    config = study.config.get("research") or {}
    if not config.get("agent"):
        raise ValueError("no agent command: set research.agent in config.yaml")
    program = Path(config.get("program", "program.md")).read_text()
    env = {**os.environ, "RSS_GOV_SOURCE": proposals.AGENT}
    for k in range(1, rounds + 1):
        prompt = (
            f"{program}\n\nThis is round {k} of {rounds}. Test your designs with "
            "`rss-gov try --source agent candidates.yaml`."
        )
        command = [str(part).replace("{prompt}", prompt) for part in config["agent"]]
        if prompt not in command:
            command.append(prompt)
        before = len(search.ledger(study.results))
        log(f"round {k} of {rounds}")
        done = subprocess.run(command, env=env)
        tried = [
            e for e in search.ledger(study.results)[before:] if e.get("source") == proposals.AGENT
        ]
        accepted = [e["scheme"]["name"] for e in tried if e.get("accepted")]
        log(f"  {len(tried)} designs tried, accepted: {', '.join(accepted) or 'none'}")
        if done.returncode:
            raise RuntimeError(f"the agent stopped with exit code {done.returncode}")
