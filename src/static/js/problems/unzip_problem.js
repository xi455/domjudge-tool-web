document.querySelector("#uploadElement").addEventListener("click", function () {
    document.querySelector("#file").click();
});

document.querySelector("#file").addEventListener('change', function() {
    let fileList = this.files;
    let fileNames = Array.from(fileList).map(file => file.name);
    let fileListElement = document.querySelector("#fileList");
    fileListElement.innerHTML = '';
    fileNames.forEach(fileName => {
        fileListElement.innerHTML += `
            <div class="card">
                <div class="card-body">
                    ${fileName}
                </div>
            </div>
        `;
    });
});