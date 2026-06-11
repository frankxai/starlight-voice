# Secrets Setup

Do not paste provider keys into chat.

For this repo, use local `.env.local` first:

```powershell
pwsh -File scripts/set-secrets.ps1
```

That command prompts for keys without echoing secret values, then writes:

```text
C:\Users\frank\starlight-voice\.env.local
```

`.env.local` is gitignored.

## What Goes Where

Use `.env.local` for this laptop:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_AGENT_ID`
- `DEEPGRAM_API_KEY`
- `CARTESIA_API_KEY`
- `GROQ_API_KEY`
- `CEREBRAS_API_KEY`

Use LiteLLM when Starlight Voice needs one model gateway across providers:

- consistent model names
- usage limits
- provider fallback
- one local/proxy endpoint for app code

LiteLLM is a model gateway, not the long-term secret vault.

Use Infisical when secrets need to sync across machines or environments:

- this laptop + second laptop
- dev/stage/prod separation
- audit trail
- rotation
- team access

Best current sequence:

1. Local `.env.local` now so development can move.
2. LiteLLM when provider routing becomes real.
3. Infisical before multi-machine or production use.

## Manual Fallback

You can copy the template by hand:

```powershell
Copy-Item .env.example .env.local
notepad .env.local
```

Never commit `.env.local`.
