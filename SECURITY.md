# Security and release checklist

- API keys belong in `server/*.local` (ignored) or environment variables only.
- Before publishing, run a secret scan over the complete Git history.
- If a key was ever committed, revoke it first, then rewrite history with
  `git filter-repo`/BFG and force-push the cleaned branch. Removing the file in
  a new commit does not remove the key from GitHub history.
- For an offline evaluation, use the sample `.room.json` files. Online
  generation requires locally configured Step/GLM credentials.
