const schoolSelect = document.getElementById('school');
const ownedCheckbox = document.getElementById('owned');
const tableContainer = document.getElementById('table-container');

const filterForm = document.getElementById('filter-form');
filterForm.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent default form submission

    const school = schoolSelect.value;
    const owned = ownedCheckbox.checked;

    // Build the CSV file URL based on user selection
    const csvUrl = `https://aboele13.github.io/CompleteW101Gear/Gear/${school}_Gear/${school}_Hats.csv`;

    // Fetch CSV data
    fetch(csvUrl)
        .then(response => response.text())
        .then(data => {
            const filteredData = filterCSVData(data, owned);
            displayTable(filteredData);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            // Handle errors appropriately (e.g., display error message to user)
        });
});

// Function to filter CSV data based on 'Owned' checkbox
function filterCSVData(data, owned) {
    const parsedData = Papa.parse(data, { header: true }).data;
    return owned ? parsedData.filter(row => row.Owned === 'True') : parsedData;
}

// Function to display the filtered data in a table
function displayTable(data) {
    tableContainer.innerHTML = ''; // Clear previous table

    // Create table element
    const table = document.createElement('table');

    // Add table headers
    const headerRow = document.createElement('tr');
    for (const key in data[0]) {
        const headerCell = document.createElement('th');
        headerCell.textContent = key;
        headerRow.appendChild(headerCell);
    }
    table.appendChild(headerRow);

    // Add data rows
    for (const row of data) {
        const dataRow = document.createElement('tr');
        for (const value of Object.values(row)) { // Iterate through row values
            const dataCell = document.createElement('td');
            dataCell.textContent = value;
            dataRow.appendChild(dataCell);
        }
        table.appendChild(dataRow);
    }

    tableContainer.appendChild(table);
}