document.querySelectorAll('.message').forEach(message => setTimeout(() => message.remove(), 4500));
document.addEventListener("DOMContentLoaded", function () {

    const carousel = document.querySelector("[data-carousel]");

    if (carousel) {
        const track = carousel.querySelector(".promo-track");
        const slides = Array.from(carousel.querySelectorAll(".promo-slide"));
        const dots = Array.from(carousel.querySelectorAll(".promo-dot"));
        const slideNumber = carousel.querySelector("[data-slide-number]");
        const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
        let currentSlide = 0;
        let timer;

        function showSlide(index) {
            currentSlide = (index + slides.length) % slides.length;
            track.style.transform = `translateX(-${currentSlide * 100}%)`;

            slides.forEach(function (slide, slideIndex) {
                const isActive = slideIndex === currentSlide;
                slide.classList.toggle("is-active", isActive);
                slide.setAttribute("aria-hidden", String(!isActive));
                slide.inert = !isActive;
            });

            dots.forEach(function (dot, dotIndex) {
                const isActive = dotIndex === currentSlide;
                dot.classList.toggle("is-active", isActive);
                if (isActive) {
                    dot.setAttribute("aria-current", "true");
                } else {
                    dot.removeAttribute("aria-current");
                }
            });

            if (slideNumber) {
                slideNumber.textContent = String(currentSlide + 1).padStart(2, "0");
            }
        }

        function stopAutoplay() {
            window.clearInterval(timer);
        }

        function startAutoplay() {
            stopAutoplay();
            if (!reducedMotion.matches) {
                timer = window.setInterval(function () {
                    showSlide(currentSlide + 1);
                }, 6000);
            }
        }

        carousel.querySelector("[data-carousel-prev]").addEventListener("click", function () {
            showSlide(currentSlide - 1);
            startAutoplay();
        });

        carousel.querySelector("[data-carousel-next]").addEventListener("click", function () {
            showSlide(currentSlide + 1);
            startAutoplay();
        });

        dots.forEach(function (dot, index) {
            dot.addEventListener("click", function () {
                showSlide(index);
                startAutoplay();
            });
        });

        carousel.addEventListener("mouseenter", stopAutoplay);
        carousel.addEventListener("mouseleave", startAutoplay);
        carousel.addEventListener("focusin", stopAutoplay);
        carousel.addEventListener("focusout", function (event) {
            if (!carousel.contains(event.relatedTarget)) {
                startAutoplay();
            }
        });
        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                stopAutoplay();
            } else if (!carousel.matches(":hover") && !carousel.contains(document.activeElement)) {
                startAutoplay();
            }
        });
        reducedMotion.addEventListener("change", startAutoplay);

        startAutoplay();
    }

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
