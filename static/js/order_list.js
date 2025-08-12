// Client-side search/filter for Orders list
document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('order-search');
  const table = document.getElementById('orders-table');
  if (!input || !table) return;

  const rows = Array.from(table.querySelectorAll('tbody tr'));
  const counter = document.querySelector('.count-pill');

  function filter() {
    const q = input.value.trim().toLowerCase();
    let visible = 0;

    rows.forEach(tr => {
      const hay =
        tr.getAttribute('data-search')?.toLowerCase() ||
        tr.textContent.toLowerCase();
      const show = !q || hay.includes(q);
      tr.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (counter) counter.textContent = `${visible} shown`;
  }

  input.addEventListener('input', filter, { passive: true });
});
