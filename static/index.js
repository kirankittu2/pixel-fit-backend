const form = document.querySelector("#image-form");

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const images = form.querySelector(".image-file");
  const imgContainer = document.querySelector(".image-container");
  const file = images.files[0];

  var formData = new FormData();
  formData.append("file", file);

  fetch("/upload", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      for (let i = 0; i < data.matrix.length; i++) {
        const container = document.createElement("div");
        container.classList.add("image-rep-row");
        for (let j = 0; j < data.matrix[i].length; j++) {
          const element = document.createElement("div");
          element.textContent = "M";
          element.style.fontWeight = "900";
          element.classList.add("image-rep");
          element.style.color = `rgb(${data.matrix[i][j][0]}, ${data.matrix[i][j][1]}, ${data.matrix[i][j][2]})`;
          container.appendChild(element);
        }
        imgContainer.appendChild(container);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
});
