## Agent Coordination

You may be working alongside other AI agents. You must coordinate with them to ensure that the work is done efficiently
and effectively.

- Coordinate with other agents before removing their in-progress edits. Don't revert or delete work you didn't author
  unless everyone agrees.
- Delete unused or obsolete files when your changes make them irrelevant (refactors, feature removals, etc.), and revert
  files only when the change is yours or explicitly requested. If a git operation leaves you unsure about other agents'
  in-flight work, stop and coordinate instead of deleting.
- Before attempting to delete a file to resolve a local type/lint failure, stop and ask the user. Other agents are often
  editing adjacent files; deleting their work to silence an error is never acceptable without explicit approval.
- Never use `git restore` (or similar commands) to revert files you didn't author—coordinate with other agents instead
  so their in-progress work stays intact.
