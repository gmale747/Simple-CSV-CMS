/* Shared data layer: loads data/posts.csv (the "database") with PapaParse.
 * Columns: post-name, post-category, post-header, post-body, post-main-image, post-url
 * All CSV content is written to the page with textContent (never innerHTML) to prevent XSS. */
'use strict';

const BlogData = (() => {
  const CSV_PATH = 'data/posts.csv';
  const REQUIRED = ['post-name', 'post-category', 'post-header', 'post-body', 'post-main-image', 'post-url'];

  function load() {
    return fetch(CSV_PATH, { cache: 'no-store' })
      .then((res) => {
        if (!res.ok) throw new Error(`Could not load ${CSV_PATH} (HTTP ${res.status})`);
        return res.text();
      })
      .then((text) => {
        const parsed = Papa.parse(text, { header: true, skipEmptyLines: true });
        const missing = REQUIRED.filter((c) => !parsed.meta.fields.includes(c));
        if (missing.length) throw new Error(`posts.csv is missing column(s): ${missing.join(', ')}`);
        return parsed.data.map((row) => ({
          name: row['post-name'].trim(),
          category: row['post-category'].trim(),
          header: row['post-header'].trim(),
          body: row['post-body'].trim(),
          image: safeImagePath(row['post-main-image'].trim()),
          slug: row['post-url'].trim(),
        }));
      });
  }

  // Only allow local image paths (blocks javascript:, data:, and remote URLs from the CSV).
  function safeImagePath(path) {
    return /^images\/[\w.-]+\.(svg|png|jpe?g|webp)$/i.test(path) ? path : 'images/placeholder.svg';
  }

  function postLink(slug) {
    return `post.html?slug=${encodeURIComponent(slug)}`;
  }

  function el(tag, opts = {}, children = []) {
    const node = document.createElement(tag);
    if (opts.className) node.className = opts.className;
    if (opts.text !== undefined) node.textContent = opts.text;
    if (opts.attrs) Object.entries(opts.attrs).forEach(([k, v]) => node.setAttribute(k, v));
    children.forEach((c) => node.appendChild(c));
    return node;
  }

  function showError(message) {
    const box = document.getElementById('error');
    box.textContent = `${message}. If you opened this file directly, serve the folder over HTTP (see README).`;
    box.classList.remove('d-none');
  }

  return { load, postLink, el, showError };
})();
