// Register global Chart.js plugins
Chart.register(ChartDataLabels);

window.createBarChart = function ({
    canvasId,
    labels,
    values,
    label = "Valori",
    backgroundColor = "#53CAFD",
    hoverColor = "#45B3E2",
    maxY = null,
    stepY = null,
    tooltipLabel = null
}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return console.error(`❌ Canvas "${canvasId}" not found`);
    const ctx = canvas.getContext("2d");

    if (window[canvasId + "Instance"]) {
        window[canvasId + "Instance"].destroy();
    }

    Chart.defaults.font.family = 'Poppins';

    const maxVal = Math.max(...values);
    const niceMax = maxY || Math.ceil(maxVal / 100) * 100;
    const step = stepY || Math.ceil(niceMax / 4);
    const roundedMax = Math.ceil(niceMax / step) * step;

    window[canvasId + "Instance"] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label,
                data: values,
                backgroundColor,
                hoverBackgroundColor: hoverColor,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: {
                    beginAtZero: true,
                    max: roundedMax,
                    ticks: {
                        stepSize: step,
                        color: '#fff',
                        callback: v => `${v.toLocaleString("en-US", { maximumFractionDigits: 0 })} mn`
                    },
                    border: {
                        display: true,
                        color: 'rgba(255,255,255,0.3)',
                        width: 1
                    }
                },
                x: {
                    ticks: { color: '#fff' },
                    grid: { drawOnChartArea: false, drawTicks: false },
                    border: {
                        display: true,
                        color: 'rgba(255,255,255,0.3)',
                        width: 1
                    }
                }
            },
            plugins: {
                datalabels: { display: false },
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(240,240,240,0.2)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderWidth: 0,
                    titleFont: { weight: 'bold' },
                    bodyFont: { weight: 'bold' },
                    callbacks: {
                        label: ctx => {
                            if (tooltipLabel) return tooltipLabel(ctx);
                            return `${ctx.dataset.label}: ${ctx.raw.toLocaleString("en-US", { minimumFractionDigits: 1 })} mnRON`;
                        }
                    }
                }
            }
        }
    });
};

window.createDonutChart = function ({
    canvasId,
    labels,
    values,
    backgroundColors = [],
    centerLabel = "",
    tooltipFormatter = null
}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return console.error(`❌ Canvas "${canvasId}" not found`);

    const ctx = canvas.getContext("2d");

    if (window[canvasId + "Instance"]) {
        window[canvasId + "Instance"].destroy();
    }

    window[canvasId + "Instance"] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderWidth: 0
            }]
        },
        options: {
            cutout: '60%',
            rotation: 35,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff',
                        font: { size: 12, weight: 'bold', family: 'Poppins' },
                        padding: 12,
                        boxWidth: 16
                    }
                },
                datalabels: {
                    color: '#fff',
                    font: { size: 14, weight: 'bold' },
                    align: 'end',
                    anchor: 'end',
                    offset: 14,
                    formatter: (value, ctx) => {
                        const total = ctx.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        return `${((value / total) * 100).toFixed(1)}%`;
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(240,240,240,0.2)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderWidth: 0,
                    callbacks: {
                        label: tooltipFormatter || ((ctx) =>
                            `${ctx.label}: ${ctx.raw.toLocaleString("en-US", { maximumFractionDigits: 1 })} RON`)
                    }
                }
            }
        }
    });

    // Update center label
    const center = document.getElementById("donutCenterLabel");
    if (center) {
        center.textContent = centerLabel;
    }
};

window.createBarLineChart = function ({
    canvasId,
    labels,
    barDataset,
    lineDataset,
    yAxisOptions = {},
    y1AxisOptions = {},
    tooltipFormatter = null
}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return console.error(`❌ Canvas ${canvasId} not found`);
    const ctx = canvas.getContext("2d");

    if (window[canvasId + "Instance"]) {
        window[canvasId + "Instance"].destroy();
    }

    Chart.defaults.font.family = "Poppins";

    window[canvasId + "Instance"] = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [
                { ...barDataset },
                { ...lineDataset }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            scales: {
                y: {
                    beginAtZero: true,
                    ...yAxisOptions,
                    ticks: {
                        color: "#fff",
                        ...yAxisOptions?.ticks
                    },
                    border: {
                        display: true,
                        color: "rgba(255,255,255,0.3)",
                        width: 1,
                        ...yAxisOptions?.border
                    }
                },
                y1: {
                    beginAtZero: true,
                    position: "right",
                    ...y1AxisOptions,
                    ticks: {
                        color: "#fff",
                        ...y1AxisOptions?.ticks
                    },
                    grid: { drawOnChartArea: false, drawTicks: false },
                    border: {
                        display: true,
                        color: "rgba(255,255,255,0.3)",
                        width: 1,
                        ...y1AxisOptions?.border
                    }
                },
                x: {
                    ticks: { color: "#fff" },
                    grid: { drawOnChartArea: false, drawTicks: false },
                    border: {
                        display: true,
                        color: "rgba(255,255,255,0.3)",
                        width: 1
                    }
                }
            },
            plugins: {
                datalabels: { display: false },
                legend: {
                    display: true,
                    position: "top",
                    align: "center",
                    labels: {
                        color: "#fff",
                        font: { size: 12, family: "Poppins" },
                        padding: 10,
                        boxWidth: 20
                    }
                },
                tooltip: {
                    backgroundColor: "rgba(240,240,240,0.2)",
                    titleColor: "#fff",
                    bodyColor: "#fff",
                    borderWidth: 0,
                    titleFont: { weight: "bold" },
                    bodyFont: { weight: "bold" },
                    callbacks: {
                        label: tooltipFormatter || function (ctx) {
                            const label = ctx.dataset.label || "";
                            return `${label}: ${ctx.raw}`;
                        }
                    }
                }
            }
        }
    });
};

window.createLineChart = function ({
    canvasId,
    labels,
    values,
    label = "Valori",
    borderColor = "#53CAFD",
    pointColor = "#53CAFD",
    backgroundColor = "transparent",
    maxY = null,
    stepY = null,
    tooltipLabel = null
}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return console.error(`❌ Canvas "${canvasId}" not found`);
    const ctx = canvas.getContext("2d");

    // Destroy previous instance if it exists
    if (window[canvasId + "Instance"]) {
        window[canvasId + "Instance"].destroy();
    }

    Chart.defaults.font.family = "Poppins";

    // Auto-scale y-axis
    const maxVal = Math.max(...values);
    const niceMax = maxY || Math.ceil(maxVal * 1.1 * 100) / 100;
    const step = stepY || Math.ceil(niceMax / 4 * 100) / 100;
    const roundedMax = Math.ceil(niceMax / step) * step;

    // Create the gradient for the line fill
    const gradientFill = ctx.createLinearGradient(0, 0, 0, ctx.canvas.clientHeight);
    gradientFill.addColorStop(0, pointColor + "CC"); // 80% opacity
    gradientFill.addColorStop(1, pointColor + "00"); // 0% opacity

    window[canvasId + "Instance"] = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label,
                data: values,
                fill: true,
                borderColor,
                backgroundColor: gradientFill,
                tension: 0.3,
                pointRadius: 5,
                pointHoverRadius: 7,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 2000,
                easing: 'easeOutQuart'
            },
            interaction: { mode: "index", intersect: false },
            scales: {
                y: {
                    beginAtZero: true,
                    max: roundedMax,
                    ticks: {
                        stepSize: step,
                        color: "#fff",
                        callback: v => `${v.toFixed(2)}%`
                    },
                    border: {
                        display: true,
                        color: "rgba(255,255,255,0.3)",
                        width: 1
                    }
                },
                x: {
                    ticks: { color: "#fff" },
                    grid: { drawOnChartArea: false, drawTicks: false },
                    border: {
                        display: true,
                        color: "rgba(255,255,255,0.3)",
                        width: 1
                    }
                }
            },
            plugins: {
                datalabels: { display: false },
                legend: {
                    display: true,
                    position: "top",
                    labels: {
                        color: "#fff",
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    backgroundColor: "rgba(240,240,240,0.8)",
                    titleColor: "#fff",
                    bodyColor: "#fff",
                    borderWidth: 0,
                    titleFont: { weight: "bold" },
                    bodyFont: { weight: "bold" },
                    callbacks: {
                        label: tooltipLabel || (ctx => `${ctx.dataset.label}: ${ctx.raw.toFixed(2)}%`)
                    }
                }
            }
        }
    });
};
