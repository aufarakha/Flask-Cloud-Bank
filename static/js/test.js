function toggleDropdown() {
    const menu = document.getElementById("dropdownMenu");
    menu.style.display = menu.style.display === "block" ? "none" : "block";
  }

  window.onclick = function(event) {
    if (!event.target.matches('.menu-dot, .menu-dot *')) {
      const menu = document.getElementById("dropdownMenu");
      if (menu && menu.style.display === "block") {
        menu.style.display = "none";
      }
    }
  };