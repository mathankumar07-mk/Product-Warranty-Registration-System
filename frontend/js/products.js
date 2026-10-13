const productList = document.querySelector("#product-list");
const productsStatus = document.querySelector("#products-status");

const API_BASE_URL = "http://127.0.0.1:8000";

async function apiRequest(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `Request failed with status ${response.status}`);
  }
  return data;
}

function formatPrice(value) {
	return new Intl.NumberFormat("en-IN", {
		style: "currency",
		currency: "INR",
	}).format(value);
}

function renderProducts(products) {
	productList.innerHTML = products.map((product, index) => `
		<a class="product-card" href="product-details.html?id=${product.id}">
			<span class="card-number">${String(index + 1).padStart(2, "0")}</span>
			<h2>${product.name}</h2>
			<p class="product-brand">${product.brand} / ${product.model_number}</p>
			<p>${product.description || "Product details available after selection."}</p>
			<div class="product-meta">
				<strong>${formatPrice(product.price)}</strong>
				<span>${product.stock_quantity} in stock</span>
			</div>
		</a>
	`).join("");
}

async function loadProducts() {
	try {
		const products = await apiRequest("/products");
		productsStatus.textContent = products.length ? `${products.length} products available` : "No products available yet.";
		if (products.length) {
			renderProducts(products);
		}
	} catch (error) {
		productsStatus.textContent = error.message;
	}
}

loadProducts();
