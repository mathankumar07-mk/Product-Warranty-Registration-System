const detailStatus = document.querySelector("#detail-status");
const detailContent = document.querySelector("#detail-content");
const productId = new URLSearchParams(window.location.search).get("id");

function formatPrice(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
    }).format(value);
}

async function loadProduct() {
    if (!productId) {
        detailStatus.textContent = "No product was selected.";
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:8000/products/${productId}`);
        const product = await response.json();
        if (!response.ok) {
            throw new Error(product.detail || "Product not found.");
        }

        detailStatus.textContent = "";
        detailContent.innerHTML = `
            <p class="eyebrow">${product.brand} / ${product.model_number}</p>
            <h1>${product.name}</h1>
            <p class="detail-description">${product.description || "Product details will be available soon."}</p>
            <div class="detail-price">${formatPrice(product.price)}</div>
            <div class="detail-meta">
                <span>Model ${product.model_number}</span>
                <span>${product.stock_quantity} in stock</span>
            </div>
            <a class="detail-action" href="login.html">Sign in to add to cart <span aria-hidden="true">&#8594;</span></a>
        `;
    } catch (error) {
        detailStatus.textContent = error.message;
    }
}

loadProduct();
