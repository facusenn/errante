// Presupuestador: preview del estimado en vivo.
// Refleja la misma lógica que el backend (services/estimator.py):
// precio base por tamaño × multiplicador por zona, con mínimo de sesión.
(function () {
    var CFG = window.QUOTE_JS_CONFIG || {};
    var sizeSelect = document.getElementById('q-size');
    var zoneSelect = document.getElementById('q-zone');
    var box = document.getElementById('q-estimate');
    var hint = document.getElementById('q-estimate-hint');

    function fmt(n) {
        try {
            return new Intl.NumberFormat('es-AR', {
                style: 'currency', currency: 'ARS', maximumFractionDigits: 0
            }).format(n);
        } catch (e) {
            return '$ ' + Math.round(n).toLocaleString('es-AR');
        }
    }

    function recalc() {
        if (!box || !sizeSelect || !zoneSelect) return;
        var size = sizeSelect.value;
        var selected = zoneSelect.options[zoneSelect.selectedIndex];
        var zoneKey = selected ? (selected.getAttribute('data-key') || '') : '';

        if (!size || !zoneKey) {
            box.innerHTML = '<span class="q-placeholder">Elegí tamaño y zona para ver el estimado</span>';
            if (hint) hint.textContent = '';
            return;
        }

        var base = (CFG.sizes && CFG.sizes[size]) || 0;
        var mult = (CFG.zones && CFG.zones[zoneKey] !== undefined) ? CFG.zones[zoneKey] : 1.0;
        var subtotal = base * mult;
        var minimum = CFG.min_price || 0;
        var total = Math.max(subtotal, minimum);
        var low = Math.round(total * 0.90);
        var high = Math.round(total * 1.15);

        box.innerHTML = fmt(low) + ' – ' + fmt(high);
        if (hint) {
            var notes = ['Precio final según detalles del diseño.'];
            if (subtotal < minimum) notes.unshift('Aplica mínimo de sesión (' + fmt(minimum) + ').');
            hint.textContent = '· ' + notes.join(' ');
        }
    }

    if (sizeSelect) sizeSelect.addEventListener('change', recalc);
    if (zoneSelect) zoneSelect.addEventListener('change', recalc);

    recalc();
})();
