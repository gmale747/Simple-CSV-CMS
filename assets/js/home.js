/* Home page: visual summary of all articles (stats, category breakdown, filterable card grid). */
'use strict';

(() => {
  const { el } = BlogData;
  let posts = [];
  let activeCategory = 'All';

  BlogData.load()
    .then((data) => {
      posts = data;
      renderStats();
      renderCategoryBars();
      renderFilters();
      renderGrid();
      document.getElementById('search').addEventListener('input', renderGrid);
    })
    .catch((err) => BlogData.showError(err.message));

  function countByCategory() {
    return posts.reduce((acc, p) => ((acc[p.category] = (acc[p.category] || 0) + 1), acc), {});
  }

  function renderStats() {
    const counts = countByCategory();
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    const stats = [
      ['Articles', posts.length],
      ['Categories', Object.keys(counts).length],
      ['Largest category', top ? top[0] : '-'],
    ];
    const wrap = document.getElementById('stats');
    stats.forEach(([label, value]) => {
      wrap.appendChild(
        el('div', { className: 'col-6 col-md-3' }, [
          el('div', { className: 'stat-tile' }, [
            el('div', { className: 'stat-value', text: String(value) }),
            el('div', { className: 'stat-label', text: label }),
          ]),
        ])
      );
    });
  }

  function renderCategoryBars() {
    const counts = countByCategory();
    const max = Math.max(...Object.values(counts));
    const wrap = document.getElementById('category-bars');
    Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .forEach(([cat, n]) => {
        const bar = el('div', { className: 'progress-bar', attrs: { role: 'presentation' } });
        bar.style.width = `${(n / max) * 100}%`;
        wrap.appendChild(
          el('div', { className: 'cat-row' }, [
            el('div', { className: 'd-flex justify-content-between small fw-semibold' }, [
              el('span', { text: cat }),
              el('span', { text: `${n} article${n > 1 ? 's' : ''}` }),
            ]),
            el('div', { className: 'progress', attrs: { 'aria-label': `${cat}: ${n} articles` } }, [bar]),
          ])
        );
      });
  }

  function renderFilters() {
    const wrap = document.getElementById('filters');
    ['All', ...Object.keys(countByCategory()).sort()].forEach((cat) => {
      const btn = el('button', {
        className: 'btn btn-sm btn-outline-dark filter-btn',
        text: cat,
        attrs: { type: 'button', 'aria-pressed': String(cat === activeCategory) },
      });
      btn.addEventListener('click', () => {
        activeCategory = cat;
        wrap.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.textContent === cat)));
        renderGrid();
      });
      wrap.appendChild(btn);
    });
  }

  function renderGrid() {
    const q = document.getElementById('search').value.trim().toLowerCase();
    const grid = document.getElementById('post-grid');
    grid.replaceChildren();
    const shown = posts.filter(
      (p) =>
        (activeCategory === 'All' || p.category === activeCategory) &&
        (!q || `${p.name} ${p.header} ${p.category}`.toLowerCase().includes(q))
    );
    document.getElementById('result-count').textContent = `(${shown.length} of ${posts.length})`;
    shown.forEach((p) => {
      grid.appendChild(
        el('div', { className: 'col-sm-6 col-lg-4' }, [
          el('article', { className: 'card h-100 post-card' }, [
            el('img', { className: 'card-img-top', attrs: { src: p.image, alt: '', loading: 'lazy' } }),
            el('div', { className: 'card-body d-flex flex-column' }, [
              el('span', { className: 'badge category-badge align-self-start mb-2', text: p.category }),
              el('h3', { className: 'h5 card-title' }, [
                el('a', { className: 'stretched-link', text: p.name, attrs: { href: BlogData.postLink(p.slug) } }),
              ]),
              el('p', { className: 'card-text text-body-secondary', text: p.header }),
            ]),
          ]),
        ])
      );
    });
    if (!shown.length) grid.appendChild(el('p', { className: 'text-body-secondary', text: 'No articles match your search.' }));
  }
})();
