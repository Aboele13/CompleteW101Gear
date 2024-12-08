const schoolSelect = document.getElementById('school');
const ownedCheckbox = document.getElementById('owned');
const tableContainer = document.getElementById('table-container');

let sortColumn = null;
let sortOrder = 'asc'; // 'asc' for ascending, 'desc' for descending

const filterForm = document.getElementById('filter-form');
filterForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const school = schoolSelect.value;
    const owned = ownedCheckbox.checked;

    const csvUrl = `https://aboele13.github.io/CompleteW101Gear/Gear/${school}_Gear/${school}_Hats.csv`;

    fetch(csvUrl)
        .then(response => response.text())
        .then(data => {
            const parsedData = Papa.parse(data, { header: true }).data;
            const filteredData = filterCSVData(parsedData, owned);

            console.log('Filtered data:', filteredData);

            displayTable(filteredData);
        })
        .catch(error => {
            console.error('Error fetching or parsing data:', error);
            tableContainer.innerHTML = '<p>Error fetching data. Please try again later.</p>';
        });
});

function filterCSVData(data, owned) {
    return owned ? data.filter(row => row.Owned === 'True') : data;
}

function displayTable(data) {
    tableContainer.innerHTML = '';

    const table = document.createElement('table');

    const headerRow = document.createElement('tr');
    for (const key in data[0]) {
        const headerCell = document.createElement('th');
        headerCell.textContent = key;
        headerCell.addEventListener('click', () => {
            sortColumn = key;
            sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
            displayTable(data);
        });
        headerRow.appendChild(headerCell);
    }
    table.appendChild(headerRow);

    const sortedData = data.sort((a, b) => {
        if (typeof a[sortColumn] === 'number' && typeof b[sortColumn] === 'number') {
            return sortOrder === 'asc' ? a[sortColumn] - b[sortColumn] : b[sortColumn] - a[sortColumn];
        } else {
            return sortOrder === 'asc' ? a[sortColumn].localeCompare(b[sortColumn]) : b[sortColumn].localeCompare(a[sortColumn]);
        }
    });

    sortedData.forEach(row => {
        const dataRow = document.createElement('tr');
        for (const value of Object.values(row)) {
            const dataCell = document.createElement('td');
            dataCell.textContent = value;
            dataRow.appendChild(dataCell);
        }
        table.appendChild(dataRow);
    });

    tableContainer.appendChild(table);
}