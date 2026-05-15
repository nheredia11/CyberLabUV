async function loadScenarios() {
  const container = document.getElementById('scenario-grid');
  try {
    const res = await fetch('./data/scenarios.json');
    const data = await res.json();
    container.innerHTML = data.map(item => {
      const isConfigured = item.estado.toLowerCase().includes('config');
      return `
        <article class="card tile">
          <div class="status"><span class="dot ${isConfigured ? '' : 'warn'}"></span>${item.estado}</div>
          <h3>${item.id} · ${item.titulo}</h3>
          <div class="tag-row">
            <span class="tag">${item.nivel}</span>
          </div>
          <p>${item.descripcion}</p>
          <div class="command">${item.accion}</div>
        </article>
      `;
    }).join('');
  } catch (err) {
    container.innerHTML = '<article class="card tile"><h3>No fue posible cargar el catalogo</h3><p>Verifica que la carpeta <code>data/</code> este disponible en la interfaz.</p></article>';
  }
}

loadScenarios();
