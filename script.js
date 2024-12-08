document.getElementById('fetchButton').addEventListener('click', fetchCSV);

function fetchCSV() {
    const school = document.getElementById('school').value;
    const itemType = document.getElementById('itemType').value;
    const url = `https://aboele13.github.io/CompleteW101Gear/Gear/${school}_Gear/${school}_${itemType}.csv`;

    fetch(url)
        .then(response => response.text())
        .then(data => {
            const table = createTable(data);
            document.getElementById('tableContainer').innerHTML = table;
            addSortingListeners();
        })
        .catch(error => {
            console.error('Error fetching the CSV file:', error);
            document.getElementById('tableContainer').innerHTML = '<p>Error fetching the CSV file.</p>';
        });
}

function createTable(csvData) {
    const rows = csvData.split('\n');
    const headers = rows[0].split(',');
    let tableHTML = '<table><thead><tr>';

    headers.forEach(header => {
        tableHTML += `<th>${header}</th>`;
    });

    tableHTML += '</tr></thead><tbody>';

    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].split(',');
        tableHTML += '<tr>';
        cells.forEach(cell => {
            tableHTML += `<td>${cell}</td>`;
        });
        tableHTML += '</tr>';
    }

    tableHTML += '</tbody></table>';
    return tableHTML;
}

function addSortingListeners() {
    const table = document.querySelector('table');
    const headers = table.querySelectorAll('th');

    headers.forEach((header, index) => {
        header.addEventListener('click', () => {
            sortTable(table, index);
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aCell = a.querySelectorAll('td')[columnIndex].textContent;
        const bCell = b.querySelectorAll('td')[columnIndex].textContent;

        return aCell.localeCompare(bCell, undefined, { numeric: true });
    });

    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}