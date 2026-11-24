#!/usr/bin/env node

/**
 * Builds everything generated from the project folders' README frontmatter:
 *
 *   README.md     the Directory and Generative Experiments tables
 *                 (between the <!-- BEGIN … --> / <!-- END … --> markers)
 *   index.html    the filter buttons, pinned cards, project cards and the
 *                 "last updated" line (also between markers)
 *   projects.json the same list as data, for other sites to read
 *
 *   node scripts/build.js          write the files
 *   node scripts/build.js --check  change nothing; exit 1 if any file is out of date
 *                                  or any project has no `status`
 *
 * Everything outside the markers is hand-written and left alone.
 * See scripts/projects.js for the frontmatter keys.
 */

const fs = require('fs');
const path = require('path');
const { ROOT, GITHUB_PAGES_BASE, collectProjects, byPublishedAsc, byPublishedDesc } = require('./projects');

const CHECK = process.argv.includes('--check');

// ─── shared helpers ───────────────────────────────────────────────────────

function formatMonth(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', timeZone: 'UTC' });
}

function formatDay(dateStr) {
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC' });
}

function replaceSection(content, name, generated, file) {
  const begin = `<!-- BEGIN ${name} -->`;
  const end = `<!-- END ${name} -->`;
  const beginIdx = content.indexOf(begin);
  const endIdx = content.indexOf(end);
  if (beginIdx === -1 || endIdx === -1) {
    throw new Error(`Markers "${begin}" / "${end}" not found in ${file}.`);
  }
  // An array of lines is indented to match the END marker, so generated HTML lines up
  const lineStart = content.lastIndexOf('\n', endIdx) + 1;
  const indent = content.slice(lineStart, endIdx).match(/^\s*/)[0];
  const body = Array.isArray(generated) ? generated.map(l => indent + l).join('\n') : generated;
  return content.slice(0, beginIdx) + `${begin}\n${body}\n${indent}${end}` + content.slice(endIdx + end.length);
}

// ─── README tables (oldest first, unchanged from the old build-readme.js) ──

function buildTable(projects) {
  const rows = projects.map(p => {
    const readme = `[${p.title}](./${p.dir}/)`;
    const site = p.siteUrl ? `[↗](${p.siteUrl})` : '—';
    const desc = (p.summary || p.description || '').replace(/\|/g, '\\|');
    const tag = p.tags.length ? p.tags.map(t => `\`${t}\``).join(' ') : '';
    return `| ${readme} | ${site} | ${desc} | ${tag} | ${p.status || '—'} | ${formatMonth(p.published)} | ${formatMonth(p.updated)} |`;
  });
  return [
    '| Project | Site | Description | Tags | Status | Published | Updated |',
    '|---|---|---|---|---|---|---|',
    ...rows,
  ].join('\n');
}

function buildReadme(projects) {
  const file = path.join(ROOT, 'README.md');
  const sorted = [...projects].sort(byPublishedAsc);
  let content = fs.readFileSync(file, 'utf8');
  content = replaceSection(content, 'DIRECTORY', buildTable(sorted), 'README.md');
  content = replaceSection(content, 'GENERATIVE', buildTable(sorted.filter(p => p.tags.includes('generative'))), 'README.md');
  return { file, content };
}

// ─── index.html ───────────────────────────────────────────────────────────

const ENTITIES = { amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'", apos: "'", nbsp: ' ' };

/** Markdown-ish text → plain text: drop links, emphasis and strikethrough markers. */
function plainText(md) {
  return (md || '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/(\*\*|__|~~|\*|_|`)(.+?)\1/g, '$2')
    .replace(/&(amp|lt|gt|quot|#39|apos|nbsp);/g, (_, e) => ENTITIES[e])
    .replace(/\s+/g, ' ')
    .trim();
}

function esc(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function assetPath(dir, file) {
  return [dir, ...file.split('/')].map(encodeURIComponent).join('/');
}

/** Pages URLs become relative so the page also works from a local server. */
function siteHref(p) {
  if (!p.siteUrl) return null;
  if (p.siteUrl.startsWith(GITHUB_PAGES_BASE)) return p.siteUrl.slice(GITHUB_PAGES_BASE.length);
  return p.siteUrl;
}

function externalHost(p) {
  if (!p.siteUrl || p.siteUrl.startsWith(GITHUB_PAGES_BASE)) return null;
  return new URL(p.siteUrl).host;
}

function slug(p) {
  return p.dir.replace(/[^a-z0-9-]/gi, '-');
}

const ARROW = '<span class="arrow" aria-hidden="true">↗</span>';
const PLAY_ICON = '<svg class="icon-play" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5v11l9.5-5.5z" fill="currentColor"/></svg>';
const PAUSE_ICON = '<svg class="icon-pause" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z" fill="currentColor"/></svg>';

function renderMedia(p, { eager }) {
  const loading = eager ? '' : ' loading="lazy"';
  if (p.thumbnail) {
    const src = assetPath(p.dir, p.thumbnail);
    const img = `<img src="${src}" alt="${esc(p.thumbnailAlt)}" width="800" height="500"${loading} decoding="async">`;
    if (!p.previews.length) return `<div class="project-media">${img}</div>`;
    // The still shows until a visitor asks for motion (hover, focus or the button).
    // preload="none": no video bytes are fetched until then.
    const sources = p.previews
      .map(f => `<source src="${assetPath(p.dir, f)}" type="video/${path.extname(f).slice(1)}">`)
      .join('');
    return `<div class="project-media has-preview">${img}<video muted loop playsinline preload="none" width="800" height="500" aria-hidden="true" tabindex="-1">${sources}</video>` +
      `<button type="button" class="preview-toggle" aria-pressed="false" hidden>${PLAY_ICON}${PAUSE_ICON}<span class="visually-hidden">Play preview of ${esc(p.title)}</span></button></div>`;
  }
  // No image yet: a type-only tile, so every card keeps the same shape
  return `<div class="project-media project-media--placeholder" aria-hidden="true">${layers(p.title)}</div>`;
}

/** Four stacked Bungee Layers fonts; only the first layer is read aloud. */
function layers(title) {
  const text = esc(title);
  return `<span class="layers"><span class="layer-regular">${text}</span><span class="layer-inline" aria-hidden="true">${text}</span><span class="layer-outline" aria-hidden="true">${text}</span><span class="layer-shade" aria-hidden="true">${text}</span></span>`;
}

function renderTitle(p, href, { layered }) {
  const inner = layered ? layers(p.title) : esc(p.title);
  return `<h3 class="project-title" id="${slug(p)}"><a href="${esc(href)}">${inner}</a></h3>`;
}

function renderMeta(p) {
  const parts = [];
  if (p.status) parts.push(`<span class="status status--${p.status}"><span class="visually-hidden">Status: </span>${p.status}</span>`);
  if (p.published) parts.push(`<time datetime="${p.published}">${formatMonth(p.published)}</time>`);
  if (p.updated && formatMonth(p.updated) !== formatMonth(p.published)) {
    parts.push(`updated <time datetime="${p.updated}">${formatMonth(p.updated)}</time>`);
  }
  const host = externalHost(p);
  if (host) parts.push(`on ${esc(host)}`);
  if (!p.siteUrl) parts.push('no live site');
  return `<p class="project-meta">${parts.join('<span aria-hidden="true"> · </span><span class="visually-hidden">, </span>')}</p>`;
}

function renderCard(p, { pinned = false, eager = false } = {}) {
  const href = siteHref(p) || p.sourceUrl;
  const leavesPlayground = /^https?:/.test(href);
  const summary = plainText(p.summary || p.description);
  const tags = p.tags.length
    ? `<ul class="tag-list" aria-label="Tags">${p.tags.map(t => `<li>${esc(t)}</li>`).join('')}</ul>`
    : '';
  // The title link covers the whole card (see .project-title a::after);
  // "read me" sits above it so it stays its own target.
  // Pinned cards also get the works-style pill; it's decoration (the whole card is the link)
  const cta = pinned ? `<span class="cta" aria-hidden="true">${p.siteUrl ? 'open' : 'read me'} ›</span>` : '';
  const readme = p.siteUrl
    ? `<p class="project-links"><a href="${esc(p.sourceUrl)}">read me<span class="visually-hidden">: ${esc(p.title)} on GitHub</span>${ARROW}</a>${cta}</p>`
    : `<p class="project-links"><span class="hint">opens the read me on GitHub${ARROW}</span>${cta}</p>`;
  const cls = pinned ? 'project-card project-card--pinned' : 'project-card';
  return [
    `<li class="project" data-tags="${esc(p.tags.join(' '))}">`,
    // Media comes after the text in the source (so the title is read and
    // focused first) and is moved above it with CSS `order`.
    `  <article class="${cls}${leavesPlayground ? ' is-external' : ''}" aria-labelledby="${slug(p)}">`,
    `    <div class="project-body">`,
    `      ${renderTitle(p, href, { layered: pinned })}`,
    `      ${renderMeta(p)}`,
    summary ? `      <p class="project-summary">${esc(summary)}</p>` : null,
    tags ? `      ${tags}` : null,
    `      ${readme}`,
    `    </div>`,
    `    ${renderMedia(p, { eager })}`,
    `  </article>`,
    `</li>`,
  ].filter(Boolean);
}

function buildFilters(projects) {
  const counts = new Map();
  for (const p of projects) for (const t of p.tags) counts.set(t, (counts.get(t) || 0) + 1);
  const tags = [...counts.keys()].sort();
  const button = (value, label, count, pressed) =>
    `<li><button type="button" data-filter="${esc(value)}" aria-pressed="${pressed}">${esc(label)} <span class="count">${count}<span class="visually-hidden"> projects</span></span></button></li>`;
  return [
    button('all', 'everything', projects.length, true),
    ...tags.map(t => button(t, t, counts.get(t), false)),
  ];
}

function buildIndex(projects) {
  const file = path.join(ROOT, 'index.html');
  const newestFirst = [...projects].sort(byPublishedDesc);
  const pinned = newestFirst
    .filter(p => p.pinned !== null)
    .sort((a, b) => a.pinned - b.pinned || byPublishedDesc(a, b));
  const rest = newestFirst.filter(p => p.pinned === null);
  const latest = projects.map(p => p.updated || p.published).filter(Boolean).sort().pop();

  let content = fs.readFileSync(file, 'utf8');
  content = replaceSection(content, 'FILTERS', buildFilters(projects), 'index.html');
  content = replaceSection(content, 'PINNED', pinned.flatMap(p => renderCard(p, { pinned: true, eager: true })), 'index.html');
  content = replaceSection(content, 'PROJECTS', rest.flatMap((p, i) => renderCard(p, { eager: i < 2 && !pinned.length })), 'index.html');
  content = replaceSection(content, 'UPDATED', [`Latest project update: <time datetime="${latest}">${formatDay(latest)}</time>.`], 'index.html');
  return { file, content };
}

// ─── projects.json ────────────────────────────────────────────────────────

function buildJson(projects) {
  const file = path.join(ROOT, 'projects.json');
  const abs = (dir, f) => (f ? GITHUB_PAGES_BASE + assetPath(dir, f) : null);
  const data = [...projects].sort(byPublishedDesc).map(p => ({
    dir: p.dir,
    title: p.title,
    summary: plainText(p.summary || p.description) || null,
    published: p.published,
    updated: p.updated,
    tags: p.tags,
    status: p.status,
    url: p.siteUrl,
    source: p.sourceUrl,
    pinned: p.pinned === null ? null : (Number.isFinite(p.pinned) ? p.pinned : true),
    thumbnail: abs(p.dir, p.thumbnail),
    preview: p.previews.map(f => abs(p.dir, f)),
  }));
  return { file, content: JSON.stringify(data, null, 2) + '\n' };
}

// ─── write or check ───────────────────────────────────────────────────────

const projects = collectProjects();
const noStatus = projects.filter(p => !p.status).map(p => p.dir);
const outputs = [buildReadme(projects), buildIndex(projects), buildJson(projects)];

const stale = outputs.filter(o => !fs.existsSync(o.file) || fs.readFileSync(o.file, 'utf8') !== o.content);

if (CHECK) {
  if (noStatus.length) {
    console.error(`No status: ${noStatus.join(', ')}`);
    console.error('Add `status: active | paused | done | archived` to each README\'s frontmatter.');
  }
  if (stale.length) {
    console.error(`Out of date: ${stale.map(o => path.relative(ROOT, o.file)).join(', ')}`);
    console.error('Run `node scripts/build.js` and commit the result.');
  }
  if (stale.length || noStatus.length) process.exit(1);
  console.log(`Up to date: ${projects.length} projects.`);
} else {
  for (const o of stale) fs.writeFileSync(o.file, o.content);
  const pinnedCount = projects.filter(p => p.pinned !== null).length;
  if (noStatus.length) console.warn(`No status yet: ${noStatus.join(', ')} (build.js --check will fail).`);
  console.log(`${projects.length} projects (${pinnedCount} pinned). ` +
    (stale.length ? `Wrote ${stale.map(o => path.relative(ROOT, o.file)).join(', ')}.` : 'Nothing changed.'));
}
