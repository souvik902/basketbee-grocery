document.addEventListener("DOMContentLoaded", function () {

    const mainImage =
        document.getElementById("mainProductImage");

    const imageArea =
        document.querySelector(".gallery-main");

    const zoomBox =
        document.getElementById("zoomBox");

    const thumbnails =
        document.querySelectorAll(".thumbnail");


    if (!mainImage || !imageArea || !zoomBox) {
        return;
    }


    /* ==========================================
       SET ZOOM IMAGE
    ========================================== */

    function setZoomImage(url) {

        zoomBox.style.backgroundImage =
            `url("${url}")`;

    }


    setZoomImage(mainImage.src);


    /* ==========================================
       THUMBNAIL CLICK
    ========================================== */

    thumbnails.forEach(function (thumbnail) {

        thumbnail.addEventListener("click", function () {

            const imageURL =
                thumbnail.getAttribute("data-image");


            if (!imageURL) {
                return;
            }


            /* Smooth image change */

            mainImage.style.opacity = "0";


            setTimeout(function () {

                mainImage.src = imageURL;

                setZoomImage(imageURL);

                mainImage.style.opacity = "1";

            }, 150);


            /* Active thumbnail */

            thumbnails.forEach(function (item) {

                item.classList.remove("active");

            });


            thumbnail.classList.add("active");

        });

    });


    /* ==========================================
       MOUSE MOVE ZOOM
    ========================================== */

    imageArea.addEventListener(
        "mousemove",
        function (event) {

            const rect =
                imageArea.getBoundingClientRect();


            const x =
                event.clientX - rect.left;


            const y =
                event.clientY - rect.top;


            const xPercent =
                (x / rect.width) * 100;


            const yPercent =
                (y / rect.height) * 100;


            zoomBox.style.backgroundPosition =
                `${xPercent}% ${yPercent}%`;


            zoomBox.classList.add("show");

        }
    );


    /* ==========================================
       MOUSE LEAVE
    ========================================== */

    imageArea.addEventListener(
        "mouseleave",
        function () {

            zoomBox.classList.remove("show");

        }
    );

});