# Setup Guide

One guide, three platforms. Follow the column for your OS; skip the others. Budget
about ten minutes for a first-time setup.

This covers getting the repo running to try the examples. If you're contributing to
the repo itself (editing chapters, running linters), see the **Development** section
in [README.md](./README.md) after this.

---

## 0. What you need

| Need | Version | Why |
|---|---|---|
| Python | **3.10 or newer** | `google-genai` requires it; Python 3.9 reached end of life 31 Oct 2025 |
| pip | any recent | installs the dependencies |
| Git | any recent | to clone the repo |
| A Google account | — | to get a free Gemini API key |

Check what you have before doing anything else:

```bash
python3 --version     # Windows: python --version
git --version
```

If Python prints 3.9 or lower, install a newer version first — everything below
assumes 3.10+.

---

## 1. Clone the repo

```bash
git clone https://github.com/tarunmudgal/ai_agent_blueprint.git
cd ai_agent_blueprint
```

---

## 2. Create a virtual environment

A virtual environment keeps this repo's dependencies separate from everything else
on your machine.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows — PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If PowerShell blocks the script with an execution-policy error, run this once,
> then retry:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Windows — Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**All platforms:** your prompt should now start with `(.venv)`. That confirms it
worked. To leave the environment later, run `deactivate` (same command everywhere).

---

## 3. Install dependencies

From the repo root, this installs everything needed to run every chapter's examples:

```bash
python3 -m pip install -r requirements.txt
```

(Windows: use `python` instead of `python3` if you didn't install from the Microsoft
Store.)

Only want to work through a single chapter? Its own folder has a narrower
`requirements.txt` with comments on why each package is needed — e.g.
[`01-smart-intern-prompt-engineering/requirements.txt`](./01-smart-intern-prompt-engineering/requirements.txt).

Verify the SDK version — the Interactions API used throughout this repo requires
`google-genai` **1.55.0 or newer**:

```bash
python3 -c "import google.genai as g; print(g.__version__)"
```

If that prints something older, or errors out, run
`python3 -m pip install -U google-genai` and confirm you're inside the virtual
environment (check for `(.venv)` in your prompt).

---

## 4. Get a Gemini API key

1. Go to **https://aistudio.google.com/apikey**.
2. Sign in with your Google account.
3. If you're new, AI Studio creates a project and key for you automatically — copy it.
   Otherwise click **Create API key**.
4. Copy the key somewhere safe immediately — you can't view the full key again later.

Treat the key like a password. Never commit it, paste it into a chat, or put it in a
URL.

> **Note:** new keys from AI Studio are created as "Auth keys." From September 2026,
> the Gemini API rejects requests from older "Standard" keys — if you're reusing a
> key from an older project, check it in AI Studio and migrate before then.

---

## 5. Set the API key

The SDK reads the `GEMINI_API_KEY` environment variable automatically — no code
changes needed once it's set. Two ways to set it:

### Option A — `.env` file (recommended)

Works the same on every platform, because Python reads it, not your shell.

```bash
cd 01-smart-intern-prompt-engineering
cp .env.example .env
```

Open `.env` in any text editor and paste your key in place of `your-key-here`. Save it.

`.env` is already covered by `.gitignore` — it will not be committed.

### Option B — shell environment variable

Only lasts for the current terminal session unless you add it to your shell profile.

**macOS / Linux (bash or zsh)**
```bash
export GEMINI_API_KEY="paste-your-key-here"
```

**Windows — PowerShell**
```powershell
$env:GEMINI_API_KEY = "paste-your-key-here"
```

**Windows — Command Prompt**
```cmd
set GEMINI_API_KEY=paste-your-key-here
```

To make it permanent:

**macOS / Linux** — append to your shell profile and reload it:
```bash
echo 'export GEMINI_API_KEY="paste-your-key-here"' >> ~/.zshrc   # zsh (macOS default)
source ~/.zshrc
# or, for bash:
echo 'export GEMINI_API_KEY="paste-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows** — set it for your user account, then **close and reopen** the terminal
(existing windows won't pick it up):
```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "paste-your-key-here", "User")
```
Or via the GUI: Start → "Edit environment variables for your account" → **New** →
name `GEMINI_API_KEY`, paste the value → OK.

---

## 6. Verify everything works

From inside `01-smart-intern-prompt-engineering/`, with your virtual environment
active:

```bash
python3 examples/01_hello_and_tokens.py
```

You should see a token count, a real response from Gemini, and a usage breakdown. If
you see that, your Python, your dependencies, and your API key are all confirmed
working together.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `401` / `PERMISSION_DENIED` | Key not set in *this* shell/session | Check `.env` exists and has the real key, or `echo $GEMINI_API_KEY` (macOS/Linux) / `echo $env:GEMINI_API_KEY` (PowerShell) is non-empty |
| `401` on a key you've had a while | Old "Standard" key, post-migration deadline | Create a new key in AI Studio |
| `404` / model not found | Model name typo | Check the script — every example pins `MODEL` in one place |
| `429 RESOURCE_EXHAUSTED` | Rate or spend limit | Wait and retry; check https://aistudio.google.com/rate-limit |
| `ImportError: google.genai` | Not installed, or wrong venv | Confirm `(.venv)` is in your prompt, then reinstall |
| `AttributeError: ... 'interactions'` | SDK older than 1.55.0 | `python3 -m pip install -U google-genai` |
| Works in terminal, fails in your IDE | IDE started before the env var was set | Restart the IDE, or use the `.env` file approach instead |
| PowerShell won't run `Activate.ps1` | Execution policy | See the note under step 2 |

Still stuck: https://ai.google.dev/gemini-api/docs/troubleshooting or
https://discuss.ai.google.dev/c/gemini-api/

---

**Next:** open [`01-smart-intern-prompt-engineering/00-index.md`](./01-smart-intern-prompt-engineering/00-index.md)
for the chapter's table of contents and three suggested reading routes.
