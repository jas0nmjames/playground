#!/usr/bin/env node

/**
 * Mirrors each project's README frontmatter onto GitHub, and turns its reviewed
 * task list into issues. The README stays the source of truth for what a
 * project is (title, summary, dates, status); GitHub owns the tasks.
 *
 *   node scripts/sync-github.mjs                 dry run (the default): print every change
 *   node scripts/sync-github.mjs --apply         make the changes
 *   node scripts/sync-github.mjs --offline       dry run without reading GitHub (as if nothing existed)
 *   node scripts/sync-github.mjs --only labels|issues|tasks|project
 *
 * Running it twice changes nothing the second time.
 *
 * What it keeps in step, for every project scripts/projects.js lists:
 *
 *   label "project: <dir>"   one per project, all one color; plus the label "tracking"
 *   tracking issue           "Project: <title>", labelled with both. Its body is the
 *                            summary, published and updated dates, status, live and
 *                            source links, and the project's milestones and releases
 *                            (a milestone titled "<title> · …", a release named
 *                            "<title>…"). Closed when the status is done or archived,
 *                            open otherwise. Its number goes back into the README as
 *                            `issue:`, so later runs update the same issue. Edit the
 *                            README, not the issue: the body is rewritten.
 *   tasks                    only from scripts/tasks/<dir>.md, a reviewed list: one
 *                            "- [ ] task" per line ("- [x]" closes it), optional
 *                            indented lines below a task as its body, and optional
 *                            "## <milestone title>" headings that file the tasks below
 *                            them under that milestone. Each task is an issue with the
 *                            project's label, a sub-issue of the tracking issue.
 *                            Matched by title, so renaming a task makes a new issue.
 *   Project "Playground"     a user-level GitHub Project, created once, with the
 *                            fields Status (single select: active, paused, done,
 *                            archived), Published (date), Updated (date) and Project
 *                            (text). Every tracking issue and task is added to it with
 *                            those fields set from its project's frontmatter.
 *
 * Dates are always the frontmatter's `published` and `updated`, never git dates:
 * the folders came into this repo in batches, so first commits are often wrong.
 *
 * Run it on your Mac. It needs gh, logged in with the project scope:
 *   gh auth refresh -s project
 * The Actions GITHUB_TOKEN can't write to a user-level Project, so this isn't
 * part of the workflow. GitHub's API can't make Project views; the script
 * prints the three to make by hand.
 */

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { ROOT, GITHUB_PAGES_BASE, STATUSES, collectProjects, byPublishedAsc } = require('./projects.js');

const OWNER = 'jas0nmjames';
const REPO = `${OWNER}/playground`;
const PROJECT_TITLE = 'Playground';
const LABEL_COLOR = 'c4c6e2'; // the directory site's --secondary
const TRACKING = { name: 'tracking', color: 'e05b08', description: "A project's tracking issue, kept in sync with its README" };
const STATUS_COLORS = { active: 'GREEN', paused: 'YELLOW', done: 'BLUE', archived: 'GRAY' };
const CLOSED_STATUSES = ['done', 'archived'];
const TASKS_DIR = path.join(ROOT, 'scripts', 'tasks');
const BLOB = `https://github.com/${REPO}/blob/main/`;

const argv = process.argv.slice(2);
const APPLY = argv.includes('--apply');
const OFFLINE = argv.includes('--offline');
const ONLY = argv.includes('--only') ? argv[argv.indexOf('--only') + 1] : 'all';
if (APPLY && OFFLINE) { console.error('--offline is for dry runs only'); process.exit(2); }
const step = name => ONLY === 'all' || ONLY === name;

// ─── gh ───────────────────────────────────────────────────────────────────

function gh(args, { input, json = false } = {}) {
  const out = execFileSync('gh', args, { input, encoding: 'utf8', maxBuffer: 64 << 20, stdio: ['pipe', 'pipe', 'pipe'] });
  return json ? JSON.parse(out || 'null') : out.trim();
}
function ghPages(apiPath) { // REST list, every page, as one array
  return OFFLINE ? [] : gh(['api', '--paginate', '--slurp', apiPath], { json: true }).flat();
}
const read = (fn, fallback) => (OFFLINE ? fallback : fn());

let changes = 0;
function say(kind, text) { console.log(`${kind.padEnd(7)} ${text}`); if (kind !== 'ok') changes++; }
/** Runs a write with --apply; in a dry run, prints it and returns `dry`. */
function write(args, { input, json, dry = null } = {}) {
  const shown = args.map(a => (/[\s'"·]/.test(a) ? JSON.stringify(a) : a)).join(' ');
  console.log(`          $ gh ${shown.length > 220 ? shown.slice(0, 220) + '…' : shown}`);
  return APPLY ? gh(args, { input, json }) : dry;
}

// ─── the projects, as GitHub should show them ────────────────────────────

const projects = collectProjects().sort(byPublishedAsc);
const missing = projects.filter(p => !p.status).map(p => p.dir);
if (missing.length) { console.error(`No status in: ${missing.join(', ')}. Run node scripts/build.js --check.`); process.exit(1); }

const labelOf = p => `project: ${p.dir}`;
const trackingTitle = p => `Project: ${p.title}`;
const marker = p => `<!-- sync-github: ${p.dir} -->`;

function plain(md) {
  return (md || '').replace(/\[([^\]]+)\]\([^)]*\)/g, '$1').replace(/\s+/g, ' ').trim();
}

function trackingBody(p, milestones, releases) {
  const rows = [
    ['Status', p.status],
    ['Published', p.published || '—'],
    ['Updated', p.updated || '—'],
    ['Live', p.siteUrl ? p.siteUrl : 'no live site'],
    ['Source', p.sourceUrl],
  ];
  const lines = [
    plain(p.summary || p.description),
    '',
    '| | |',
    '|---|---|',
    ...rows.map(([k, v]) => `| ${k} | ${v} |`),
  ];
  const mine = milestones.filter(m => m.title.startsWith(`${p.title} · `)).sort((a, b) => a.title.localeCompare(b.title, 'en', { numeric: true }));
  if (mine.length) lines.push('', `**Milestones:** ${mine.map(m => `[${m.title.slice(p.title.length + 3)}](${m.html_url})${m.state === 'closed' ? ' (closed)' : ''}`).join(' · ')}`);
  const rel = releases.filter(r => (r.name || '').startsWith(p.title)).sort((a, b) => (a.tag_name || '').localeCompare(b.tag_name || ''));
  if (rel.length) lines.push('', `**Releases:** ${rel.map(r => `[${r.name}](${r.html_url})`).join(' · ')}`);
  lines.push('', `<sub>Kept in sync with [\`${p.dir}/README.md\`](${BLOB}${p.dir}/README.md) by \`scripts/sync-github.mjs\`: edit the README's frontmatter, not this issue. Tasks are its sub-issues, from \`scripts/tasks/${p.dir}.md\`.</sub>`, marker(p));
  return lines.join('\n');
}

function readTasks(dir) {
  const file = path.join(TASKS_DIR, `${dir}.md`);
  if (!existsSync(file)) return [];
  const tasks = [];
  let milestone = null;
  for (const line of readFileSync(file, 'utf8').split('\n')) {
    const h = line.match(/^##\s+(.+?)\s*$/);
    if (h) { milestone = h[1]; continue; }
    const t = line.match(/^- \[( |x|X)\] (.+?)\s*$/);
    if (t) { tasks.push({ title: t[2], done: t[1] !== ' ', milestone, body: [] }); continue; }
    const b = line.match(/^ {2,}(\S.*)$/);
    if (b && tasks.length) tasks[tasks.length - 1].body.push(b[1]);
  }
  return tasks.map(t => ({ ...t, body: t.body.join('\n') }));
}

function setFrontmatter(dir, key, value) {
  const file = path.join(ROOT, dir, 'README.md');
  const raw = readFileSync(file, 'utf8');
  const m = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) throw new Error(`${dir}/README.md has no frontmatter`);
  const lines = m[1].split(/\r?\n/);
  const i = lines.findIndex(l => l.startsWith(`${key}:`));
  if (i >= 0) lines[i] = `${key}: ${value}`; else lines.push(`${key}: ${value}`);
  writeFileSync(file, raw.slice(0, m.index) + `---\n${lines.join('\n')}\n---` + raw.slice(m.index + m[0].length));
}

console.log(`== sync-github (${APPLY ? 'APPLY' : 'DRY RUN'}${OFFLINE ? ', offline' : ''}): ${projects.length} projects`);

// ─── what's on GitHub now ─────────────────────────────────────────────────

const ghLabels = read(() => gh(['label', 'list', '--repo', REPO, '--limit', '1000', '--json', 'name,color,description'], { json: true }), []);
const milestones = ghPages(`repos/${REPO}/milestones?state=all&per_page=100`);
const releases = ghPages(`repos/${REPO}/releases?per_page=100`);
const issues = OFFLINE ? [] : ghPages(`repos/${REPO}/issues?state=all&per_page=100`).filter(i => !i.pull_request);
const issueByNumber = new Map(issues.map(i => [i.number, i]));
const labelNames = i => (i.labels || []).map(l => (typeof l === 'string' ? l : l.name));

// ─── 1. labels ────────────────────────────────────────────────────────────

if (step('labels')) {
  console.log('\n-- 1. Labels');
  const wanted = [TRACKING, ...projects.map(p => ({ name: labelOf(p), color: LABEL_COLOR, description: p.title.slice(0, 100) }))];
  for (const w of wanted) {
    const have = ghLabels.find(l => l.name.toLowerCase() === w.name.toLowerCase());
    if (!have) {
      say('create', `label "${w.name}"`);
      write(['label', 'create', w.name, '--repo', REPO, '--color', w.color, '--description', w.description]);
    } else if (have.color.toLowerCase() !== w.color || (have.description || '') !== w.description) {
      say('update', `label "${w.name}"`);
      write(['label', 'edit', have.name, '--repo', REPO, '--color', w.color, '--description', w.description]);
    } else say('ok', `label "${w.name}"`);
  }
}

// ─── 2. tracking issues ───────────────────────────────────────────────────

const tracking = new Map(); // dir → issue number (or null in a dry run)
for (const p of projects) {
  let n = p.issue && issueByNumber.has(p.issue) ? p.issue : null;
  if (!n) { // recover the issue if the README lost its number
    const found = issues.find(i => (i.body || '').includes(marker(p)) || (labelNames(i).includes(TRACKING.name) && labelNames(i).includes(labelOf(p))));
    if (found) n = found.number;
  }
  tracking.set(p.dir, n);
}

if (step('issues')) {
  console.log('\n-- 2. Tracking issues');
  for (const p of projects) {
    const body = trackingBody(p, milestones, releases);
    const state = CLOSED_STATUSES.includes(p.status) ? 'closed' : 'open';
    let n = tracking.get(p.dir);
    if (!n) {
      say('create', `"${trackingTitle(p)}" [${state}]`);
      const url = write(['issue', 'create', '--repo', REPO, '--title', trackingTitle(p), '--label', labelOf(p), '--label', TRACKING.name, '--body-file', '-'], { input: body });
      if (APPLY) {
        n = Number(url.split('/').pop());
        tracking.set(p.dir, n);
        issueByNumber.set(n, { number: n, state: 'open', title: trackingTitle(p), body, labels: [labelOf(p), TRACKING.name] });
      }
      if (state === 'closed') write(['issue', 'close', String(n ?? '<new>'), '--repo', REPO, '--reason', 'completed']);
    } else {
      const have = issueByNumber.get(n);
      const edits = [];
      if (have.title !== trackingTitle(p)) edits.push('title');
      if ((have.body || '').trim() !== body.trim()) edits.push('body');
      const lacks = [labelOf(p), TRACKING.name].filter(l => !labelNames(have).includes(l));
      if (lacks.length) edits.push('labels');
      if (edits.length) {
        say('update', `#${n} "${trackingTitle(p)}" (${edits.join(', ')})`);
        write(['issue', 'edit', String(n), '--repo', REPO, '--title', trackingTitle(p), '--body-file', '-', ...lacks.flatMap(l => ['--add-label', l])], { input: body });
      } else say('ok', `#${n} "${trackingTitle(p)}"`);
      if (have.state.toLowerCase() !== state) {
        say(state === 'closed' ? 'close' : 'reopen', `#${n} (status: ${p.status})`);
        write(state === 'closed' ? ['issue', 'close', String(n), '--repo', REPO, '--reason', 'completed'] : ['issue', 'reopen', String(n), '--repo', REPO]);
      }
    }
    if (n !== p.issue) {
      say('write', `issue: ${n ?? '<new>'} into ${p.dir}/README.md`);
      if (APPLY) setFrontmatter(p.dir, 'issue', n);
    }
  }
}

// ─── 3. tasks ─────────────────────────────────────────────────────────────

const taskIssues = new Map(); // dir → [{ number, task }]
const findTask = (p, t) => issues.find(i => i.title === t.title && labelNames(i).includes(labelOf(p)) && !labelNames(i).includes(TRACKING.name));
if (step('tasks')) {
  console.log('\n-- 3. Tasks (from scripts/tasks/<dir>.md)');
  for (const p of projects) {
    const tasks = readTasks(p.dir);
    if (!tasks.length) continue;
    const parent = tracking.get(p.dir);
    const subs = parent && !OFFLINE ? gh(['api', '--paginate', '--slurp', `repos/${REPO}/issues/${parent}/sub_issues?per_page=100`], { json: true }).flat().map(i => i.number) : [];
    const list = [];
    console.log(`  ${p.dir}: ${tasks.length} tasks`);
    for (const t of tasks) {
      const ms = t.milestone ? milestones.find(m => m.title === t.milestone) : null;
      if (t.milestone && !ms) console.log(`          (no milestone "${t.milestone}" on GitHub yet; filed without one)`);
      const state = t.done ? 'closed' : 'open';
      const have = findTask(p, t);
      let n = have ? have.number : null;
      if (!have) {
        say('create', `"${t.title}"${ms ? ` → ${ms.title}` : ''}`);
        const url = write(['issue', 'create', '--repo', REPO, '--title', t.title, '--label', labelOf(p), '--body-file', '-', ...(ms ? ['--milestone', ms.title] : [])], { input: t.body || `A task for ${p.title}, from \`scripts/tasks/${p.dir}.md\`.` });
        if (APPLY) n = Number(url.split('/').pop());
        if (t.done) write(['issue', 'close', String(n ?? '<new>'), '--repo', REPO, '--reason', 'completed']);
      } else {
        const msNow = have.milestone ? have.milestone.title : null;
        if (ms && msNow !== ms.title) { say('update', `#${n} milestone → ${ms.title}`); write(['issue', 'edit', String(n), '--repo', REPO, '--milestone', ms.title]); }
        if (have.state.toLowerCase() !== state) {
          say(t.done ? 'close' : 'reopen', `#${n} "${t.title}"`);
          write(t.done ? ['issue', 'close', String(n), '--repo', REPO, '--reason', 'completed'] : ['issue', 'reopen', String(n), '--repo', REPO]);
        } else if (!(ms && msNow !== ms.title)) say('ok', `#${n} "${t.title}"`);
      }
      if (!n || !parent || !subs.includes(n)) {
        say('attach', `${n ? '#' + n : '<new>'} as a sub-issue of ${parent ? '#' + parent : 'the new tracking issue'}`);
        if (APPLY && n && parent) {
          const id = num => gh(['issue', 'view', String(num), '--repo', REPO, '--json', 'id', '--jq', '.id']);
          write(['api', 'graphql', '-f', 'query=mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{number}}}', '-f', `p=${id(parent)}`, '-f', `c=${id(n)}`]);
        } else {
          console.log('          $ gh api graphql -f query=\'mutation($p:ID!,$c:ID!){addSubIssue(…)}\' -f p=<tracking issue id> -f c=<task id>');
        }
      }
      list.push({ number: n, task: t });
    }
    taskIssues.set(p.dir, list);
  }
}

// ─── 4. the Project ───────────────────────────────────────────────────────

if (step('project')) {
  console.log(`\n-- 4. Project "${PROJECT_TITLE}" (user-level, ${OWNER})`);
  let proj = read(() => gh(['project', 'list', '--owner', OWNER, '--format', 'json', '--limit', '100'], { json: true }).projects.find(x => x.title === PROJECT_TITLE), null);
  if (!proj) {
    say('create', `Project "${PROJECT_TITLE}"`);
    proj = write(['project', 'create', '--owner', OWNER, '--title', PROJECT_TITLE, '--format', 'json'], { json: true, dry: { number: '<new>', id: '<new>' } });
  } else say('ok', `Project "${PROJECT_TITLE}" (#${proj.number})`);
  const live = APPLY || (proj.id !== '<new>' && !OFFLINE);
  const fields = live ? gh(['project', 'field-list', String(proj.number), '--owner', OWNER, '--format', 'json', '--limit', '100'], { json: true }).fields : [];
  const field = name => fields.find(f => f.name === name);

  // Status: a new user Project already has a Status field (Todo, In progress, Done);
  // its options are replaced by the four statuses.
  const status = field('Status');
  const optionNames = status ? (status.options || []).map(o => o.name) : [];
  if (status && STATUSES.every(s => optionNames.includes(s)) && optionNames.length === STATUSES.length) say('ok', 'field Status');
  else if (status) {
    say('update', `field Status options: ${optionNames.join(', ') || '(none)'} → ${STATUSES.join(', ')}`);
    const opts = STATUSES.map(s => `{name:"${s}",color:${STATUS_COLORS[s]},description:""}`).join(',');
    write(['api', 'graphql', '-f', `query=mutation{updateProjectV2Field(input:{fieldId:"${status.id}",singleSelectOptions:[${opts}]}){projectV2Field{...on ProjectV2SingleSelectField{id}}}}`]);
  } else {
    say('create', 'field Status (single select)');
    write(['project', 'field-create', String(proj.number), '--owner', OWNER, '--name', 'Status', '--data-type', 'SINGLE_SELECT', '--single-select-options', STATUSES.join(',')]);
  }
  for (const [name, type] of [['Published', 'DATE'], ['Updated', 'DATE'], ['Project', 'TEXT']]) {
    if (field(name)) say('ok', `field ${name}`);
    else { say('create', `field ${name} (${type.toLowerCase()})`); write(['project', 'field-create', String(proj.number), '--owner', OWNER, '--name', name, '--data-type', type]); }
  }

  // Re-read the fields (new ones, new option ids) before setting values.
  const fieldsNow = APPLY ? gh(['project', 'field-list', String(proj.number), '--owner', OWNER, '--format', 'json', '--limit', '100'], { json: true }).fields : fields;
  const F = name => fieldsNow.find(f => f.name === name);
  const items = live ? gh(['project', 'item-list', String(proj.number), '--owner', OWNER, '--format', 'json', '--limit', '2000'], { json: true }).items : [];
  const norm = item => Object.fromEntries(Object.entries(item).map(([k, v]) => [k.toLowerCase().replace(/\s+/g, ''), v]));
  const byIssue = new Map(items.filter(i => i.content && i.content.number).map(i => [i.content.number, norm(i)]));

  const rows = [];
  for (const p of projects) {
    rows.push({ p, number: tracking.get(p.dir), what: `tracking issue "${trackingTitle(p)}"` });
    for (const t of taskIssues.get(p.dir) || readTasks(p.dir).map(task => ({ number: (findTask(p, task) || {}).number || null, task }))) {
      rows.push({ p, number: t.number, what: `task "${t.task.title}"` });
    }
  }
  console.log(`  ${rows.length} items: ${projects.length} tracking issues and ${rows.length - projects.length} tasks`);
  for (const { p, number, what } of rows) {
    const want = { status: p.status, published: p.published, updated: p.updated, project: p.title };
    let item = number ? byIssue.get(number) : null;
    if (!item) {
      say('add', `${number ? '#' + number : '<new>'} ${what}: ${Object.values(want).join(' · ')}`);
      const added = write(['project', 'item-add', String(proj.number), '--owner', OWNER, '--url', `https://github.com/${REPO}/issues/${number ?? '<new>'}`, '--format', 'json'], { json: true, dry: { id: '<new>' } });
      item = { id: added.id };
    }
    const diffs = Object.entries(want).filter(([k, v]) => v && String(item[k] ?? '') !== v);
    if (!diffs.length) { say('ok', `#${number} ${what}`); continue; }
    if (byIssue.has(number)) say('set', `#${number} ${what}: ${diffs.map(([k, v]) => `${k} ${item[k] ?? '—'} → ${v}`).join(', ')}`);
    for (const [k, v] of diffs) {
      const f = F(k === 'status' ? 'Status' : k[0].toUpperCase() + k.slice(1));
      const base = ['project', 'item-edit', '--id', item.id, '--project-id', proj.id, '--field-id', f ? f.id : `<${k} field>`];
      if (k === 'status') {
        const opt = f && (f.options || []).find(o => o.name === v);
        write([...base, '--single-select-option-id', opt ? opt.id : `<${v}>`]);
      } else if (k === 'project') write([...base, '--text', v]);
      else write([...base, '--date', v]);
    }
  }

  console.log(`
  Views can't be made through GitHub's API. Make these by hand in the Project, once:
  1. Roadmap: layout Roadmap, start date Published, target date Updated, group by
     Status. The "when was each made" timeline.
  2. Board: layout Board, column field Status, filter "is:issue is:open -label:tracking".
     The open tasks by status.
  3. Table: layout Table, group by Project, with Status, Published and Updated shown.`);
}

console.log(`\n${changes ? `${changes} change${changes === 1 ? '' : 's'}` : 'Nothing to change.'}${APPLY ? '' : ' Dry run: nothing was changed. Run again with --apply.'}`);
