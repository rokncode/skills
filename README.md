# Skills

A collection of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) for building polished, Apple-style web interfaces. Each skill is a folder with a `SKILL.md` that an AI coding agent (Claude Code, Cursor, Codex, Gemini CLI, Copilot, …) loads automatically when the task matches its description.


## Installation

### Option 1 — `skills` CLI (recommended)

[skills.sh](https://skills.sh) provides an open CLI that installs skills into any supported agent (Claude Code, Cursor, Codex, Gemini CLI, GitHub Copilot, Windsurf, and more). No setup needed beyond Node.js.

```bash
# Install every skill in this repo (you'll be asked which agents to install into)
npx skills add rokncode/skills

# Install a single skill
npx skills add rokncode/skills --skill liquid-glassy

# Install globally (available in all your projects) instead of the current project
npx skills add rokncode/skills -g

# Target a specific agent and skip prompts
npx skills add rokncode/skills -a claude-code -y

# See which skills the repo contains without installing
npx skills add rokncode/skills --list
```

### Option 2 — Manual install for Claude Code

Claude Code discovers skills from two locations:

- **Personal** (all projects): `~/.claude/skills/`
- **Project** (shared with your team via git): `.claude/skills/` in your repo

```bash
git clone https://github.com/rokncode/skills.git /tmp/rokncode-skills

# Personal
mkdir -p ~/.claude/skills
cp -R /tmp/rokncode-skills/apple-design /tmp/rokncode-skills/liquid-glassy ~/.claude/skills/

# …or per project
mkdir -p .claude/skills
cp -R /tmp/rokncode-skills/liquid-glassy .claude/skills/
```

Restart Claude Code (or start a new session) and the skills will appear. Ask *"what skills are available?"* to confirm, or invoke one directly with `/liquid-glassy`.

### Option 3 — Other agents (manual)

Every skill is just a folder containing `SKILL.md`, so you can copy it into whatever directory your agent reads skills or rules from, for example:

| Agent | Project path | Global path |
| --- | --- | --- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| OpenAI Codex | `.agents/skills/` | `~/.codex/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` |

> Paths change as agents evolve — when in doubt, use the `skills` CLI above, which knows the right location for each agent.

### Claude.ai / Claude Desktop

Zip a skill folder (e.g. `liquid-glassy/`) and upload it under **Settings → Capabilities → Skills**.

## Usage

You don't need to call skills explicitly. The agent reads each skill's `description` and loads it when your request matches, e.g.:

- *"Make this modal a liquid glass card"* → `liquid-glassy`
- *"Add a draggable bottom sheet with a spring that feels native"* → `apple-design`

## Contributing

1. Create a new folder named after the skill (kebab-case).
2. Add a `SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: my-skill
   description: What the skill does and when the agent should use it. Include trigger phrases.
   ---

   # My Skill

   Instructions, examples, and references…
   ```

3. Keep `SKILL.md` focused; put long references in extra files next to it and link to them.
4. Add the skill to the table above and open a PR.
