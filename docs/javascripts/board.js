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
    // collapsed view ranks only each model's best build; "Show all builds" ranks every build
    var all = board.classList.contains('ob-all');
    var n = 0;
    rows.forEach(function (r) {
      board.insertBefore(r, anchor);
      var ranked = value(r, key) !== null && (all || !r.classList.contains('ob-alt'));
      r.querySelector('.ob-rank').textContent = ranked ? String(++n) : '·';
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
  document.addEventListener('change', function (e) {
    var box = e.target.closest && e.target.closest('.ob-board .ob-all-builds');
    if (!box) return;
    var board = box.closest('.ob-board');
    board.classList.toggle('ob-all', box.checked);
    sortBoard(board, board.dataset.sort);
  });
})();
