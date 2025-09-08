# Pull Request

Thank you for your contribution to Talktor! Please follow this template to help reviewers.

## Summary

- What does this PR do? Why?
- Link to issue(s) / context (if any):

## Scope

- [ ] Bug fix
- [ ] Feature
- [ ] Refactor / Cleanup
- [ ] Docs
- [ ] Release

## Versioning

- Current version in `VERSION`: `$(cat VERSION)` (keepers: update when preparing a release PR)
- If this PR is a release:
  - [ ] Bumped `VERSION` (e.g., 0.1.0)
  - [ ] Added/updated entry in `CHANGELOG.md` under `## [X.Y.Z] - YYYY-MM-DD`

## Changes (high level)

- [ ] API surface (endpoints, schemas)
- [ ] Realtime protocol (WS types, audio format)
- [ ] DB schema / migrations
- [ ] Logging or metrics
- [ ] DevOps (scripts, Docker, CI/CD)

## Testing

- [ ] Local run passes (`./scripts/ops/dev_start.sh` then hit `/health`)
- [ ] Manual WS test with `scripts/interactive_audio_ws_client.py`
- [ ] Basic REST sanity (start/end conversation, fetch feedback summary)

## Screenshots (if UI)

<!-- Drag and drop images or GIFs -->

## Checklist

- [ ] I read `docs/CONTEXT_REPOSITORY.md` and followed conventions.
- [ ] I updated docs if behavior changed.
- [ ] I ran `python3 -m compileall backend` (sanity on syntax).
- [ ] No secrets committed; `.env` is used for configuration.
