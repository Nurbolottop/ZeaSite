/* ZEA admin — живое превью цвета и иконки в форме редактирования */
(function () {
  var COLORS = {
    indigo: '#6366f1', purple: '#a855f7', cyan: '#06b6d4',
    blue: '#3b82f6', green: '#22c55e', pink: '#ec4899',
    orange: '#f97316', red: '#ef4444', yellow: '#eab308'
  };

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    /* ── Превью цвета ── */
    document.querySelectorAll('select[name="color"]').forEach(function (sel) {
      var sw = document.createElement('span');
      sw.style.cssText =
        'display:inline-block;width:24px;height:24px;border-radius:6px;' +
        'margin-left:12px;vertical-align:middle;border:1px solid rgba(255,255,255,.25);' +
        'box-shadow:0 1px 4px rgba(0,0,0,.3);';
      sel.parentNode.insertBefore(sw, sel.nextSibling);
      function upd() { sw.style.background = COLORS[sel.value] || '#888'; }
      sel.addEventListener('change', upd);
      upd();
    });

    /* ── Превью иконки (lucide) — работает для select и input ── */
    document.querySelectorAll('select[name="icon"], input[name="icon"]').forEach(function (fld) {
      var box = document.createElement('span');
      box.style.cssText =
        'display:inline-flex;align-items:center;justify-content:center;' +
        'width:40px;height:40px;border-radius:8px;margin-left:12px;' +
        'vertical-align:middle;background:rgba(99,102,241,.18);color:#a5b4fc;';
      fld.parentNode.insertBefore(box, fld.nextSibling);
      function upd() {
        var name = (fld.value || '').trim() || 'help-circle';
        box.innerHTML = '<i data-lucide="' + name + '"></i>';
        if (window.lucide) lucide.createIcons();
      }
      fld.addEventListener('input', upd);
      fld.addEventListener('change', upd);
      upd();
    });
  });
})();
