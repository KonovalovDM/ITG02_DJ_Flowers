document.addEventListener("DOMContentLoaded", function() {
    console.log("FlowerDelivery: сайт загружен!");

    // Добавление товара в корзину
    document.querySelectorAll(".add-to-cart").forEach(button => {
        button.addEventListener("click", function() {
            alert("Товар добавлен в корзину!");
        });
    });
});
