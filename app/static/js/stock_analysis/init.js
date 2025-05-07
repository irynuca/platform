document.addEventListener("DOMContentLoaded", function () {
    // ✅ Load default chart on page load
    loadStockChart('1y');
    renderRevenueChart();
    renderSegmentRevenueChart();
    renderProfitabilityChart();
    applyFrozenColumnToNewTables(); 

    // ✅ Set up stock chart period buttons
    const periodButtons = document.querySelectorAll(".stock-period-btn");
    periodButtons.forEach(button => {
        const period = button.getAttribute("data-period");
        button.addEventListener("click", () => {
            loadStockChart(period);
        });
    });

    // ✅ Setup financial view buttons (PL, BS, CF)
    const financialButtons = [
        { id: "btn-pl-annual", tab: "pl_statement", type: "annual", aggr: "cml" },
        { id: "btn-pl-quarterly", tab: "pl_statement", type: "quarter", aggr: "qtl" },
        { id: "btn-pl-quarterly-cml", tab: "pl_statement", type: "quarter", aggr: "cml" },
        { id: "btn-bs-annual", tab: "balance_sheet", type: "annual", aggr: "cml" },
        { id: "btn-bs-quarterly-cml", tab: "balance_sheet", type: "quarter", aggr: "cml" },
        { id: "btn-cf-annual", tab: "cf_statement", type: "annual", aggr: "cml" },
        { id: "btn-cf-quarterly", tab: "cf_statement", type: "quarter", aggr: "qtl" },
        { id: "btn-cf-quarterly-cml", tab: "cf_statement", type: "quarter", aggr: "cml" }
    ];

    financialButtons.forEach(({ id, tab, type, aggr }) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener("click", () => {
                loadFinancialData(tab, type, aggr);
            });
        }
    });

    // ✅ Ratios tab buttons
    const ratioButtons = [
        { id: "btn-ratios-annual", type: "annual", aggr: "cml" },
        { id: "btn-ratios-quarter", type: "quarter", aggr: "qtl" },
        { id: "btn-ratios-quarter-cml", type: "quarter", aggr: "cml" }
    ];

    ratioButtons.forEach(({ id, type, aggr }) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.addEventListener("click", () => {
                loadRatiosData(type, aggr);
            });
        }
    });

    document.querySelectorAll('a[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', function (e) {
            const targetTabId = e.target.getAttribute("data-bs-target");

            if (targetTabId === "#summary") {
                console.log("📊 Switched to Summary tab");
                renderRevenueChart();
                renderSegmentRevenueChart();
                renderProfitabilityChart(); 
            }

            else if (targetTabId === "#fundamentale") {
                renderRevenueGrowthChart();
                renderOperatingProfitChart();
                renderNetProfitChart();
                renderAnnualRevenueGrowthChart();

            }

            else if (targetTabId === "#financials") {
                console.log("🔵 Switched to Financials tab");
    
                const container = document.querySelector("#pl_statement .table-container");
                if (container) {
                    container.innerHTML = "<p>📊 Se încarcă datele financiare...</p>";
                }
                loadFinancialData("pl_statement", "annual", "cml");
            }

            else if (targetTabId === "#indicators") {
                console.log("🟢 Switched to Ratios tab");
    
                const container = document.getElementById("accordion-ratios");
                if (container) {
                    container.innerHTML = "<p>📊 Se încarcă indicatorii financiari...</p>";
                }
                loadRatiosData("annual", "cml");
            }

            else if (targetTabId === "#dividends") {
                const el = document.getElementById("dividend-countdown");
                const exDate = el?.dataset?.exdate;
                if (exDate) {initCountdownClock(exDate);}
                renderDPSChart();
                renderDividendYieldChart();
                renderDividendPayoutChart();
                renderDividendtoFCFEChart();
              }              
        });
    });
});

function applyFrozenColumnToNewTables() {
    const tables = document.querySelectorAll('table.freeze-column:not(.table-frozen-column)');
    tables.forEach(table => {
        table.classList.add('table-frozen-column');
        const parent = table.parentElement;
        if (!parent.classList.contains('table-responsive-container')) {
            const container = document.createElement('div');
            container.className = 'table-responsive-container';
            table.parentNode.insertBefore(container, table);
            container.appendChild(table);
        }
    });
}
