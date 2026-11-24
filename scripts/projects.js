/**
 * Reads every project folder's README.md frontmatter and returns one
 * normalized list. Shared by scripts/build.js (root README tables,
 * index.html and projects.json) and scripts/capture-media.mjs.
 *
 * Frontmatter keys (all optional except published):
 *
 *   published: YYYY-MM-DD   sort key for the directory (newest first on the page)
 *   updated:   YYYY-MM-DD
 *   tags:      generative, interactive        comma-separated
 *   url:       https://…    live site somewhere other than GitHub Pages
 *   nosite:    true         no live site at all
 *   title:     Display name  overrides the README's # heading
 *   summary:   One or two sentences for the directory cards and README tables
 *              (otherwise the README's first paragraph is used)
 *   pinned:    1            pin to the top of index.html; lower numbers come first
 *   thumbnail: path         still image, relative to the project folder
 *                           (otherwise thumbnail.webp/.jpg/.png in the folder)
 *   thumbnail_alt: text     alt text for the thumbnail (otherwise decorative)
 *   preview:   path         short looping video (.mp4/.webm), relative to the folder
 *                           (otherwise preview.mp4 / preview.webm in the folder)
 *   status:    active | paused | done | archived      required; `build.js --check` fails without it
 *              active    being worked on now
 *              paused    unfinished, and set aside for now
 *              done      finished; it may still get fixes
 *              archived  kept for the record, no longer maintained
 *   issue:     123          the project's tracking issue on GitHub. Written by
 *                           scripts/sync-github.mjs; don't set it by hand
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const GITHUB_PAGES_BASE = 'https://jas0nmjames.github.io/playground/';
const GITHUB_TREE_BASE = 'https://github.com/jas0nmjames/playground/tree/main/';

const THUMBNAIL_NAMES = ['thumbnail.webp', 'thumbnail.jpg', 'thumbnail.jpeg', 'thumbnail.png', 'thumbnail.avif', 'thumbnail.gif'];
const PREVIEW_NAMES = ['preview.webm', 'preview.mp4'];
const STATUSES = ['active', 'paused', 'done', 'archived'];

function unquote(value) {
  const m = value.match(/^(['"])(.*)\1$/);
  return m ? m[2] : value;
}

function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return {};
  const result = {};
  for (const line of match[1].split(/\r?\n/)) {
    if (/^\s*#/.test(line)) continue;
    const [key, ...rest] = line.split(':');
    if (!key || !rest.length) continue;
    result[key.trim()] = unquote(rest.join(':').trim());
  }
  return result;
}

function stripFrontmatter(content) {
  return content.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n*/, '');
}

function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

function extractDescription(content) {
  const lines = content.split('\n');
  let pastH1 = false;
  for (let i = 0; i < lines.length; i++) {
    const trimmed = lines[i].trim();
    if (!pastH1) {
      if (/^#\s/.test(trimmed)) pastH1 = true;
      continue;
    }
    if (!trimmed) continue;
    if (trimmed.startsWith('#')) break;
    if (trimmed.startsWith('[![')) continue;
    if (trimmed.startsWith('![')) continue;
    if (trimmed.startsWith('*') && trimmed.endsWith('*')) continue;
    // Join the rest of the paragraph (hard-wrapped lines) into one line
    const paragraph = [trimmed];
    for (let j = i + 1; j < lines.length; j++) {
      const next = lines[j].trim();
      if (!next || /^([#>|`-]|\d+\.\s|!\[|\[!\[)/.test(next)) break;
      paragraph.push(next);
    }
    return paragraph.join(' ');
  }
  return null;
}

function firstExisting(dir, names) {
  return names.find(name => fs.existsSync(path.join(ROOT, dir, name))) || null;
}

function collectProjects() {
  const dirs = fs.readdirSync(ROOT).filter(name => {
    if (name.startsWith('.')) return false;
    return fs.statSync(path.join(ROOT, name)).isDirectory();
  });

  const projects = [];

  for (const dir of dirs) {
    const readmePath = path.join(ROOT, dir, 'README.md');
    if (!fs.existsSync(readmePath)) continue;

    const raw = fs.readFileSync(readmePath, 'utf8');
    const fm = parseFrontmatter(raw);
    const body = stripFrontmatter(raw);
    const tags = fm.tags ? fm.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
    const nosite = fm.nosite === 'true';
    const siteUrl = nosite ? null : (fm.url ? fm.url.trim() : `${GITHUB_PAGES_BASE}${dir}/`);

    let pinned = null;
    if (fm.pinned && fm.pinned !== 'false') {
      const n = Number(fm.pinned);
      pinned = Number.isFinite(n) ? n : Infinity; // `pinned: true` sorts after numbered pins
    }

    const thumbnail = fm.thumbnail || firstExisting(dir, THUMBNAIL_NAMES);
    const previews = fm.preview
      ? [fm.preview]
      : PREVIEW_NAMES.filter(name => fs.existsSync(path.join(ROOT, dir, name)));

    const status = fm.status ? fm.status.trim().toLowerCase() : null;
    if (status && !STATUSES.includes(status)) {
      throw new Error(`${dir}/README.md has status: ${fm.status}; use one of ${STATUSES.join(', ')}`);
    }
    const issue = fm.issue && /^\d+$/.test(fm.issue.trim()) ? Number(fm.issue) : null;

    for (const file of [thumbnail, ...previews].filter(Boolean)) {
      if (!fs.existsSync(path.join(ROOT, dir, file))) {
        throw new Error(`${dir}/README.md points at ${file}, which does not exist`);
      }
    }

    projects.push({
      dir,
      title: fm.title || extractTitle(body) || dir,
      description: extractDescription(body),
      summary: fm.summary || null,
      published: fm.published || null,
      updated: fm.updated || null,
      tags,
      siteUrl,
      sourceUrl: `${GITHUB_TREE_BASE}${dir}`,
      pinned,
      thumbnail,
      thumbnailAlt: fm.thumbnail_alt || '',
      previews,
      status,
      issue,
    });
  }

  return projects;
}

/** Oldest first; projects with no published date go last, alphabetically. */
function byPublishedAsc(a, b) {
  if (a.published && b.published) return a.published.localeCompare(b.published) || a.dir.localeCompare(b.dir);
  if (a.published) return -1;
  if (b.published) return 1;
  return a.dir.localeCompare(b.dir);
}

/** Newest first; projects with no published date go last, alphabetically. */
function byPublishedDesc(a, b) {
  if (a.published && b.published) return b.published.localeCompare(a.published) || a.dir.localeCompare(b.dir);
  return byPublishedAsc(a, b);
}

module.exports = {
  ROOT,
  STATUSES,
  GITHUB_PAGES_BASE,
  collectProjects,
  byPublishedAsc,
  byPublishedDesc,
};
