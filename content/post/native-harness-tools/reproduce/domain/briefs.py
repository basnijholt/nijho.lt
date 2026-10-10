"""Domain paragraphs for the three search roles on the MindRoom shell instance."""

_SETTING = """The agent is a MindRoom agent (an Agno agent assembled by MindRoom
from authored YAML configuration) served through MindRoom's OpenAI-compatible
API. Its `shell` and `file` tools run inside a dedicated Docker worker. Each
task is ONE user message naming a task directory that holds the input files,
plus a short job typical of terminal work: summarize a CSV, count events in a
web log, fix a small Python package until its unittest suite passes, find a
commit in git history, rename a function across a package, filter JSON, find
files by size, dig a value out of nested archives, write a small shell script,
edit one value in a config file without touching anything else, extract one
line from a command that prints a huge amount of output, or merge two CSVs.
After the agent replies, a hidden check grades the files left in the task
directory: exact output files and formats, passing hidden tests, unchanged
files that had to stay unchanged. The chat reply itself is not graded."""

ANALYST = _SETTING + """ The frozen policy is gpt-6-luna, a small fast
model. Rank failure modes by how many trials they cost. Separate "wrong
approach or wrong answer" from "right answer but wrong file, path, or format"
and from "stopped early or never wrote the output" and from tool-handling
problems (huge outputs, truncated results, wrong working directory)."""

DIGESTER = """The trajectory is one MindRoom agent turn: the task, every
assistant step (shell and file tool calls with arguments, tool results as
returned to the model) as stored in the agent's session database, the final
reply, and at the end the GRADING block with the hidden check's verdict.
Read GRADING first, then find the step where the work went wrong: a wrong
command, misread output, a file written to the wrong place or with the wrong
format, an edit that changed more than asked, or a run that ended before the
output existed."""

PROPOSER = _SETTING + """

The harness you edit is the agent's authored configuration,
harness/agent.yaml. Evolvable keys (anything else is rejected before
measurement):
- role, instructions: the agent's system prompt text.
- tools: a list drawn ONLY from [shell, file, python]; all of them run in the
  worker. `shell` runs bash commands (`run_shell_command`, with `tail` and
  `timeout` arguments, plus `check_shell_command`/`kill_shell_command` for
  long runs); `file` reads, writes, searches and patches files relative to the
  worker workspace; `python` runs Python code.
- max_tool_calls_per_turn (int): cap on tool calls in one turn.
- compress_tool_results (bool), compaction (mapping of MindRoom compaction
  overrides: enabled, threshold_tokens, threshold_percent, reserve_tokens):
  how tool results and long histories are kept in context.
- markdown (bool) and show_tool_calls (bool): reply formatting.
Model, provider, memory, learning and worker routing are frozen and injected
by the runner. Out of bounds, enforced before measurement: task ids, any
specific value, name, path or answer from a task, and any reference to the
grader. The run is judged on held-out instances of the same kinds of jobs, so
prefer general working methods (inspect inputs before acting, verify outputs
against the request, keep huge outputs out of context) over anything keyed to
particular instances. Litmus test: would this make a careful engineer more
reliable on many unfamiliar small terminal jobs?"""

CRITIC = """The harness is the authored YAML configuration of a MindRoom agent
(role, instructions, which of the worker-routed shell/file/python tools it has,
tool-call cap, context compression, reply formatting) doing small terminal jobs
graded by hidden checks. General engineering method ("inspect the input files
first", "verify the output file matches the requested format before
finishing", "filter huge command output with grep instead of reading it all",
"run the tests after editing") is legitimate and NOT leakage. Reject task ids,
specific file names, values, function names or answers taken from tasks, and
anything that references the grader."""
