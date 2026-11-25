// Agrega filas vacías al formset de artículos usando el <template> que genera Django.
(function () {
  var boton = document.getElementById('agregar-fila');
  var plantilla = document.getElementById('fila-vacia');
  var cuerpo = document.getElementById('detalles-body');
  var total = document.getElementById('id_detalles-TOTAL_FORMS');
  if (!boton || !plantilla || !cuerpo || !total) return;

  boton.addEventListener('click', function () {
    var indice = parseInt(total.value, 10);
    var html = plantilla.innerHTML.replace(/__prefix__/g, indice);
    cuerpo.insertAdjacentHTML('beforeend', html);
    total.value = indice + 1;
    var selects = cuerpo.querySelectorAll('tr:last-child select');
    if (selects.length) selects[0].focus();
  });
})();
