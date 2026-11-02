// Leaderboard column sort. Delegated from document so it survives instant navigation; the server renders the
// default order, so the board reads correctly without this script.
(function () {
  function value(row, key) {
    var v = row.dataset[key];
    return v === undefined || v === '' ? null : parseFloat(v);
  }
  function sortBoard(board, key) {
    var rows = Array.prototype.slice.call(board.querySelectorAll(':scope > details.ob-row'));
    rows.sort(function (a, b) {
      var va = value(a, key), vb = value(b, key);
      if (va === null && vb !== null) return 1;
      if (vb === null && va !== null) return -1;
      return ((vb || 0) - (va || 0)) || (value(b, 'standard') - value(a, 'standard'));
    });
    var anchor = board.querySelector(':scope > .ob-queued');
    var n = 0;
    rows.forEach(function (r) {
      board.insertBefore(r, anchor);
      r.querySelector('.ob-rank').textContent = value(r, key) === null ? '·' : String(++n);
    });
    board.dataset.sort = key;
    board.querySelectorAll('.ob-sort').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.dataset.key === key));
    });
  }
  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.ob-board .ob-sort');
    if (btn) sortBoard(btn.closest('.ob-board'), btn.dataset.key);
  });
})();
