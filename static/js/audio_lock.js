document.addEventListener("DOMContentLoaded", () => {
    const audio = document.getElementById("audio");
    const nextBtn = document.getElementById("nextBtn");

    if (!audio || !nextBtn) return;

    // bloquer le bouton au départ
    nextBtn.disabled = true;
    nextBtn.classList.add("disabled");

    audio.addEventListener("ended", () => {
        nextBtn.disabled = false;
        nextBtn.classList.remove("disabled");
    });
});
