# Tasks

One file per project, `<dir>.md`, read by `scripts/sync-github.mjs`. Each `- [ ] task` line becomes an issue with the project's label, as a sub-issue of its tracking issue; `- [x]` closes it. Lines indented under a task become its body. A `## <milestone title>` heading files the tasks below it under that milestone, once the milestone exists on GitHub.

These are drafts from the READMEs and known gaps. Edit them before `node scripts/sync-github.mjs --apply`: a task is matched to its issue by its title, so renaming a task after it's synced makes a new issue.
