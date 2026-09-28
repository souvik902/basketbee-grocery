// BasketBee front-end interactions: AJAX add-to-cart + live badge/bar updates.

function basketbeeCsrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

function basketbeeUpdateCartBadge(count) {
  const badge = document.getElementById('cart-badge');
  const barCount = document.getElementById('cart-bar-count');
  const bar = document.getElementById('cart-bar');

  if (count > 0) {
    if (badge) {
      badge.textContent = count;
    } else {
      const btn = document.querySelector('.icon-btn');
      if (btn) {
        const span = document.createElement('span');
        span.className = 'badge';
        span.id = 'cart-badge';
        span.textContent = count;
        btn.appendChild(span);
      }
    }
    if (barCount) barCount.textContent = count;
    if (bar) bar.classList.add('is-visible');
  } else {
    if (badge) badge.remove();
    if (bar) bar.classList.remove('is-visible');
  }
}

function basketbeeAddToCart(url) {
  return fetch(url, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': basketbeeCsrfToken(),
    },
  })
    .then((r) => r.json())
    .then((data) => {
      basketbeeUpdateCartBadge(data.cart_count);
      return data;
    });
}

document.addEventListener('click', function (event) {
  const btn = event.target.closest('.add-btn');
  if (!btn) return;
  event.preventDefault();
  const url = btn.dataset.addUrl;
  const originalText = btn.textContent;
  basketbeeAddToCart(url).then(() => {
    btn.textContent = 'Added ✓';
    setTimeout(() => { btn.textContent = originalText; }, 1000);
  });
});

// Show the cart bar on load if the badge already has items.
document.addEventListener('DOMContentLoaded', function () {
  const badge = document.getElementById('cart-badge');
  if (badge) {
    document.getElementById('cart-bar')?.classList.add('is-visible');
  }
});
