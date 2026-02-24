/* Awesome Seedance Gallery */
(function () {
  'use strict';

  let DATA = { meta: {}, items: [] };
  let filtered = [];

  const $ = (s) => document.querySelector(s);
  const grid = $('#grid');
  const stats = $('#stats');
  const empty = $('#empty');
  const modal = $('#modal');
  const modalContent = $('#modal-content');
  const searchInput = $('#search');
  const filterPlatform = $('#filter-platform');
  const filterTag = $('#filter-tag');
  const filterType = $('#filter-type');
  const sortBy = $('#sort-by');

  /* --- Load data --- */
  fetch('data.json')
    .then((r) => r.json())
    .then((d) => {
      DATA = d;
      initFilters();
      applyFilters();
    })
    .catch((e) => {
      stats.textContent = 'Failed to load data.';
      console.error(e);
    });

  /* --- Populate filter dropdowns --- */
  function initFilters() {
    const { platforms, tags } = DATA.meta;
    platforms.forEach((p) => {
      const o = document.createElement('option');
      o.value = p; o.textContent = p;
      filterPlatform.appendChild(o);
    });
    tags.forEach((t) => {
      const o = document.createElement('option');
      o.value = t; o.textContent = t;
      filterTag.appendChild(o);
    });
  }

  /* --- Filter & Sort --- */
  function applyFilters() {
    const q = searchInput.value.toLowerCase().trim();
    const plat = filterPlatform.value;
    const tag = filterTag.value;
    const type = filterType.value;
    const sort = sortBy.value;

    filtered = DATA.items.filter((item) => {
      if (plat && item.platform !== plat) return false;
      if (tag && !(item.tags || []).includes(tag)) return false;
      if (type && item.type !== type) return false;
      if (q) {
        const hay = [
          item.title, item.author,
          ...(item.tags || []),
          item.summary_zh || '', item.summary_en || ''
        ].join(' ').toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      if (sort === 'title') return (a.title || '').localeCompare(b.title || '');
      const ka = sort === 'published_at' ? 'published_at' : 'added_at';
      return (b[ka] || '').localeCompare(a[ka] || '');
    });

    render();
  }

  /* --- Render grid --- */
  function render() {
    stats.textContent = `${filtered.length} of ${DATA.meta.total} cases`;
    empty.style.display = filtered.length ? 'none' : 'block';
    grid.innerHTML = '';

    filtered.forEach((item) => {
      const card = document.createElement('div');
      card.className = 'card';
      card.onclick = () => openModal(item);
      card.innerHTML = renderCard(item);
      grid.appendChild(card);
    });
  }

  function renderCard(item) {
    const thumb = getThumb(item);
    const tags = (item.tags || []).slice(0, 4).map((t) => `<span class="tag">${esc(t)}</span>`).join('');
    const date = formatDate(item.added_at);
    return `
      <div class="card-thumb">${thumb}</div>
      <div class="card-body">
        <div class="card-title">${esc(item.title)}</div>
        <div class="card-author">${esc(item.author || 'Unknown')}</div>
        <div class="card-tags">${tags}</div>
        ${date ? `<div class="card-date">${date}</div>` : ''}
      </div>`;
  }

  function getThumb(item) {
    const p = item.preview || {};
    const poster = p.poster || '';
    const isSvgPlaceholder = poster.endsWith('.svg');
    // Prefer real preview URL over SVG placeholders
    if (p.ok && p.url && (isSvgPlaceholder || !poster)) {
      if (p.kind === 'video') {
        return `<img src="${esc(p.url)}" alt="" loading="lazy" onerror="this.parentNode.innerHTML='<div class=\\'placeholder-thumb\\'>🎬</div>'"><span class="play-badge">▶</span>`;
      }
      return `<img src="${esc(p.url)}" alt="" loading="lazy" onerror="this.parentNode.innerHTML='<div class=\\'placeholder-thumb\\'>🎬</div>'">`;
    }
    if (poster && !isSvgPlaceholder) {
      return `<img src="${esc(poster)}" alt="" loading="lazy"><span class="play-badge">▶</span>`;
    }
    return `<div class="placeholder-thumb">🎬</div>`;
  }

  /* --- Modal --- */
  function openModal(item) {
    const p = item.preview || {};
    let mediaHtml = '';
    if (p.ok && p.url && p.kind === 'video') {
      mediaHtml = `<video src="${esc(p.url)}" controls autoplay muted style="width:100%;border-radius:var(--radius-sm);margin-bottom:1rem"></video>`;
    } else if (p.ok && p.url) {
      mediaHtml = `<img src="${esc(p.url)}" alt="" style="width:100%;border-radius:var(--radius-sm);margin-bottom:1rem">`;
    }

    const summaryZh = item.summary_zh || '';
    const summaryEn = item.summary_en || '';
    const summary = summaryZh && summaryEn && summaryZh !== summaryEn
      ? `${esc(summaryEn)}<br><span style="color:var(--text-muted)">${esc(summaryZh)}</span>`
      : esc(summaryEn || summaryZh);

    const tags = (item.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join(' ');

    modalContent.innerHTML = `
      <div class="modal-header">
        <h2>${esc(item.title)}</h2>
        <button class="modal-close" onclick="document.getElementById('modal').style.display='none'">&times;</button>
      </div>
      <div class="modal-body">
        ${mediaHtml}
        <div class="detail-row"><span class="detail-label">Author</span><span class="detail-value">${esc(item.author || 'Unknown')}</span></div>
        <div class="detail-row"><span class="detail-label">Platform</span><span class="detail-value">${esc(item.platform || 'unknown')}</span></div>
        <div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">${esc(item.type || '')}</span></div>
        <div class="detail-row"><span class="detail-label">Added</span><span class="detail-value">${formatDate(item.added_at) || '—'}</span></div>
        ${item.published_at ? `<div class="detail-row"><span class="detail-label">Published</span><span class="detail-value">${formatDate(item.published_at)}</span></div>` : ''}
        <div class="detail-row"><span class="detail-label">Tags</span><span class="detail-value">${tags}</span></div>
        ${summary ? `<div class="summary-block">${summary}</div>` : ''}
        <div class="action-row">
          <a href="${esc(item.url)}" target="_blank" rel="noopener" class="btn-primary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            View original
          </a>
        </div>
      </div>`;
    modal.style.display = 'flex';
  }

  /* --- Helpers --- */
  function esc(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function formatDate(iso) {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch { return ''; }
  }

  /* --- Events --- */
  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyFilters, 200);
  });
  filterPlatform.addEventListener('change', applyFilters);
  filterTag.addEventListener('change', applyFilters);
  filterType.addEventListener('change', applyFilters);
  sortBy.addEventListener('change', applyFilters);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.style.display = 'none';
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') modal.style.display = 'none';
  });

})();

