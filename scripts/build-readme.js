#!/usr/bin/env node

/**
 * Reads each subfolder's README.md, parses frontmatter dates and tags,
 * and regenerates two sections in the root README.md:
 *
 *   <!-- BEGIN DIRECTORY --> / <!-- END DIRECTORY -->
 *     Full project table, sorted by published date (oldest first).
 *
 *   <!-- BEGIN GENERATIVE --> / <!-- END GENERATIVE -->
 *     Table filtered to projects tagged "generative".
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const ROOT_README = path.join(ROOT, 'README.md');
const GITHUB_PAGES_BASE = 'https://jas0nmjames.github.io/playground/';

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const result = {};
  for (const line of match[1].split('\n')) {
    const [key, ...rest] = line.split(':');
    if (key && rest.length) result[key.trim()] = rest.join(':').trim();
  }
  return result;
}

function stripFrontmatter(content) {
  return content.replace(/^---\n[\s\S]*?\n---\n*/, '');
}

function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

function extractDescription(content) {
  const lines = content.split('\n');
  let pastH1 = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!pastH1) {
      if (/^#\s/.test(trimmed)) pastH1 = true;
      continue;
    }
    if (!trimmed) continue;
    if (trimmed.startsWith('#')) break;
    if (trimmed.startsWith('[![')) continue;
    if (trimmed.startsWith('![')) continue;
    if (trimmed.startsWith('*') && trimmed.endsWith('*')) continue;
    return trimmed;
  }
  return null;
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T12:00:00Z');
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', timeZone: 'UTC' });
}

function buildTable(projects) {
  const rows = projects.map(p => {
    const readme = `[${p.title}](./${p.dir}/)`;
    const site = p.siteUrl ? `[↗](${p.siteUrl})` : '—';
    const desc = p.description || '';
    const tag = p.tags.length ? p.tags.map(t => `\`${t}\``).join(' ') : '';
    const pub = formatDate(p.published);
    const upd = formatDate(p.updated);
    return `| ${readme} | ${site} | ${desc} | ${tag} | ${pub} | ${upd} |`;
  });

  return [
    '| Project | Site | Description | Tags | Published | Updated |',
    '|---|---|---|---|---|---|',
    ...rows,
  ].join('\n');
}

function replaceSection(content, beginMarker, endMarker, generated) {
  const beginIdx = content.indexOf(beginMarker);
  const endIdx = content.indexOf(endMarker);
  if (beginIdx === -1 || endIdx === -1) {
    console.error(`Markers "${beginMarker}" / "${endMarker}" not found in README.`);
    process.exit(1);
  }
  return (
    content.slice(0, beginIdx) +
    `${beginMarker}\n${generated}\n${endMarker}` +
    content.slice(endIdx + endMarker.length)
  );
}

// Collect subdirectories
const entries = fs.readdirSync(ROOT).filter(name => {
  if (name.startsWith('.')) return false;
  return fs.statSync(path.join(ROOT, name)).isDirectory();
});

const projects = [];

for (const dir of entries) {
  const readmePath = path.join(ROOT, dir, 'README.md');
  if (!fs.existsSync(readmePath)) continue;

  const raw = fs.readFileSync(readmePath, 'utf8');
  const fm = parseFrontmatter(raw);
  const body = stripFrontmatter(raw);
  const title = extractTitle(body) || dir;
  const description = extractDescription(body);
  const tags = fm.tags ? fm.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
  // nosite: true → no live site link (docs/design-only projects)
  const nosite = fm.nosite === 'true';
  // url: explicit frontmatter override (e.g. external deployment); otherwise GitHub Pages
  const siteUrl = nosite ? null : (fm.url ? fm.url.trim() : `${GITHUB_PAGES_BASE}${dir}/`);

  projects.push({
    dir,
    title,
    description,
    published: fm.published || null,
    updated: fm.updated || null,
    tags,
    siteUrl,
  });
}

// Sort: dated projects oldest → newest, then undated alphabetically
projects.sort((a, b) => {
  if (a.published && b.published) return a.published.localeCompare(b.published);
  if (a.published) return -1;
  if (b.published) return 1;
  return a.dir.localeCompare(b.dir);
});

const generativeProjects = projects.filter(p => p.tags.includes('generative'));

let rootContent = fs.readFileSync(ROOT_README, 'utf8');
rootContent = replaceSection(rootContent, '<!-- BEGIN DIRECTORY -->', '<!-- END DIRECTORY -->', buildTable(projects));
rootContent = replaceSection(rootContent, '<!-- BEGIN GENERATIVE -->', '<!-- END GENERATIVE -->', buildTable(generativeProjects));
fs.writeFileSync(ROOT_README, rootContent);

console.log(`Updated README: ${projects.length} total projects, ${generativeProjects.length} generative.`);
