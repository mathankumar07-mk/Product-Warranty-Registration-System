const adminStatus = document.querySelector("#admin-status");
const adminProducts = document.querySelector("#admin-products");
const categorySelect = document.querySelector("#category-id");
const categoryForm = document.querySelector("#category-form");
const productForm = document.querySelector("#product-form");

const token = localStorage.getItem("access_token");
const apiHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
});

function showStatus(message, isError = false) {
    adminStatus.textContent = message;
    adminStatus.classList.toggle("status-error", isError);
}

async function loadCategories() {
    const response = await fetch("http://127.0.0.1:8000/categories");
    const categories = await response.json();
    if (!response.ok) {
        throw new Error(categories.detail || "Unable to load categories.");
    }
    categorySelect.innerHTML = categories.map((category) =>
        `<option value="${category.id}">${category.name}</option>`
    ).join("");
}

async function loadProducts() {
    const response = await fetch("http://127.0.0.1:8000/products");
    const products = await response.json();
    if (!response.ok) {
        throw new Error(products.detail || "Unable to load products.");
    }
    adminProducts.innerHTML = products.map((product) => `
        <article class="admin-product-row">
            <div>
                <strong>${product.name}</strong>
                <span>${product.brand} / ${product.model_number}</span>
            </div>
            <div class="admin-product-value">${product.price} / ${product.stock_quantity} units</div>
        </article>
    `).join("") || "<p class=\"empty-state\">No products yet.</p>";
}

async function loadAdminData() {
    if (!token) {
        window.location.href = "login.html";
        return;
    }
    try {
        await Promise.all([loadCategories(), loadProducts()]);
        showStatus("Admin catalogue ready.");
    } catch (error) {
        showStatus(error.message, true);
    }
}

categoryForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(categoryForm);
    try {
        const response = await fetch("http://127.0.0.1:8000/categories", {
            method: "POST",
            headers: apiHeaders(),
            body: JSON.stringify({ name: formData.get("name"), description: formData.get("description") }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "Unable to create category.");
        categoryForm.reset();
        await loadCategories();
        showStatus("Category created.");
    } catch (error) {
        showStatus(error.message, true);
    }
});

productForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(productForm);
    const payload = {
        category_id: Number(formData.get("category_id")),
        name: formData.get("name"),
        description: formData.get("description"),
        price: Number(formData.get("price")),
        stock_quantity: Number(formData.get("stock_quantity")),
        brand: formData.get("brand"),
        model_number: formData.get("model_number"),
    };
    try {
        const response = await fetch("http://127.0.0.1:8000/products", {
            method: "POST",
            headers: apiHeaders(),
            body: JSON.stringify(payload),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || "Unable to create product.");
        productForm.reset();
        await loadProducts();
        showStatus("Product created.");
    } catch (error) {
        showStatus(error.message, true);
    }
});

loadAdminData();
