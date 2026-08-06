# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Reasonix is a DeepSeek-native AI coding agent for the terminal: a config- and
plugin-driven harness shipped as a single static Go binary, tuned around
DeepSeek's prefix cache. `REASONIX.md` at the repo root is the project's own
agent-memory file (the Reasonix analog of this file) — read it too; its
conventions apply to all work here.

## Repository layout: four independently built parts

This is a monorepo with **three separate Go modules** plus JS/TS subprojects.
`go build ./...` / `go test ./...` at the root do NOT touch the others:

- **Root module (`reasonix`)** — the CLI/TUI engine. Entry point
  `cmd/reasonix`; the kernel lives under `internal/`. `CGO_ENABLED=0`, lean
  dependencies (see `docs/SPEC.md` §1 — new third-party deps need strong
  justification).
- **`desktop/`** — Wails-based desktop app; a nested Go module (needs CGO/WebKit)
  that imports the root kernel via `replace reasonix => ../`. Frontend is
  Vite + pnpm under `desktop/frontend/`.
- **`sdk/go/`** — public extension SDK with a **hard stdlib-only contract**
  (CI fails if it gains any dependency). Its DTOs are generated from
  `internal/extension/protocol` (`cmd/extension-protocol-gen`), so changes
  there must keep the SDK in sync.
- **`workers/`** (Cloudflare Workers: accounts, crash-report, forum) and
  **`site/`** (Astro website) — TS/JS, deployed by their own workflows.

## Common commands

```bash
make build          # CLI binary -> bin/reasonix (CGO_ENABLED=0, version ldflags)
make test           # go test ./...  (root module only)
make vet            # go vet ./...
make fmt            # gofmt -w .
make hooks          # git hooks: pre-push runs go vet
make cross          # cross-compile 6 targets -> dist/

go test ./internal/agent/ -v                     # one package
go test ./internal/tool/builtin/ -run TestGrep   # one test

make desktop-test   # desktop module tests (cd desktop && go test .)
make sdk-test       # SDK tests (cd sdk/go && go test ./...)
make sdk-test-race
./dev               # desktop dev mode (wails dev + vite, branch-hashed ports)
```

Pre-push CI simulation (from REASONIX.md — run before every commit):

```bash
gofmt -w .
go vet ./...
go test ./internal/tool/builtin/ ./internal/boot/
```

CI also runs `golangci-lint` (config in `.golangci.yml`), `go test -race` over
concurrency-heavy packages, and the prompt-cache guard tests
(`REASONIX_RELEASE_CACHE_GUARD=1 go test ./...` enables `TestCacheHit*`).

### Isolated dev runs

Never point a source build at real user state. `REASONIX_HOME` gives a build
its own self-contained state tree (config, credentials, sessions, cache):

```bash
REASONIX_HOME=/tmp/reasonix-dev go run ./cmd/reasonix
```

## Architecture

### Dependency direction (acyclic)

```
cli → {agent, plugin, config} → {tool, provider}
```

Built-in subpackages (`provider/openai`, `tool/builtin`) import their parent to
self-register via `init()`; **parents never import children**. `cmd/reasonix`
blank-imports the builtin packages to trigger registration. Before importing a
new internal package from a non-test file, check the target package's *test
files* don't import back to you (run `go test ./path/to/target/`; a
`[setup failed]` message means a cycle).

### Key concepts (multi-file, worth knowing up front)

- **One transport-agnostic controller.** `internal/control.Controller` sits
  behind every frontend — chat TUI (`internal/cli`), HTTP/SSE server
  (`internal/serve`), ACP for editors (`internal/acp`), and the Wails desktop
  app. Add behavior to the controller, not to a frontend, so all inherit it.
- **Cache-first prefix stability is product behavior.** The system-prompt
  prefix (base prompt + tool schemas + memory) must stay byte-stable across
  turns so DeepSeek's automatic prefix cache stays warm. Never mutate it
  mid-session — per-turn material rides the turn tail (see `control.Compose`).
  Guard tests (`TestCacheHit*`) enforce this in CI.
- **Interface-first registries.** `provider.Provider` (Name/Stream) and
  `tool.Tool` (Name/Description/Schema/ReadOnly/Execute) are resolved by name
  from registries declared in `reasonix.toml`. Any OpenAI-compatible vendor is
  a config instance of `kind = "openai"`, not new code. Tool `Execute` errors
  are returned to the model for self-correction, never fatal.
- **Two extension tiers.** Compile-time built-ins (self-register in `init()`),
  and runtime plugins: MCP servers (`internal/plugin`, stdio/http/sse
  transports) and Extension Protocol v1 sidecars (`internal/extension`).
- **Agent loop** in `internal/agent` (session, coordinator, compaction,
  subagents); typed events flow through `internal/event`.

`docs/SPEC.md` is the engineering contract — code follows it; change the spec
first, then the code. `docs/TOOL_CONTRACT.md` documents the built-in tool
schema surface and is backed by tests.

Adding a built-in tool, a provider, or i18n strings: follow the recipes in
`CONTRIBUTING.md` (tools register with `tool.RegisterBuiltin`, providers with
`provider.Register`; i18n strings go in `internal/i18n` for both `en` and `zh`
locales — `TestCatalogsComplete` fails if one is missed).

## Conventions

- English is the primary language for all code, comments, and user-facing
  strings. Most `docs/*.md` have a `.zh-CN.md` counterpart to keep in sync.
- `gofmt` enforced by CI; wrap errors with `fmt.Errorf("...: %w", err)`.
- Library code never calls `os.Exit` or prints to stdout/stderr — only `cli/`
  and `main` decide exit codes and user-facing messages.
- Exported identifiers need doc comments; each package documents its concern
  in a package comment.
- Conventional Commits (`feat(glob): ...`, `fix: ...`, `test(event): ...`).

## Pull requests

- Base branch is **`main-v2`** (not `main`).
- PR body template requires a `Documentation-impact:` line, and — for changes
  touching cache-sensitive paths (`internal/boot/`, `internal/tool/`,
  `internal/provider/`, `internal/agent/` prompt/compaction files,
  `internal/memory/`, `internal/skill/`, `internal/plugin/`, etc.; full list in
  `scripts/check-cache-impact.sh`) — `Cache-impact:` (`none|low|medium|high`
  plus reason) and `Cache-guard:` (the focused guard test/command) lines.
  Changes under `internal/config/`, `internal/memory/`, `internal/outputstyle/`,
  `internal/skill/`, or `internal/boot/` also need `System-prompt-review:`.
  Placeholder values (`n/a`, `todo`, `tbd`) are rejected by CI.
- Review-feedback hygiene: amend rather than stacking fixup commits; at most
  one force-push per review round; keep the diff minimal.
