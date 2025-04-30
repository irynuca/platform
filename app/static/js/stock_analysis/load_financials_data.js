// --- Load & Render Financial Tables ---
function updateFinancialTable(tabId, data) {
    const container = document.querySelector(`#${tabId} .table-container`);
    if (!container) {
        console.error(`❌ Container not found for tabId: ${tabId}`);
        return;
    }

    console.log("✅ Rendering table for:", tabId, data);

    if (!data || data.length === 0) {
        container.innerHTML = "<p>📊 Date financiare indisponibile.</p>";
        return;
    }

    let allPeriods = new Set();
    data.forEach(row => {
        Object.keys(row.values).forEach(date => allPeriods.add(date));
    });

    let sortedPeriods = Array.from(allPeriods).sort((a, b) => new Date(a) - new Date(b));

    let theadHTML = "<thead class='thead-info'><tr><th class='text-start'>Metric</th>";
    sortedPeriods.forEach(period => {
        theadHTML += `<th class="text-end">${period}</th>`;
    });
    theadHTML += "</tr></thead>";

    let tbodyHTML = "<tbody>";
    data.forEach(row => {
        tbodyHTML += `<tr><td class="text-start">${row.metric_name}</td>`;
        sortedPeriods.forEach(period => {
            const value = row.values[period];
            if (value !== undefined && value !== null && value !== "") {
                tbodyHTML += `<td class="text-end">${Number(value).toLocaleString('en-US', { maximumFractionDigits: 0 })}</td>`;
            } else {
                tbodyHTML += `<td class="text-end">-</td>`;
            }
        });
        tbodyHTML += `</tr>`;
    });
    tbodyHTML += "</tbody>";

    container.innerHTML = `
        <table class="table primary-table-bordered table-hover align-middle text-white freeze-column">
            ${theadHTML}
            ${tbodyHTML}
        </table>
    `;
    applyFrozenColumnToNewTables();
}

window.loadFinancialData = function (tabID, periodType, aggrType, retry = 0) {
    const ticker = STOCK_TICKER;
    let endpoint;

    if (tabID === "pl_statement") endpoint = "pl_data";
    else if (tabID === "balance_sheet") endpoint = "bs_data";
    else if (tabID === "cf_statement") endpoint = "cf_data";
    else {
        console.error(`❌ Unknown tab ID: ${tabID}`);
        return;
    }

    const container = document.querySelector(`#${tabID} .table-container`);
    if (!container) {
        if (retry < 5) {
            console.warn(`⚠️ Container not found, retrying in 100ms... attempt ${retry + 1}`);
            setTimeout(() => loadFinancialData(tabID, periodType, aggrType, retry + 1), 100);
        } else {
            console.error(`❌ Container still not found after retries for tabId: ${tabID}`);
        }
        return;
    }

    console.log("📡 Fetching URL:", `/${endpoint}/${ticker}/${periodType}/${aggrType}`);

    fetch(`/${endpoint}/${ticker}/${periodType}/${aggrType}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`❌ Fetch failed with status ${response.status}`);
            }
            return response.json();
        })
        .then(data => updateFinancialTable(tabID, data))
        .catch(error => console.error("❌ Fetch error:", error));
};
