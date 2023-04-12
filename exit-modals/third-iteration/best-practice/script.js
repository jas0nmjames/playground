function showModal() {
    document.getElementById("myModal").style.display = "block";
}

function closeModal() {
    document.getElementById("myModal").style.display = "none";
}

function leaveSite() {
    window.open("new_page.html", "_blank");
    closeModal();
}