const tableBody = document.getElementById('tableBody');
const visibleCount = document.getElementById('visibleCount');
const leagueFilter = document.getElementById('leagueFilter');
const quickFilter = document.getElementById('quickFilter');
const sortMode = document.getElementById('sortMode');
const ctx = document.getElementById('probChart').getContext('2d');

function mainRows() {
    return Array.from(document.querySelectorAll('.match-row'));
}

function parseProbability(text) {
    const match = text.match(/([0-9.]+)%/);
    return match ? Number(match[1]) : 0;
}

function pairedDetail(row) {
    return document.getElementById(`detail-${row.dataset.index}`);
}

function rowVisible(row) {
    const leagueOk = leagueFilter.value === 'all' || row.dataset.league === leagueFilter.value;
    let quickOk = true;
    if (quickFilter.value === 'risk-a') quickOk = row.dataset.risk === 'A';
    if (quickFilter.value === 'risk-b') quickOk = row.dataset.risk === 'B';
    if (quickFilter.value === 'risk-c') quickOk = row.dataset.risk === 'C';
    if (quickFilter.value === 'combo') quickOk = row.dataset.combo === '1';
    if (quickFilter.value === 'upset') quickOk = row.dataset.upset === '有';
    return leagueOk && quickOk;
}

function sortRows(rows) {
    const riskRank = { A: 1, B: 2, C: 3 };
    rows.sort((a, b) => {
        if (sortMode.value === 'risk') return riskRank[a.dataset.risk] - riskRank[b.dataset.risk];
        if (sortMode.value === 'value') return Number(b.dataset.value) - Number(a.dataset.value);
        return a.dataset.time.localeCompare(b.dataset.time, 'zh-CN');
    });
    rows.forEach(row => {
        const detail = pairedDetail(row);
        tableBody.appendChild(row);
        tableBody.appendChild(detail);
    });
}

function drawChart(rows) {
    const labels = [];
    const probH = [];
    const probD = [];
    const probA = [];
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        labels.push(cells[2].innerText.replace(/\s+/g, ' '));
        probH.push(parseProbability(cells[3].querySelector('.win').innerText));
        probD.push(parseProbability(cells[3].querySelector('.draw').innerText));
        probA.push(parseProbability(cells[3].querySelector('.lose').innerText));
    });
    if (window.probabilityChart) window.probabilityChart.destroy();
    window.probabilityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: '主胜概率', data: probH, backgroundColor: 'rgba(20, 184, 166, 0.82)', borderRadius: 5 },
                { label: '平局概率', data: probD, backgroundColor: 'rgba(234, 179, 8, 0.82)', borderRadius: 5 },
                { label: '客胜概率', data: probA, backgroundColor: 'rgba(248, 113, 113, 0.82)', borderRadius: 5 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: '#cbd5e1', boxWidth: 10, font: { size: 11 } } } },
            scales: {
                x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(148, 163, 184, 0.08)' } },
                y: { beginAtZero: true, max: 100, ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { color: 'rgba(148, 163, 184, 0.10)' } }
            }
        }
    });
}

function applyView() {
    const rows = mainRows();
    sortRows(rows);
    const filtered = [];
    rows.forEach(row => {
        const show = rowVisible(row);
        const detail = pairedDetail(row);
        row.classList.toggle('hidden', !show);
        if (!show) detail.classList.remove('open');
        detail.classList.toggle('hidden', !show);
        if (show) filtered.push(row);
    });
    visibleCount.innerText = filtered.length;
    drawChart(filtered);
}

function setActive(buttons, active) {
    buttons.forEach(button => button.classList.toggle('active', button === active));
}

document.querySelectorAll('.detail-button').forEach(button => {
    button.addEventListener('click', () => {
        const detail = document.getElementById(button.dataset.target);
        detail.classList.toggle('open');
        button.textContent = detail.classList.contains('open') ? '收起详情' : '深度分析详情';
    });
});

document.querySelectorAll('[data-density]').forEach(button => {
    button.addEventListener('click', () => {
        document.body.classList.toggle('compact', button.dataset.density === 'compact');
        document.body.classList.toggle('standard', button.dataset.density === 'standard');
        setActive(Array.from(document.querySelectorAll('[data-density]')), button);
    });
});

document.querySelectorAll('[data-font]').forEach(button => {
    button.addEventListener('click', () => {
        document.body.classList.remove('font-small', 'font-medium', 'font-large');
        document.body.classList.add(`font-${button.dataset.font}`);
        setActive(Array.from(document.querySelectorAll('[data-font]')), button);
    });
});

[leagueFilter, quickFilter, sortMode].forEach(element => element.addEventListener('change', applyView));
applyView();
