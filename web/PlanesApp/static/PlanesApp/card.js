(() => {
  'use strict';
  const form = document.querySelector('.card-form');
  const card = document.querySelector('[data-demo-card]');
  if (!form || !card) return;
  const holder = form.querySelector('[data-card-holder]');
  const number = form.querySelector('[data-card-number]');
  const expiry = form.querySelector('[data-card-expiry]');
  const cvc = form.querySelector('[data-card-cvc]');
  const update = () => {
    card.querySelector('[data-preview-holder]').textContent = holder.value.trim() || 'Tu nombre';
    card.querySelector('[data-preview-number]').textContent = number.value.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim() || '•••• •••• •••• ••••';
    card.querySelector('[data-preview-expiry]').textContent = expiry.value || 'MM/AA';
    card.querySelector('[data-preview-cvc]').textContent = cvc.value.replace(/\D/g, '').slice(0, 3) || '•••';
  };
  form.addEventListener('input', update);
  cvc.addEventListener('focus', () => card.classList.add('is-back'));
  cvc.addEventListener('blur', () => card.classList.remove('is-back'));
  update();
})();
