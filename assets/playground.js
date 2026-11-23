/* Playground directory: color mode buttons, tag filters and preview videos.
   Everything here is an enhancement: without JavaScript the page shows every
   project, follows the system color mode and shows still images only.
   Built with assistance from Claude (Anthropic), November 2026. */

(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  // ─── Color modes (same behavior as jasonjames.works) ──────────────────────
  (function colorModes() {
    var tm = window.themeModes, root = document.documentElement;
    var group = document.querySelector('[data-theme-modes]');
    if (!tm || !group) return;
    var buttons = group.querySelectorAll('[data-set-mode]');
    var themeColor = document.querySelector('meta[name="theme-color"]');

    function show() {
      buttons.forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.dataset.setMode === root.dataset.mode));
      });
      if (themeColor) {
        var accent = getComputedStyle(root).getPropertyValue('--accent').trim();
        if (accent) themeColor.setAttribute('content', accent);
      }
    }

    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        root.dataset.mode = b.dataset.setMode;
        try { localStorage.setItem(tm.KEY, b.dataset.setMode); } catch (e) {}
        show();
      });
    });

    // Until the visitor picks a mode, follow the system live
    ['(prefers-color-scheme: dark)', '(prefers-contrast: more)', '(forced-colors: active)']
      .forEach(function (q) {
        window.matchMedia(q).addEventListener('change', function () {
          if (!tm.saved()) { root.dataset.mode = tm.system(); show(); }
        });
      });

    group.hidden = false;
    show();
  })();

  // ─── Tag filters ──────────────────────────────────────────────────────────
  // The choice lives in the URL (?tag=generative) so a filtered view can be linked to.
  (function filters() {
    var panel = document.querySelector('.filters');
    if (!panel) return;
    var buttons = panel.querySelectorAll('[data-filter]');
    var status = document.getElementById('filter-status');
    var projects = document.querySelectorAll('.project');
    var sections = document.querySelectorAll('.listing > section');
    var emptyNote = document.querySelector('.empty-note');
    var resetButtons = document.querySelectorAll('.link-button[data-filter]');

    function apply(tag, announce) {
      var known = Array.prototype.some.call(buttons, function (b) { return b.dataset.filter === tag; });
      if (!known) tag = 'all';

      var shown = 0;
      projects.forEach(function (li) {
        var match = tag === 'all' || (' ' + li.dataset.tags + ' ').indexOf(' ' + tag + ' ') > -1;
        li.hidden = !match;
        if (match) shown++;
      });

      // Pinned hides when nothing in it matches; "everything else" says so instead
      sections.forEach(function (section) {
        var any = section.querySelector('.project:not([hidden])');
        if (section.id === 'pinned') section.hidden = !any;
        else if (emptyNote) emptyNote.hidden = !!any;
      });

      buttons.forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.dataset.filter === tag));
      });

      var url = new URL(window.location.href);
      if (tag === 'all') url.searchParams.delete('tag');
      else url.searchParams.set('tag', tag);
      history.replaceState(null, '', url);

      if (announce && status) {
        status.textContent = tag === 'all'
          ? 'Showing all ' + shown + ' projects.'
          : 'Showing ' + shown + ' of ' + projects.length + ' projects tagged ' + tag + '.';
      }
    }

    buttons.forEach(function (b) {
      b.addEventListener('click', function () { apply(b.dataset.filter, true); });
    });
    resetButtons.forEach(function (b) {
      b.addEventListener('click', function () {
        apply('all', true);
        var first = panel.querySelector('[data-filter="all"]');
        if (first) first.focus();
      });
    });

    panel.hidden = false;
    apply(new URL(window.location.href).searchParams.get('tag') || 'all', false);
  })();

  // ─── Preview videos ───────────────────────────────────────────────────────
  // A still shows by default. Hovering or focusing a card plays its preview
  // (unless the visitor prefers reduced motion); the round button plays or
  // pauses it on purpose, which also works on touch screens. No video bytes
  // load until one of those happens (preload="none").
  (function previews() {
    document.querySelectorAll('.project-media.has-preview').forEach(function (media) {
      var video = media.querySelector('video');
      var button = media.querySelector('.preview-toggle');
      var card = media.closest('.project-card');
      var label = button.querySelector('.visually-hidden');
      var title = label.textContent.replace(/^Play preview of /, '');
      var pinnedOn = false; // the visitor pressed play

      function play() {
        var p = video.play();
        if (p && p.catch) p.catch(function () { stop(); });
      }
      function stop() {
        video.pause();
        media.classList.remove('is-playing');
      }
      function setPressed(on) {
        pinnedOn = on;
        button.setAttribute('aria-pressed', String(on));
        label.textContent = (on ? 'Pause preview of ' : 'Play preview of ') + title;
      }

      video.addEventListener('playing', function () { media.classList.add('is-playing'); });

      button.addEventListener('click', function () {
        setPressed(!pinnedOn);
        if (pinnedOn) play(); else stop();
      });

      function hoverStart() {
        if (!reducedMotion.matches && !pinnedOn) play();
      }
      function hoverEnd(e) {
        if (pinnedOn) return;
        if (e.type === 'focusout' && card.contains(e.relatedTarget)) return;
        if (e.type === 'mouseleave' && card.contains(document.activeElement)) return;
        stop();
      }
      card.addEventListener('mouseenter', hoverStart);
      card.addEventListener('mouseleave', hoverEnd);
      card.addEventListener('focusin', hoverStart);
      card.addEventListener('focusout', hoverEnd);

      button.hidden = false;
    });
  })();
})();
