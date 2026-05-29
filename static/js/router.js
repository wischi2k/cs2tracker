// SPA: lädt Detail rechts ohne Voll-Reload; Fallback auf echte Navigation bleibt erhalten
(function () {
  const detail = document.getElementById('detail');
  if (!detail) return;

  async function loadDetail(url) {
    const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
    if (!res.ok) throw new Error(res.status);
    detail.innerHTML = await res.text();
  }

  document.addEventListener('click', async (ev) => {
    const a = ev.target.closest('a.item-link');
    if (!a) return;
    ev.preventDefault();
    try {
      await loadDetail(a.href);
      history.pushState(null, '', a.href);
    } catch {
      window.location.href = a.href;
    }
  });

  window.addEventListener('popstate', () => {
    loadDetail(window.location.href).catch(()=>{});
  });
})();
