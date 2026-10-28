/* Article page: renders one post selected by ?slug=<post-url>. */
'use strict';

(() => {
  const { el } = BlogData;
  const slug = new URLSearchParams(window.location.search).get('slug');

  BlogData.load()
    .then((posts) => {
      const post = posts.find((p) => p.slug === slug);
      if (!post) throw new Error('Article not found');

      document.title = `${post.name} | Road Construction Help Center`;
      document.getElementById('crumb').textContent = post.name;
      document.getElementById('post-category').textContent = post.category;
      document.getElementById('post-name').textContent = post.name;
      document.getElementById('post-header').textContent = post.header;
      const img = document.getElementById('post-image');
      img.src = post.image;
      img.alt = `Illustration for ${post.name}`;

      // Body paragraphs are separated by blank lines in the CSV.
      const body = document.getElementById('post-body');
      post.body.split(/\n\s*\n/).forEach((para) => body.appendChild(el('p', { text: para })));

      const related = posts.filter((p) => p.category === post.category && p.slug !== post.slug);
      const list = document.getElementById('related');
      if (!related.length) list.appendChild(el('li', { className: 'text-body-secondary', text: 'No other articles yet.' }));
      related.forEach((p) =>
        list.appendChild(el('li', { className: 'mb-2' }, [el('a', { text: p.name, attrs: { href: BlogData.postLink(p.slug) } })]))
      );
    })
    .catch((err) => {
      document.getElementById('article').classList.add('d-none');
      BlogData.showError(err.message);
    });
})();
