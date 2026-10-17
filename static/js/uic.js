/* ══════════════════════════════════════════════════════════════
   UIC — JavaScript (repris de la maquette d'origine, sans routeur SPA).
   Aucun code inline : compatible avec la Content-Security-Policy.
══════════════════════════════════════════════════════════════ */
(function () {
  'use strict';
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ── Toast ── */
  function showToast(msg, type) {
    var t = $('#toast'); if (!t) return;
    t.textContent = msg; t.className = 'toast ' + (type || 'ok') + ' show';
    clearTimeout(showToast._t);
    showToast._t = setTimeout(function () { t.classList.remove('show'); }, 4500);
  }
  /* Messages Django → toast */
  var firstMsg = $('.dj-msg');
  if (firstMsg) showToast(firstMsg.textContent, firstMsg.dataset.type === 'error' ? 'err' : 'ok');

  /* ── Splash (une seule fois par session, page d'accueil) ── */
  var splash = $('#splash'), stu = $('#student-img'), stuWrap = $('#hero-student');
  function revealStudent() {
    if (!stu) return;
    stu.classList.add('visible');
    setTimeout(function () { stu.classList.add('floating'); if (stuWrap) stuWrap.classList.add('glow'); }, 1200);
  }
  if (splash) {
    var seen = false;
    // Le splash s'affiche à chaque chargement de l'accueil (arrivée, lien, rechargement, téléphone compris).
    // Il est sauté seulement au retour arrière/avant du navigateur, pour ne pas gêner la navigation.
    try {
      var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
      seen = !!nav && nav.type === 'back_forward';
    } catch (e) {}
    if (seen) { splash.remove(); revealStudent(); }
    else {
      document.body.style.overflow = 'hidden';
      var loaded = false, elapsed = false;
      var tryHide = function () {
        if (!(loaded && elapsed)) return;
        splash.classList.add('out'); document.body.style.overflow = '';
        try { sessionStorage.setItem('uic_splash', '1'); } catch (e) {}
        setTimeout(function () { splash.style.display = 'none'; revealStudent(); }, 950);
      };
      window.addEventListener('load', function () { loaded = true; tryHide(); });
      setTimeout(function () { elapsed = true; tryHide(); }, 3200);
    }
  } else { revealStudent(); }

  /* ── Barre de progression ── */
  var pbar = $('#pbar');
  /* ── Header qui se masque / apparaît ── */
  var hdr = $('#site-header'), lastY = 0;
  window.addEventListener('scroll', function () {
    var y = window.scrollY;
    if (pbar) pbar.style.width = Math.min(y / Math.max(document.body.scrollHeight - window.innerHeight, 1) * 100, 100) + '%';
    if (hdr) { hdr.classList.toggle('scrolled', y > 30); hdr.classList.toggle('hidden', y > lastY && y > 200); }
    lastY = y;
  }, { passive: true });

  /* ── Burger ── */
  var burger = $('#burger'), menu = $('#nav-menu');
  if (burger && menu) {
    burger.addEventListener('click', function () {
      burger.classList.toggle('open'); menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', menu.classList.contains('open'));
    });
    $$('a', menu).forEach(function (a) { a.addEventListener('click', function () { menu.classList.remove('open'); burger.classList.remove('open'); }); });
  }

  /* ── Apparitions au scroll ── */
  var rev = $$('.reveal');
  if ('IntersectionObserver' in window) {
    var revIO = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); revIO.unobserve(e.target); } });
    }, { threshold: 0.1 });
    rev.forEach(function (el) { revIO.observe(el); });
  } else { rev.forEach(function (el) { el.classList.add('in'); }); }

  /* ── Compteurs animés ── */
  function easeOut(t) { return 1 - Math.pow(1 - t, 3); }
  function animCounter(el) {
    var target = +el.dataset.target, suffix = el.dataset.suffix || '', t0 = performance.now(), dur = 1800;
    (function tick(now) {
      var p = Math.min((now - t0) / dur, 1);
      el.textContent = Math.round(easeOut(p) * target).toLocaleString('fr-FR') + suffix;
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  }
  var counters = $$('[data-target]');
  if ('IntersectionObserver' in window) {
    var cIO = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { animCounter(e.target); cIO.unobserve(e.target); } });
    }, { threshold: 0.5 });
    counters.forEach(function (el) { cIO.observe(el); });
  } else { counters.forEach(function (el) { el.textContent = (+el.dataset.target).toLocaleString('fr-FR') + (el.dataset.suffix || ''); }); }

  /* ── Filtre des filières : niveau + recherche (fonctionne quel que soit le nombre de formations) ── */
  (function () {
    var grid = $('#fgrid'); if (!grid) return;
    var cards = $$('.fcard', grid), search = $('#fil-search'), count = $('#fil-count'), empty = $('#fil-empty');
    var level = 'all';
    function norm(t) { return (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
    function apply() {
      var q = norm(search ? search.value.trim() : ''), n = 0;
      cards.forEach(function (c) {
        var okLv = level === 'all' || (c.dataset.lv || '').split(' ').indexOf(level) !== -1;
        var okQ = !q || norm(c.dataset.nom).indexOf(q) !== -1;
        c.hidden = !(okLv && okQ); if (!c.hidden) n++;
      });
      if (count) count.textContent = n + ' formation' + (n > 1 ? 's' : '');
      if (empty) empty.hidden = n !== 0 || !cards.length;
    }
    $$('.flt').forEach(function (btn) {
      btn.addEventListener('click', function () {
        $$('.flt').forEach(function (b) { b.classList.remove('on'); });
        btn.classList.add('on'); level = btn.dataset.f; apply();
      });
    });
    if (search) search.addEventListener('input', apply);
  })();

  /* ── Catalogue des formations : école + niveau + recherche ── */
  (function () {
    var cat = $('#fcat'); if (!cat) return;
    var cards = $$('.ccard', cat), groups = $$('.fgroup', cat);
    var search = $('#fil-search'), count = $('#fil-count'), empty = $('#fil-empty');
    var level = 'all', pole = 'all';
    function norm(t) { return (t || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
    function apply() {
      var q = norm(search ? search.value.trim() : ''), n = 0;
      cards.forEach(function (c) {
        var okLv = level === 'all' || (c.dataset.lv || '').split(' ').indexOf(level) !== -1;
        var okP = pole === 'all' || c.dataset.pole === pole;
        var okQ = !q || norm(c.dataset.nom).indexOf(q) !== -1;
        c.hidden = !(okLv && okP && okQ); if (!c.hidden) n++;
      });
      groups.forEach(function (g) { g.hidden = !$$('.ccard:not([hidden])', g).length; });
      if (count) count.textContent = n + ' formation' + (n > 1 ? 's' : '');
      if (empty) empty.hidden = n !== 0 || !cards.length;
    }
    function bind(sel, attr, set) {
      $$(sel).forEach(function (btn) {
        btn.addEventListener('click', function () {
          $$(sel).forEach(function (b) { b.classList.remove('on'); });
          btn.classList.add('on'); set(btn.dataset[attr]); apply();
        });
      });
    }
    bind('.flt[data-f]', 'f', function (v) { level = v; });
    bind('.flt[data-p]', 'p', function (v) { pole = v; });
    if (search) search.addEventListener('input', apply);
  })();

  /* ── Admission : accordéon 3 étapes ── */
  function openStep(id) {
    $$('.acc-body').forEach(function (b) { b.classList.remove('open'); });
    $$('.acc-trigger').forEach(function (t) { t.classList.remove('active'); });
    var b = document.getElementById(id), t = $('[data-acc="' + id + '"]');
    if (b) b.classList.add('open'); if (t) t.classList.add('active');
  }
  $$('.acc-trigger').forEach(function (tr) {
    tr.addEventListener('click', function () {
      var id = tr.dataset.acc, body = document.getElementById(id);
      var isOpen = body.classList.contains('open');
      $$('.acc-body').forEach(function (b) { b.classList.remove('open'); });
      $$('.acc-trigger').forEach(function (t) { t.classList.remove('active'); });
      if (!isOpen) { body.classList.add('open'); tr.classList.add('active'); }
    });
  });
  function stepValid(stepId) {
    var ok = true;
    $$('input[required], select[required]', document.getElementById(stepId)).forEach(function (inp) {
      if (!inp.value.trim() || !inp.checkValidity()) {
        ok = false; inp.classList.add('is-err');
        setTimeout(function () { inp.classList.remove('is-err'); }, 2500);
      }
    });
    return ok;
  }
  function val(id) { var e = document.getElementById(id); return e ? e.value : ''; }
  function selText(id) { var e = document.getElementById(id); return e && e.selectedIndex > -1 ? e.options[e.selectedIndex].text : ''; }
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function buildRecap() {
    var rc = $('#recap-content'); if (!rc) return;
    rc.innerHTML = '<b>Nom :</b> ' + esc(val('fPrenom') + ' ' + val('fNom')) + '<br><b>Email :</b> ' + esc(val('fEmail')) +
      '<br><b>Filière :</b> ' + esc(selText('fFiliere')) + '<br><b>Niveau :</b> ' + esc(selText('fNiveau'));
  }
  $$('[data-next]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var from = btn.dataset.from, next = btn.dataset.next;
      if (!stepValid(from)) { showToast('Veuillez compléter tous les champs.', 'err'); return; }
      var num = from.replace('step', ''), done = document.getElementById('done' + num);
      if (done) { done.textContent = 'Étape ' + num + ' complétée ✓'; done.classList.add('show'); }
      if (from === 'step2') buildRecap();
      openStep(next);
    });
  });
  var form = $('#admission-form');
  if (form) {
    buildRecap();
    form.addEventListener('submit', function (e) {
      if (!stepValid('step1')) { e.preventDefault(); openStep('step1'); showToast('Veuillez compléter vos informations.', 'err'); return; }
      if (!stepValid('step2')) { e.preventDefault(); openStep('step2'); showToast('Veuillez choisir une filière et un niveau.', 'err'); return; }
      var b = $('#btnSubmit'); if (b) { b.textContent = '⏳ Envoi en cours...'; b.disabled = true; }
    });
  }

  /* ── FAQ (accordéon) ── */
  $$('.faq-q').forEach(function (q) {
    q.addEventListener('click', function () {
      q.classList.toggle('open'); q.nextElementSibling.classList.toggle('open');
      q.setAttribute('aria-expanded', q.classList.contains('open'));
    });
  });
})();
