let anno;
let jsonData = [];

document.addEventListener("DOMContentLoaded", function () {
    fetch("data.json")
        .then(response => response.json())
        .then(data => {
            console.log("✅ JSON Loaded:", data);
            jsonData = data;
            displayTables(jsonData);
        });

    function displayTables(tables) {
        const image = document.getElementById("page-image");
        if (!image) {
            console.error("❌ Image element not found!");
            return;
        }

        console.log("🚀 Initializing Annotorious...");
        anno = Annotorious.init({ image: image });

        tables.forEach(table => {
            if (table.page_no === 7) {
                const annotation = {
                    id: table.TableId,
                    type: "Annotation",
                    body: [{ type: "TextualBody", value: table.TableId }],
                    target: {
                        selector: [
                            {
                                type: "FragmentSelector",
                                conformsTo: "http://www.w3.org/TR/media-frags/",
                                value: `xywh=${table.Left * image.naturalWidth},${table.Top * image.naturalHeight},${table.Width * image.naturalWidth},${table.Height * image.naturalHeight}`
                            }
                        ]
                    }
                };
                anno.addAnnotation(annotation);
            }
        });

        anno.on("clickAnnotation", function (annotation) {
            const tableId = annotation.body[0].value;
            console.log(`📌 Table Selected: ${tableId}`);

            const tableData = jsonData.find(t => t.TableId === tableId);
            if (!tableData) {
                console.warn("⚠️ No data found for this table.");
                return;
            }

            updateRightPanel(tableData);
        });
    }

    function updateRightPanel(table) {
        console.log("🔄 Updating Right Panel...");
        
        // Populate table data
        let tableBody = document.querySelector("#table-data tbody");
        tableBody.innerHTML = "";  // Clear previous content
    
        table.MongoDB_Data.mappedValues.recordValues.forEach(record => {
            let row = document.createElement("tr");
            row.innerHTML = `
                <td contenteditable="false">${record.playerName || ""}</td>
                <td contenteditable="false">${record.statValue || ""}</td>
                <td contenteditable="false">${record.opponentName || ""}</td>
                <td contenteditable="false">${record.gameDate ? record.gameDate["$date"].split("T")[0] : ""}</td>
                <td contenteditable="false">${record.season || ""}</td>
            `;
            tableBody.appendChild(row);
        });
    
        // ✅ Fix metadata update: Use correct IDs from index.html
        document.getElementById("entity-value").textContent = table.MongoDB_Data.correctMappedValues.entity || "N/A";
        document.getElementById("statLabel-value").textContent = table.MongoDB_Data.mappedValues.statLabel || "N/A";
        document.getElementById("statPeriod-value").textContent = table.MongoDB_Data.correctMappedValues.statPeriod || "N/A";
        
                   
        // Enable buttons
        document.getElementById("edit-button").classList.remove("disabled");
        document.getElementById("submit-button").classList.remove("disabled");
    }

    document.getElementById("edit-button").addEventListener("click", function () {
        console.log("📝 Edit Mode Activated");
        document.querySelectorAll("#table-data tbody td").forEach(td => td.contentEditable = "true");
        this.style.display = "none";
        document.getElementById("submit-button").style.display = "inline-block";
    });

    document.getElementById("submit-button").addEventListener("click", function () {
        console.log("✅ Data Submitted (Mock)");
        document.querySelectorAll("#table-data tbody td").forEach(td => td.contentEditable = "false");
        alert("✅ Data submitted (mock function)");
        this.style.display = "none";
        document.getElementById("edit-button").style.display = "inline-block";
    });
});
