const loginForm = document.querySelector("#login-form");
const loginStatus = document.querySelector("#login-status");
const registerForm = document.querySelector("#register-form");
const registerStatus = document.querySelector("#register-status");
const dashboardStatus = document.querySelector("#dashboard-status");
const userName = document.querySelector("#user-name");
const logoutButton = document.querySelector("#logout-button");

async function loadCurrentUser() {
	const token = localStorage.getItem("access_token");
	if (!token) {
		window.location.href = "login.html";
		return;
	}

	try {
		const user = await getCurrentUser(token);
		if (userName) {
			userName.textContent = user.name;
		}
	} catch (error) {
		localStorage.removeItem("access_token");
		if (dashboardStatus) {
			dashboardStatus.textContent = error.message;
		}
		window.location.href = "login.html";
	}
}

if (userName) {
	loadCurrentUser();
}

if (logoutButton) {
	logoutButton.addEventListener("click", () => {
		localStorage.removeItem("access_token");
		window.location.href = "login.html";
	});
}

if (loginForm) {
	loginForm.addEventListener("submit", async (event) => {
		event.preventDefault();
		loginStatus.textContent = "Signing in...";

		const formData = new FormData(loginForm);
		const payload = {
			email: formData.get("email"),
			password: formData.get("password"),
		};

		try {
			const result = await loginUser(payload);
			localStorage.setItem("access_token", result.access_token);
			loginStatus.textContent = "Signed in successfully.";
			window.location.href = "dashboard.html";
		} catch (error) {
			loginStatus.textContent = error.message;
		}
	});
}

if (registerForm) {
	registerForm.addEventListener("submit", async (event) => {
		event.preventDefault();
		registerStatus.textContent = "Creating your account...";

		const formData = new FormData(registerForm);
		const payload = {
			name: formData.get("name"),
			email: formData.get("email"),
			password: formData.get("password"),
			phone: formData.get("phone") || null,
		};

		try {
			await registerUser(payload);
			window.location.href = "login.html";
		} catch (error) {
			registerStatus.textContent = error.message;
		}
	});
}
