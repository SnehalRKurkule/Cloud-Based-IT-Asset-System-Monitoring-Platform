// -----------Asset Search-----------------
// document.getElementById("assetSearch")
//     .addEventListener("input", filterAssets);

// document.getElementById("statusFilter")
//     .addEventListener("change", filterAssets);


// function filterAssets() {

//     const searchText =
//         document.getElementById("assetSearch")
//         .value
//         .toLowerCase();

//     const status =
//         document.getElementById("statusFilter")
//         .value;

//     const filtered = allAssets.filter(asset => {

//         const matchesSearch =
//             asset.hostname.toLowerCase().includes(searchText) ||
//             asset.ip_address.toLowerCase().includes(searchText);

//         const matchesStatus =
//             status === "ALL" ||
//             asset.status === status;

//         return matchesSearch && matchesStatus;
//     });

//     displayAssets(filtered);
// }


// ------------------------Dashboard-------------------------
async function loadDashboard() {
    const summary = await fetch("/api/dashboard/summary").then(r => r.json());

    document.getElementById("total").textContent = summary.total_assets;
    document.getElementById("healthy").textContent = summary.healthy;
    document.getElementById("warning").textContent = summary.warning;
    document.getElementById("critical").textContent = summary.critical;

    const assets = await fetch("/api/assets").then(r => r.json());
    const rows = [];

    for (const asset of assets) {
        let metrics = [];
        try {
            metrics = await fetch(`/api/assets/${asset.asset_id}/metrics?limit=1`)
                .then(r => r.json());
        } catch (e) {}

        const m = metrics[0];

        rows.push(`
    <tr class="asset-row"
        onclick="window.location.href='/assets/${asset.asset_id}'">
        <td>${asset.hostname}</td>
        <td>${asset.ip_address || "-"}</td>
        <td>${asset.os || "-"}</td>
        <td>${m ? Number(m.cpu_usage).toFixed(1) + "%" : "-"}</td>
        <td>${m ? Number(m.memory_usage).toFixed(1) + "%" : "-"}</td>
        <td>${m ? Number(m.disk_usage).toFixed(1) + "%" : "-"}</td>
        <td class="status ${asset.status}">${asset.status}</td>
        <td>${asset.last_seen || "-"}</td>
    </tr>
`);
    }

    document.getElementById("assetTable").innerHTML =
        rows.join("") || `<tr><td colspan="7">No assets registered yet.</td></tr>`;

    const alerts = await fetch("/api/alerts").then(r => r.json());

    document.getElementById("alertTable").innerHTML =
        alerts.map(a => `
            <tr>
                <td>${a.hostname}</td>
                <td>${a.metric_type}</td>
                <td>${Number(a.metric_value).toFixed(1)}%</td>
                <td>${Number(a.threshold).toFixed(1)}%</td>
                <td class="status ${a.severity}">${a.severity}</td>
                <td class="status ${a.status}">${a.status}</td>
            </tr>
        `).join("") ||
        `<tr><td colspan="6">No alerts.</td></tr>`;
}

loadDashboard();
setInterval(loadDashboard, 10000);


// ------------------------Assets------------------------- 

let allAssets = [];

async function loadAssets() {

    const response = await fetch("/api/assets");

    if (!response.ok) {
        console.error("Failed to load assets");
        return;
    }

    allAssets = await response.json();

    displayAssets(allAssets);
}

function displayAssets(assets) {

    const tableBody = document.getElementById("assetTableBody");

    tableBody.innerHTML = "";

    assets.forEach(asset => {

        const row = document.createElement("tr");

        row.classList.add("asset-row");

        row.innerHTML = `
            
            <td>${asset.hostname}</td>

            <td>${asset.ip_address}</td>

            <td>${asset.os}</td>

            <td>${formatMetric(asset.cpu_usage)}</td>

            <td>${formatMetric(asset.memory_usage)}</td>

            <td>${formatMetric(asset.disk_usage)}</td>

            <td>
                <span class="status ${asset.status.toLowerCase()}">
                    ${asset.status}
                </span>
            </td>

            <td>
                ${formatLastSeen(asset.updated_at)}
            </td>

        `;

        row.addEventListener("click", () => {

            window.location.href =
                `/assets/${asset.asset_id}`;

        });

        tableBody.appendChild(row);
    });
}

function formatMetric(value) {

    if (value === null || value === undefined) {
        return "-";
    }

    return Number(value).toFixed(1) + "%";
}


