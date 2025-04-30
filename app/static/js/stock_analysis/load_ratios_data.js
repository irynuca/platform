// --- Load and Render Ratios Accordion ---

window.loadRatiosData = function (periodType, aggrType) {
    const ticker = STOCK_TICKER;

    const url = `/ratios_data/${ticker}/${periodType}/${aggrType}`;
    console.log("📡 Fetching ratios from:", url);

    fetch(url)
        .then(response => response.json())
        .then(data => updateRatiosTable(data))
        .catch(error => console.error("❌ Error loading ratios", error));
};

function updateRatiosTable(data) {
    const container = document.getElementById("accordion-ratios");
    if (!container) {
        console.warn("⚠️ 'accordion-ratios' container not found");
        return;
    }

    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = "<p>📊 Nicio informație disponibilă.</p>";
        return;
    }

    // Build accordion content
    container.innerHTML = "";

    let index = 0;
    for (const [category, statement] of Object.entries(data)) {
        index++;
        const collapseId = `collapse_ratio_${index}`;
        const headerId = `accord_ratio_${index}`;

        let allPeriods = new Set();
        statement.forEach(r => {
            Object.keys(r.values).forEach(p => allPeriods.add(p));
        });
        let sortedPeriods = Array.from(allPeriods).sort((a, b) => new Date(a) - new Date(b));

        // Build table header
        let thead = `<thead><tr><th class="text-start">Indicator</th>`;
        sortedPeriods.forEach(p => {
            thead += `<th class="text-end">${p}</th>`;
        });
        thead += `</tr></thead>`;

        // Build table body
        let tbody = `<tbody>`;
        statement.forEach(row => {
            tbody += `<tr><td class="text-start">${row.metric_name}</td>`;
            sortedPeriods.forEach(p => {
                const value = p in row.values ? `${(parseFloat(row.values[p])).toFixed(2)}%` : 'n.a.';
                tbody += `<td class="text-end">${value}</td>`;
            });
            tbody += `</tr>`;
        });
        tbody += `</tbody>`;

        // Accordion section
        container.innerHTML += `
            <div class="accordion-item">
                <div class="accordion-header rounded-lg"
                        id="${headerId}"
                        data-bs-toggle="collapse"
                        data-bs-target="#${collapseId}"
                        aria-expanded="true"
                        aria-controls="${collapseId}"
                        role="button">
                    <span class="accordion-header-text">${category}</span>
                </div>

                <div id="${collapseId}" class="collapse accordion__body"
                     aria-labelledby="${headerId}"
                     data-bs-parent="#accordion-ratios">
                    <div class="table-responsive custom-scroll-wrapper text-white">
                        <div class="table-container">
                            <table class="table border-0 table-striped align-middle text-white freeze-column">
                                ${thead}
                                ${tbody}
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}
