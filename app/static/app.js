document.addEventListener('DOMContentLoaded', function() {
  let loanIndex = 0;
  const addBtn = document.getElementById('add-loan');
  const loansDiv = document.getElementById('loans');
  // Set loanIndex to max existing index + 1
  const existingRows = loansDiv.querySelectorAll('.loan-row');
  if (existingRows.length > 0) {
    loanIndex = Array.from(existingRows).reduce((maxIdx, row) => {
      const input = row.querySelector('input[name^="loan_amount_"]');
      if (input) {
        const idx = parseInt(input.name.split('_').pop(), 10);
        return Math.max(maxIdx, idx);
      }
      return maxIdx;
    }, 0) + 1;
  } else {
    loanIndex = 1;
  }
  if (addBtn) {
    addBtn.addEventListener('click', function() {
      const row = document.createElement('div');
      row.className = 'loan-row';
      row.innerHTML = `
        <label>Amount ($)<input type="number" name="loan_amount_${loanIndex}" min="0" step="0.01" required></label>
        <label>APR (%)<input type="number" name="apr_${loanIndex}" min="0" max="100" step="0.01" required></label>
        <label>Term (months)<input type="number" name="term_months_${loanIndex}" min="1" step="1" required></label>
        <button type="button" class="remove-loan" style="margin-left:1rem;margin-top:.5rem;background:#e74c3c;color:#fff;border:none;padding:.3rem .7rem;border-radius:4px;cursor:pointer">Remove</button>
      `;
      loansDiv.appendChild(row);
      loanIndex++;
    });
  }
  loansDiv.addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-loan')) {
      const row = e.target.closest('.loan-row');
      if (row) row.remove();
    }
  });
});
