// Backend URLs
const LOCAL = {
    UPLOAD_URL: "http://localhost:8000/embeddings/upload",
    PROCESS_URL: "http://localhost:8000/embeddings/process-uploads"
};
const PROD = {
    UPLOAD_URL: "http://10.1.1.172:3820/embeddings/upload",
    PROCESS_URL: "http://10.1.1.172:3820/embeddings/process-uploads"
};

// Choose environment
let ENV = PROD; // Change to LOCAL for local testing

const SUPPORTED_EXTENSIONS = [".txt", ".pdf", ".docx", ".md"];

const folderPicker = document.getElementById("folderPicker");
const uploadBtn = document.getElementById("uploadBtn");
const statusDiv = document.getElementById("status");
const filesTableBody = document.querySelector("#filesTable tbody");

uploadBtn.addEventListener("click", async () => {
    const files = folderPicker.files;
    if (!files.length) {
        alert("Select a folder first!");
        return;
    }

    const filteredFiles = Array.from(files).filter(f =>
        SUPPORTED_EXTENSIONS.includes(f.name.slice(f.name.lastIndexOf(".")).toLowerCase())
    );

    statusDiv.textContent = `Found ${filteredFiles.length} supported files. Starting upload...`;

    filesTableBody.innerHTML = "";

    for (const file of filteredFiles) {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("uploaded_at", new Date().toISOString());
        formData.append("uploaded_by", navigator.userAgent);
        formData.append("original_path", file.webkitRelativePath);

        let uploadStatus = "Pending";
        let uploadMessage = "";

        try {
            const resp = await fetch(ENV.UPLOAD_URL, {
                method: "POST",
                body: formData
            });
            const result = await resp.json();
            uploadStatus = result.success ? "Success" : "Failed";
            uploadMessage = result.message || "";
        } catch (err) {
            uploadStatus = "Error";
            uploadMessage = err.message;
        }

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${file.name}</td>
            <td>${new Date().toLocaleString()}</td>
            <td>${navigator.userAgent}</td>
            <td>${uploadStatus}</td>
            <td>${uploadMessage}</td>
        `;
        filesTableBody.appendChild(row);
    }

    statusDiv.textContent = "All uploads completed. Triggering processing...";

    try {
        const processResp = await fetch(ENV.PROCESS_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ directory_path: "/app/data/uploads", recursive: true })
        });
        const processJson = await processResp.json();
        if (processJson.success) {
            statusDiv.textContent = `Processing complete: ${processJson.result.inserted_chunks} chunks inserted.`;
        } else {
            statusDiv.textContent = `Processing failed: ${processJson.error}`;
        }
    } catch (err) {
        statusDiv.textContent = `Processing error: ${err.message}`;
    }
});
