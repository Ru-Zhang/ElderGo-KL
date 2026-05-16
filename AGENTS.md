# Agent instructions (ElderGo-KL)

## Git commits

- **Never** add `Co-authored-by: Cursor <cursoragent@cursor.com>` (or any Cursor co-author trailer) to commit messages.
- Commit messages should list only human authors for this project.

After cloning, enable the repo hook once:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
```
