function showToast(message) {
  const toast = document.getElementById('copy-toast');

  if (!toast) {
    return;
  }

  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 1800);
}

async function copyText(text) {
  const cleaned = String(text || '').replace(/\s+/g, ' ').trim();

  if (!cleaned) {
    showToast('No hay texto para copiar');
    return;
  }

  try {
    await navigator.clipboard.writeText(cleaned);
    showToast('Texto copiado');
  } catch {
    const textarea = document.createElement('textarea');
    textarea.value = cleaned;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('Texto copiado');
  }
}

function bindCopyButtons() {
  document.querySelectorAll('[data-copy-target]').forEach(button => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-copy-target');
      const target = document.getElementById(targetId);

      if (!target) {
        showToast('No se encontró la evidencia');
        return;
      }

      copyText(target.textContent);
    });
  });

  document.querySelectorAll('[data-copy-text]').forEach(button => {
    button.addEventListener('click', () => {
      copyText(button.getAttribute('data-copy-text'));
    });
  });
}

function addEventCopyButtons() {
  document.querySelectorAll('.event-item').forEach((eventItem, index) => {
    if (eventItem.querySelector('.event-copy-btn')) {
      return;
    }

    const message = eventItem.querySelector('strong')?.textContent || '';
    const time = eventItem.querySelector('small')?.textContent || '';
    const kind = eventItem.querySelector('.event-kind')?.textContent || '';

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'event-copy-btn';
    button.textContent = 'Copiar evento';
    button.setAttribute(
      'data-copy-text',
      `Evento ${index + 1} del laboratorio: tipo ${kind}, fecha ${time}, detalle: ${message}`
    );

    eventItem.appendChild(button);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  bindCopyButtons();
  addEventCopyButtons();
  bindCopyButtons();
});