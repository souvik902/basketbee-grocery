document.querySelectorAll('.message').forEach(message => setTimeout(() => message.remove(), 4500));
document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("searchInput");

    if (!searchInput) return;

    const searchWords = [
        "rice",
        "milk",
        "atta",
        "vegetables",
        "biscuits",
        "fruits",
        "oil"
    ];

    let index = 0;

    function changePlaceholder() {

        // যদি user কিছু লিখে থাকে, animation বন্ধ থাকবে
        if (searchInput.value.trim() !== "") {
            return;
        }

        searchInput.classList.add("placeholder-slide");

        setTimeout(function () {

            index = (index + 1) % searchWords.length;

            searchInput.placeholder =
                `Search "${searchWords[index]}"`;

            searchInput.classList.remove("placeholder-slide");

        }, 350);
    }

    // প্রথম text
    searchInput.placeholder = `Search "${searchWords[0]}"`;

    // প্রতি 2.5 সেকেন্ডে পরিবর্তন
    setInterval(changePlaceholder, 2500);

});
