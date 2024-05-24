// Add event listener to filter input
const filterInput = document.getElementById("filter-input");
filterInput.addEventListener("input", filterLogs);

// Define logEntries as an array of log entry elements
const logEntries = document.getElementsByClassName('log-entry');

// Get all text content on the page
const pageText = document.body.textContent.toLowerCase();

function filterLogs() {
    const input = document.getElementById("filter-input");
    const filter = input.value.toUpperCase(); // Perform the uppercase conversion once
    const table = document.getElementsByTagName("table")[0];

    if (!table) {
        console.error("No table found on the page");
        return;  // Exit the function early if no table is found
    }

    const tr = table.getElementsByTagName("tr");

    // Start loop from 1 to skip the header row
    for (let i = 1; i < tr.length; i++) {
        const td = tr[i].getElementsByTagName("td");
        let cellContainsFilter = false; // Reset for each row

        for (let j = 0; j < td.length; j++) {
            const txtValue = td[j].textContent.toUpperCase(); // Using textContent and convert to uppercase here
            if (txtValue.includes(filter)) {
                cellContainsFilter = true; // Found the filter text in one of the cells
                break; // Break as soon as a match is found
            }
        }

        // Show or hide the row based on the presence of the filter text in any cell
        tr[i].style.display = cellContainsFilter ? "" : "none";
    }
}
