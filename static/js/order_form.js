// static/js/order_form.js
// Card-based item picker + summary + formset mapper
document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('cards-grid');
  const summaryList = document.getElementById('summary-list');
  const summaryTotal = document.getElementById('summary-total');
  const summaryTable = document.getElementById('summary-table');
  const tableInput =
    document.getElementById('id_table_number') ||
    document.querySelector('[name="table_number"]');
  const formEl = document.getElementById('order-form');

  // Management form
  const totalFormsInput = document.querySelector('[name$="-TOTAL_FORMS"]');
  if (!grid || !summaryList || !summaryTotal || !totalFormsInput || !formEl) return;

  function money(n){ return '₱' + (Math.round(n*100)/100).toFixed(2); }

  function updateCardState(card){
    const check = card.querySelector('.card-check');
    const qty = card.querySelector('.qty-input');
    const badge = card.querySelector('.selected-badge');
    qty.disabled = !check.checked;
    if(check.checked){
      card.classList.add('selected');
      badge.style.display = 'block';
    }else{
      card.classList.remove('selected');
      badge.style.display = 'none';
      qty.value = 1;
    }
  }

  function rebuildSummary(){
    summaryList.innerHTML = '';
    let total = 0;
    [...grid.querySelectorAll('.card')].forEach(card=>{
      const checked = card.querySelector('.card-check').checked;
      if(!checked) return;
      const name = card.querySelector('.item-title').textContent.trim();
      const price = parseFloat(card.dataset.price || '0');
      const qty = parseInt(card.querySelector('.qty-input').value || '1',10);
      const li = document.createElement('li');
      li.className = 'summary-row';
      li.innerHTML = `<span>${name} × ${qty}</span><strong>${money(price*qty)}</strong>`;
      summaryList.appendChild(li);
      total += price*qty;
    });
    summaryTotal.textContent = money(total);
    summaryTable.textContent = tableInput && tableInput.value ? `Table ${tableInput.value}` : '—';
  }

  // Normalize table code: letters, digits and single spaces; uppercase
  if (tableInput) {
    tableInput.addEventListener('input', () => {
      const raw = tableInput.value;
      const cleaned = raw
        .replace(/[^a-zA-Z0-9 ]+/g, '')
        .replace(/\s+/g, ' ')
        .trim()
        .toUpperCase()
        .slice(0, 32);
      if (cleaned !== raw) {
        const pos = tableInput.selectionStart || cleaned.length;
        tableInput.value = cleaned;
        try { tableInput.setSelectionRange(pos, pos); } catch(e) {}
      }
      rebuildSummary();
    }, { passive: true });
  }

  // Checkbox changes (when user clicks the checkbox itself)
  grid.addEventListener('change', (e)=>{
    if(e.target.classList.contains('card-check')){
      updateCardState(e.target.closest('.card'));
      rebuildSummary();
    }
  });

  // Unified click handler:
  // - click minus/plus => adjust qty
  // - click on qty input or checkbox => native behavior
  // - click anywhere else in the card => toggle selection
  grid.addEventListener('click', (e) => {
    const btn = e.target.closest('.qty-btn');
    const qtyInputEl = e.target.closest('.qty-input');
    const checkboxEl = e.target.closest('.card-check');

    // 1) Quantity buttons
    if (btn) {
      const card = btn.closest('.card');
      const input = card.querySelector('.qty-input');
      if (input.disabled) return; // not selected yet
      let v = parseInt(input.value || '1', 10);
      if (btn.dataset.action === 'minus' && v > 1) v--;
      if (btn.dataset.action === 'plus') v++;
      input.value = v;
      rebuildSummary();
      return;
    }

    // 2) Let qty input & checkbox act normally
    if (qtyInputEl || checkboxEl) return;

    // 3) Toggle by clicking the card anywhere else
    const card = e.target.closest('.card');
    if (card) {
      const check = card.querySelector('.card-check');
      check.checked = !check.checked;
      updateCardState(card);
      rebuildSummary();
    }
  });

  // Manual typing in quantity input
  grid.addEventListener('input', (e)=>{
    if(e.target.classList.contains('qty-input')) rebuildSummary();
  });

  // Initialize visuals
  grid.querySelectorAll('.card').forEach(updateCardState);
  rebuildSummary();

  // BEFORE SUBMIT: map selected cards -> formset rows
  formEl.addEventListener('submit', (e)=>{
    const selected = [...grid.querySelectorAll('.card')].filter(c=>c.querySelector('.card-check').checked);

    if(selected.length === 0){
      e.preventDefault();
      alert('Please select at least one item.');
      return;
    }

    const mgmtPrefix = totalFormsInput.name.replace('-TOTAL_FORMS','');
    const maxRows = parseInt(totalFormsInput.value,10);

    if(selected.length > maxRows){
      e.preventDefault();
      alert(`Too many items selected (${selected.length}). Increase formset 'extra' to at least ${selected.length}.`);
      return;
    }

    for(let i=0;i<maxRows;i++){
      const rowPrefix = `${mgmtPrefix}-${i}`;
      const sel = document.querySelector(`[name="${rowPrefix}-menu_item"]`);
      const qty = document.querySelector(`[name="${rowPrefix}-quantity"]`);
      const notes = document.querySelector(`[name="${rowPrefix}-notes"]`);
      const del = document.querySelector(`[name="${rowPrefix}-DELETE"]`);

      if(i < selected.length){
        const card = selected[i];
        const id = card.dataset.id;
        const qv = parseInt(card.querySelector('.qty-input').value || '1',10);
        if(sel) sel.value = id;
        if(qty) qty.value = qv;
        if(notes) notes.value = '';
        if(del) del.checked = false;
      }else{
        if(del) del.checked = true;
        if(sel) sel.value = '';
        if(qty) qty.value = '';
        if(notes) notes.value = '';
      }
    }
  });
});
