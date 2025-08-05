document.addEventListener("DOMContentLoaded", () => {
    const checkboxes = document.querySelectorAll(".checkbox-card input[type=checkbox]");
    const summaryItems = document.getElementById("summary-items");
    const totalPriceEl = document.getElementById("total-price");

    function updateSummary() {
        let total = 0;
        summaryItems.innerHTML = "";
        let itemsSelected = false;

        checkboxes.forEach((cb) => {
            if (cb.checked) {
                const card = cb.closest(".checkbox-card");
                const name = card.querySelector(".food-name").innerText;
                const qty = parseInt(card.querySelector(".qty-input").value);
                const price = parseFloat(cb.dataset.price);

                total += price * qty;
                itemsSelected = true;

                const itemEl = document.createElement("p");
                itemEl.innerText = `${name} x${qty} → ₱${(price * qty).toFixed(2)}`;
                summaryItems.appendChild(itemEl);
            }
        });

        if (!itemsSelected) {
            summaryItems.innerHTML = "<p>No items selected yet.</p>";
        }
        totalPriceEl.innerText = `₱${total.toFixed(2)}`;
    }

    checkboxes.forEach((cb) => {
        cb.addEventListener("change", (e) => {
            const card = cb.closest(".checkbox-card");
            card.classList.toggle("selected", cb.checked);
            updateSummary();
        });

        // Quantity buttons
        const card = cb.closest(".checkbox-card");
        const qtyInput = card.querySelector(".qty-input");
        const qtyBtns = card.querySelectorAll(".qty-btn");

        qtyBtns.forEach((btn) => {
            btn.addEventListener("click", () => {
                let qty = parseInt(qtyInput.value);
                if (btn.dataset.action === "increase") qty++;
                if (btn.dataset.action === "decrease" && qty > 1) qty--;
                qtyInput.value = qty;
                updateSummary();
            });
        });

        qtyInput.addEventListener("input", updateSummary);
    });

    updateSummary();
});
