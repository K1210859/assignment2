// Open original image in the modal body (thumbnails and anchors call this)
window.openPreview = function (url) {
  var body = document.getElementById("image-modal-body");
  while (body.firstChild) body.removeChild(body.firstChild);
  var img = document.createElement("img");
  img.className = "img-fluid";
  img.src = url;
  img.alt = "preview";
  body.appendChild(img);
};

// Search input validation (5.2)
(function () {
  var form = document.getElementById("searchForm");
  if (!form) return;

  function validate() {
    var by = document.getElementById("searchBy").value;
    var name = document.getElementById("searchText").value.trim();
    var date = document.getElementById("searchDate").value.trim();
    var tags = document.getElementById("searchTags").value.trim();

    if (by === "name") {
      if (!name) { alert("Name should not be empty"); return false; } // 5.2.2
    } else if (by === "date") {
      // Only format check MM/DD/YYYY (no other date checks) – 5.2.1
      var re = /^(0?[1-9]|1[0-2])\/([0-9]{1,2})\/\d{4}$/;
      if (!re.test(date)) { alert("Date format should be MM/DD/YYYY"); return false; }
    } else if (by === "tags") {
      if (!tags) { alert("Tags should not be empty"); return false; } // 5.2.3
    }
    return true;
  }

  form.addEventListener("submit", function (e) {
    if (!validate()) e.preventDefault();
  });

  // Show/hide relevant input helper (optional UX)
  function syncInputs() {
    var by = document.getElementById("searchBy").value;
    document.getElementById("searchText").style.display = (by === "name") ? "block" : "none";
    document.getElementById("searchDate").style.display = (by === "date") ? "block" : "none";
    document.getElementById("searchTags").style.display = (by === "tags") ? "block" : "none";
  }
  document.getElementById("searchBy").addEventListener("change", syncInputs);
  syncInputs();
})();
