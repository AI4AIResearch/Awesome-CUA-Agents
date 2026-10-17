import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = [ROOT / ".github" / "workflows" / "catalog.yml", ROOT / ".github" / "workflows" / "scan.yml", ROOT / "automation" / "publish.yml"]
RUNTIMES = {"node": ("actions/setup-node@", "node-version"), "python": ("actions/setup-python@", "python-version")}
COMMAND = re.compile(r"(?:^|[\s|;&(]|run: )(node|python3?)\s")


def jobs(path):
    lines = path.read_text().splitlines()
    body, name, found = lines[lines.index("jobs:") + 1:], None, {}
    for line in body:
        header = re.fullmatch(r"  ([A-Za-z_][\w-]*):\s*", line)
        if header:
            name = header.group(1)
            found[name] = []
        elif name:
            found[name].append(line)
    return found


def setups(lines, action, key):
    result = []
    for i, line in enumerate(lines):
        if action in line:
            ref = line.split(action, 1)[1].split()[0]
            version = next((l.split(":", 1)[1].strip() for l in lines[i + 1:i + 6] if l.strip().startswith(key + ":")), None)
            result.append((i, ref, version))
    return result


class WorkflowRuntimeTests(unittest.TestCase):
    def test_every_job_that_runs_node_or_python_sets_up_a_pinned_version_first(self):
        checked = set()
        for path in WORKFLOWS:
            for job, lines in jobs(path).items():
                for runtime, (action, key) in RUNTIMES.items():
                    uses = [i for i, line in enumerate(lines) if any(m.group(1).startswith(runtime) for m in COMMAND.finditer(line))]
                    if not uses:
                        continue
                    checked.add((path.name, job, runtime))
                    configured = setups(lines, action, key)
                    with self.subTest(workflow=path.name, job=job, runtime=runtime):
                        self.assertTrue(configured, f"{job} runs {runtime} without {action}")
                        self.assertLess(configured[0][0], uses[0])
                        self.assertRegex(configured[0][1], r"^[0-9a-f]{40}$")
                        self.assertRegex(configured[0][2] or "", r"^'\d+(\.\d+)?'$")
        self.assertTrue({("catalog.yml", "validate", "node"), ("scan.yml", "scan", "node"), ("publish.yml", "notify_search", "python")} <= checked)

    def test_node_and_python_versions_agree_across_workflows_and_package_engines(self):
        for runtime, (action, key) in RUNTIMES.items():
            pins = {(ref, version) for path in WORKFLOWS for lines in jobs(path).values() for _, ref, version in setups(lines, action, key)}
            self.assertEqual(len(pins), 1, f"{runtime}: {sorted(pins)}")
        node = next(version for path in WORKFLOWS for lines in jobs(path).values() for _, _, version in setups(lines, *RUNTIMES["node"]))
        engines = json.loads((ROOT / "package.json").read_text()).get("engines", {})
        self.assertEqual(engines.get("node"), ">=" + node.strip("'"))


if __name__ == "__main__":
    unittest.main()
