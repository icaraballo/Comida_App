"""La página del visor: HTML, CSS y JS en un único fichero.

Autocontenida a propósito. Sin CDN, sin fuentes remotas, sin una sola petición
de red: estos son datos de estado emocional y pensamientos, y la superficie de
exposición tiene que ser cero por defecto (D9). Se abre con doble clic.
"""

PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Registro — visor</title>
<style>
  :root {
    color-scheme: light dark;
    --fondo: #faf9f7; --papel: #fff; --tinta: #23201d; --suave: #6b635c;
    --linea: #e4dfd8; --acento: #7c6a58; --realce: #f0ebe4;
    --sin-registrar: #f2efeb; --sin-ingestas: #ded5c8; --registrado: #a89078;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --fondo: #1a1816; --papel: #232020; --tinta: #ece7e1; --suave: #9c938a;
      --linea: #35302c; --acento: #c2a98e; --realce: #2c2724;
      --sin-registrar: #262220; --sin-ingestas: #4a4139; --registrado: #a89078;
    }
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--fondo); color: var(--tinta);
    font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
  }
  .envoltorio { max-width: 1040px; margin: 0 auto; padding: 24px 16px 64px; }
  h1 { font-size: 1.45rem; margin: 0 0 4px; letter-spacing: -.01em; }
  .sub { color: var(--suave); font-size: .85rem; margin-bottom: 20px; }
  .aviso {
    background: var(--realce); border-left: 3px solid var(--acento);
    padding: 12px 14px; border-radius: 0 6px 6px 0; margin-bottom: 24px;
    font-size: .85rem; color: var(--suave);
  }
  .aviso strong { color: var(--tinta); }
  .cifras { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 28px; }
  .cifra .n { font-size: 1.5rem; font-weight: 600; }
  .cifra .et { font-size: .75rem; color: var(--suave); text-transform: uppercase;
               letter-spacing: .05em; }
  .mes { margin-bottom: 28px; }
  .mes h2 { font-size: .95rem; font-weight: 600; margin: 0 0 10px; text-transform: capitalize; }
  .rejilla { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
  .cab { font-size: .68rem; color: var(--suave); text-align: center; padding-bottom: 4px;
         text-transform: uppercase; letter-spacing: .04em; }
  .celda {
    aspect-ratio: 1; border: none; border-radius: 6px; cursor: default;
    background: var(--sin-registrar); color: var(--suave);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    font: inherit; font-size: .8rem; padding: 2px; transition: outline-color .12s;
    outline: 2px solid transparent;
  }
  .celda.hay { background: var(--sin-ingestas); color: var(--tinta); cursor: pointer; }
  .celda.ingestas { background: var(--registrado); color: #fff; cursor: pointer; }
  .celda:is(.hay, .ingestas):hover { outline-color: var(--acento); }
  .celda.activa { outline-color: var(--acento); outline-width: 3px; }
  .celda .d { font-weight: 600; }
  .celda .n { font-size: .62rem; opacity: .8; }
  .celda.vacia { background: none; }
  .leyenda { display: flex; flex-wrap: wrap; gap: 14px; font-size: .75rem;
             color: var(--suave); margin: 4px 0 28px; }
  .leyenda span { display: flex; align-items: center; gap: 6px; }
  .llave { width: 12px; height: 12px; border-radius: 3px; display: inline-block; }
  .dia {
    background: var(--papel); border: 1px solid var(--linea); border-radius: 10px;
    padding: 20px; margin-top: 8px;
  }
  .dia h2 { margin: 0 0 2px; font-size: 1.1rem; text-transform: capitalize; }
  .dia .meta { color: var(--suave); font-size: .82rem; margin-bottom: 18px; }
  .ingesta { border-top: 1px solid var(--linea); padding: 16px 0; }
  .ingesta:last-of-type { padding-bottom: 0; }
  .fila-hora { display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
  .hora { font-variant-numeric: tabular-nums; font-weight: 600; font-size: 1.05rem; }
  .tipo { font-size: .72rem; text-transform: uppercase; letter-spacing: .05em;
          color: var(--suave); }
  .hueco { font-size: .72rem; color: var(--suave); margin-left: auto; }
  .alimentos { margin: 6px 0 10px; }
  .transicion { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
                margin-bottom: 8px; }
  .flecha { color: var(--suave); }
  .et-emocion, .et-dato {
    display: inline-block; font-size: .76rem; padding: 2px 8px; border-radius: 99px;
    border: 1px solid var(--linea); background: var(--realce); margin: 0 3px 3px 0;
  }
  .pensamiento { color: var(--suave); font-style: italic; font-size: .87rem; margin: 4px 0; }
  .datos { margin-top: 8px; }
  .seccion { margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--linea); }
  .seccion h3 { font-size: .74rem; text-transform: uppercase; letter-spacing: .05em;
                color: var(--suave); margin: 0 0 6px; font-weight: 600; }
  .seccion p { margin: 0; white-space: pre-wrap; }
  .nada { color: var(--suave); font-style: italic; }
  footer { margin-top: 40px; font-size: .75rem; color: var(--suave);
           border-top: 1px solid var(--linea); padding-top: 14px; }
  @media (max-width: 520px) {
    .celda .n { display: none; }
    .dia { padding: 16px; }
  }
</style>
</head>
<body>
<div class="envoltorio">
  <h1>Registro de alimentación y estado emocional</h1>
  <p class="sub" id="sub"></p>

  <div class="aviso">
    <strong>Esto es el visor de revisión, no un informe.</strong> No hay gráficos de patrones
    a propósito: hacen falta 4–6 semanas de registro antes de mirar nada, y mirar a los diez
    días lleva a conclusiones que después condicionan lo que se registra.
    Los días se colorean sólo por <em>si hay registro</em> — nunca por cómo fue el día.
  </div>

  <div class="cifras" id="cifras"></div>
  <div id="calendario"></div>
  <div class="leyenda">
    <span><i class="llave" style="background:var(--registrado)"></i> día con ingestas</span>
    <span><i class="llave" style="background:var(--sin-ingestas)"></i> nota sin ingestas</span>
    <span><i class="llave" style="background:var(--sin-registrar)"></i> sin registrar</span>
  </div>
  <div id="detalle"></div>

  <footer id="pie"></footer>
</div>

<script id="datos" type="application/json">__DATOS__</script>
<script>
const D = JSON.parse(document.getElementById('datos').textContent);
const porFecha = Object.fromEntries(D.dias.map(d => [d.fecha, d]));
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const bonito = v => esc(String(v).replace(/_/g, ' '));

document.getElementById('sub').textContent =
  D.desde ? `${D.desde} — ${D.hasta} · generado el ${D.generado}` : 'sin notas';

const conIngestas = D.dias.filter(d => d.n_ingestas > 0).length;
const nIngestas = D.dias.reduce((a, d) => a + d.n_ingestas, 0);
document.getElementById('cifras').innerHTML = [
  [D.dias.length, 'días registrados'],
  [conIngestas, 'con ingestas'],
  [nIngestas, 'ingestas'],
  [nIngestas && conIngestas ? (nIngestas / conIngestas).toFixed(1) : '—', 'ingestas por día'],
].map(([n, et]) => `<div class="cifra"><div class="n">${n}</div><div class="et">${et}</div></div>`).join('');

// --- Calendario: un bloque por mes, del primero al último día registrado ---
function meses() {
  if (!D.desde) return [];
  const [a0, m0] = D.desde.split('-').map(Number);
  const [a1, m1] = D.hasta.split('-').map(Number);
  const salida = [];
  for (let a = a0, m = m0; a < a1 || (a === a1 && m <= m1); m === 12 ? (m = 1, a++) : m++) {
    salida.push([a, m]);
  }
  return salida;
}

document.getElementById('calendario').innerHTML = meses().map(([a, m]) => {
  const primero = new Date(a, m - 1, 1);
  const dias = new Date(a, m, 0).getDate();
  const hueco = (primero.getDay() + 6) % 7;            // la semana empieza en lunes
  let celdas = Array(hueco).fill('<div class="celda vacia"></div>');
  for (let d = 1; d <= dias; d++) {
    const fecha = `${a}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    const dia = porFecha[fecha];
    const clase = !dia ? '' : (dia.n_ingestas > 0 ? 'ingestas' : 'hay');
    const cuenta = dia && dia.n_ingestas ? `<span class="n">${dia.n_ingestas}</span>` : '';
    celdas.push(dia
      ? `<button class="celda ${clase}" data-f="${fecha}"><span class="d">${d}</span>${cuenta}</button>`
      : `<div class="celda"><span class="d">${d}</span></div>`);
  }
  return `<div class="mes"><h2>${D.meses[m - 1]} ${a}</h2><div class="rejilla">
    ${D.dias_semana.map(n => `<div class="cab">${n.slice(0, 3)}</div>`).join('')}
    ${celdas.join('')}</div></div>`;
}).join('');

// --- Detalle del día ---
const etiquetas = (lista, extra) => {
  const partes = (lista || []).map(v => `<span class="et-emocion">${bonito(v)}</span>`);
  if (extra) partes.push(`<span class="et-emocion">“${esc(extra)}”</span>`);
  return partes.length ? partes.join('') : '<span class="nada">—</span>';
};

function pintarIngesta(i) {
  const datos = [
    i.hambre_antes && `hambre: ${bonito(i.hambre_antes)}`,
    i.energia && `energía: ${bonito(i.energia === 'otro' && i.energia_otro ? i.energia_otro : i.energia)}`,
    (i.sintomas || []).length && `síntomas: ${(i.sintomas).map(s =>
      s === 'otros' && i.sintoma_otros ? i.sintoma_otros : String(s).replace(/_/g, ' ')).join(', ')}`,
    i.compania && bonito(i.compania), i.lugar && bonito(i.lugar),
    i.pantalla === true && 'con pantalla', i.pantalla === false && 'sin pantalla',
  ].filter(Boolean);

  return `<div class="ingesta">
    <div class="fila-hora">
      <span class="hora">${esc(i.hora || '--:--')}</span>
      <span class="tipo">${bonito(i.tipo || '')}${i.madrugada ? ' · madrugada' : ''}</span>
      ${i.hueco_min != null ? `<span class="hueco">${Math.round(i.hueco_min / 60 * 10) / 10} h desde la anterior</span>` : ''}
    </div>
    <div class="alimentos">${esc(i.alimentos || '')}</div>
    ${i.pensamientos_antes ? `<p class="pensamiento">“${esc(i.pensamientos_antes)}”</p>` : ''}
    <div class="transicion">
      ${etiquetas(i.emociones_antes, i.emocion_otra_antes)}
      <span class="flecha">→</span>
      ${etiquetas(i.emociones_despues, i.emocion_otra_despues)}
    </div>
    ${i.pensamientos_despues ? `<p class="pensamiento">“${esc(i.pensamientos_despues)}”</p>` : ''}
    ${datos.length ? `<div class="datos">${datos.map(d =>
      `<span class="et-dato">${esc(d)}</span>`).join('')}</div>` : ''}
  </div>`;
}

function pintarDia(fecha) {
  const d = porFecha[fecha];
  if (!d) return;
  const meta = [
    d.sueno_horas != null && `durmió ${d.sueno_horas} h${d.sueno_calidad ? ` (${d.sueno_calidad})` : ''}`,
    d.agua_litros != null && `${d.agua_litros} L de agua`,
    (d.actividad || d.actividad_horas != null) && `actividad: ${[d.actividad_horas != null && `${d.actividad_horas} h`, d.actividad].filter(Boolean).join(', ')}`,
  ].filter(Boolean).join(' · ');

  const secciones = [
    ['Reflexiones', d.reflexiones],
    ['Pensamientos predominantes', d.pensamientos_predominantes],
    ['Orgullo y gratitud', d.orgullo_y_gratitud],
  ].filter(([, t]) => t).map(([t, c]) =>
    `<div class="seccion"><h3>${t}</h3><p>${esc(c)}</p></div>`).join('');

  document.getElementById('detalle').innerHTML = `<div class="dia">
    <h2>${D.dias_semana[d.dia_semana]}, ${fecha}</h2>
    <p class="meta">${meta || '<span class="nada">sin datos del día</span>'}</p>
    ${d.ingestas.length ? d.ingestas.map(pintarIngesta).join('')
      : '<p class="nada">Sin ingestas registradas. Es un dato, no un hueco.</p>'}
    ${secciones}
  </div>`;

  document.querySelectorAll('.celda.activa').forEach(c => c.classList.remove('activa'));
  const celda = document.querySelector(`.celda[data-f="${fecha}"]`);
  if (celda) celda.classList.add('activa');
  document.getElementById('detalle').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

document.getElementById('calendario').addEventListener('click', e => {
  const celda = e.target.closest('.celda[data-f]');
  if (celda) pintarDia(celda.dataset.f);
});

document.getElementById('pie').textContent =
  `Origen: ${D.origen} · Página local y autocontenida: no hace ninguna petición de red.`;

if (D.dias.length) pintarDia(D.dias[D.dias.length - 1].fecha);
</script>
</body>
</html>
"""
