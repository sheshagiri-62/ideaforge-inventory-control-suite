const formatCurrency = (value) => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;

const productTableBody = document.getElementById('productsTableBody');
const suppliersTableBody = document.getElementById('suppliersTableBody');
const lowStockList = document.getElementById('lowStockList');
const userBadge = document.getElementById('userBadge');
const logoutBtn = document.getElementById('logoutBtn');
const loginButton = document.getElementById('loginButton');
const loginForm = document.getElementById('loginForm');
const productForm = document.getElementById('productForm');
const supplierForm = document.getElementById('supplierForm');
const loginMessage = document.getElementById('loginMessage');
const productMessage = document.getElementById('productMessage');
const supplierMessage = document.getElementById('supplierMessage');
const loginModal = document.getElementById('loginModal');
const closeModalBtn = document.getElementById('closeModalBtn');

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Request failed');
  }

  return data;
}

function renderStats(stats) {
  document.getElementById('statsProducts').textContent = stats.products ?? 0;
  document.getElementById('statsSuppliers').textContent = stats.suppliers ?? 0;
  document.getElementById('statsLowStock').textContent = stats.low_stock ?? 0;
  document.getElementById('statsInventoryValue').textContent = formatCurrency(stats.inventory_value ?? 0);
  userBadge.textContent = stats.username || 'Guest';

  if (stats.username && stats.username !== 'Guest') {
    logoutBtn.classList.remove('hidden');
    loginButton.classList.add('hidden');
  } else {
    logoutBtn.classList.add('hidden');
    loginButton.classList.remove('hidden');
  }
}

function renderProducts(products) {
  if (!productTableBody) return;
  productTableBody.innerHTML = products.length
    ? products.map((product) => `
        <tr>
          <td>${product.sku}</td>
          <td>${product.name}</td>
          <td>${product.category || '-'}</td>
          <td>${product.stock}</td>
          <td>${formatCurrency(product.price)}</td>
        </tr>
      `).join('')
    : '<tr><td colspan="5">No products found.</td></tr>';
}

function renderSuppliers(suppliers) {
  if (!suppliersTableBody) return;
  suppliersTableBody.innerHTML = suppliers.length
    ? suppliers.map((supplier) => `
        <tr>
          <td>${supplier.name}</td>
          <td>${supplier.contact_person || '-'}</td>
          <td>${supplier.email || '-'}</td>
          <td>${supplier.phone || '-'}</td>
        </tr>
      `).join('')
    : '<tr><td colspan="4">No suppliers found.</td></tr>';
}

function renderLowStock(items) {
  if (!lowStockList) return;
  lowStockList.innerHTML = items.length
    ? items.map((item) => `<li>${item.name} — ${item.stock} left</li>`).join('')
    : '<li>All products are within the safe stock threshold.</li>';
}

function setActiveSection(sectionId) {
  document.querySelectorAll('.nav-item').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.section === sectionId);
  });

  document.querySelectorAll('.page-section').forEach((section) => {
    section.classList.toggle('active', section.id === sectionId);
  });
}

async function loadDashboard() {
  try {
    const [stats, products, suppliers, lowStock] = await Promise.all([
      fetchJson('/api/stats'),
      fetchJson('/api/products'),
      fetchJson('/api/suppliers'),
      fetchJson('/api/low-stock'),
    ]);

    renderStats(stats);
    renderProducts(products);
    renderSuppliers(suppliers);
    renderLowStock(lowStock);
  } catch (error) {
    console.error(error);
  }
}

loginButton?.addEventListener('click', () => {
  loginModal?.classList.remove('hidden');
});

closeModalBtn?.addEventListener('click', () => {
  loginModal?.classList.add('hidden');
});

loginForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(loginForm);
  const payload = {
    username: formData.get('username'),
    password: formData.get('password'),
  };

  try {
    const response = await fetchJson('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    loginMessage.textContent = `Welcome, ${response.username}!`;
    loginMessage.style.color = '#85f0b2';
    loginModal.classList.add('hidden');
    await loadDashboard();
  } catch (error) {
    loginMessage.textContent = error.message;
    loginMessage.style.color = '#fca5a5';
  }
});

productForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(productForm);
  const payload = {
    sku: formData.get('sku'),
    name: formData.get('name'),
    category: formData.get('category'),
    price: formData.get('price'),
    stock: formData.get('stock'),
    description: formData.get('description'),
  };

  try {
    const response = await fetchJson('/api/products', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    productMessage.textContent = response.message || 'Product added successfully.';
    productMessage.style.color = '#85f0b2';
    productForm.reset();
    await loadDashboard();
  } catch (error) {
    productMessage.textContent = error.message;
    productMessage.style.color = '#fca5a5';
  }
});

supplierForm?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const formData = new FormData(supplierForm);
  const payload = {
    name: formData.get('name'),
    contact_person: formData.get('contact_person'),
    email: formData.get('email'),
    phone: formData.get('phone'),
    address: formData.get('address'),
  };

  try {
    const response = await fetchJson('/api/suppliers', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    supplierMessage.textContent = response.success ? 'Supplier added successfully.' : 'Supplier added.';
    supplierMessage.style.color = '#85f0b2';
    supplierForm.reset();
    await loadDashboard();
  } catch (error) {
    supplierMessage.textContent = error.message;
    supplierMessage.style.color = '#fca5a5';
  }
});

logoutBtn?.addEventListener('click', async () => {
  try {
    await fetchJson('/api/auth/logout', { method: 'POST' });
    await loadDashboard();
    loginMessage.textContent = 'Signed out successfully.';
    loginMessage.style.color = '#85f0b2';
  } catch (error) {
    console.error(error);
  }
});

document.querySelectorAll('.nav-item').forEach((item) => {
  item.addEventListener('click', () => setActiveSection(item.dataset.section));
});

document.getElementById('refreshBtn')?.addEventListener('click', loadDashboard);

setActiveSection('overview');
loadDashboard();
