/**
 * AI Tuber Platform — GCP Ops Portal
 * API fetch → DOM 描画ロジック
 */

// ── 定数 ──────────────────────────────────────────────
const REFRESH_INTERVAL_MS = 60_000;
const CONSOLE_BASE = 'https://console.cloud.google.com';

// ── ユーティリティ ────────────────────────────────────
function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

function statusHtml(text, tone) {
    return `<span class="status status--${tone}"><span class="status__dot"></span>${text}</span>`;
}

function linkHtml(text, href) {
    return `<a href="${href || '#'}" target="_blank" rel="noopener">${text}</a>`;
}

function toneFor(status) {
    if (['成功', '正常', '完了', 'OK', '稼働中', '有効'].includes(status)) return 'green';
    if (['失敗', 'エラー'].includes(status)) return 'red';
    if (['実行中', 'ビルド中', '起動中'].includes(status)) return 'blue';
    return 'gray';
}

function tableHtml(columns, rows) {
    const ths = columns.map(c => `<th>${c}</th>`).join('');
    const trs = rows.map(row =>
        `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
    ).join('');
    return `
    <div class="data-table"><div class="data-table__wrap">
      <table><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>
    </div></div>`;
}

function errorHtml(msg) {
    return `<div class="error-message">データ取得に失敗しました: ${msg}</div>`;
}

function getConsoleUrl(type, item) {
    const base = `${CONSOLE_BASE}`;
    const p = `project=${projectId}`;
    let url = '#';
    switch (type) {
        case 'scheduler':
            url = `${base}/cloudscheduler/jobs/edit/${item.region}/${item.name}?${p}`;
            break;
        case 'workflow':
            url = `${base}/workflows/workflow/${item.location}/${item.name}/executions?${p}`;
            break;
        case 'execution':
            // 実行詳細画面は単数形の 'execution' かつ末尾に /summary が必要
            url = `${base}/workflows/workflow/${item.location || 'asia-northeast1'}/ai-tuber-streaming-pipeline/execution/${item.executionId}/summary?${p}`;
            break;
        case 'service':
            url = `${base}/run/detail/${item.region}/${item.name}/revisions?${p}`;
            break;
        case 'job':
            url = `${base}/run/jobs/details/${item.region}/${item.name}/executions?${p}`;
            break;
        case 'compute':
            url = `${base}/compute/instancesDetail/zones/${item.zone}/instances/${item.name}?${p}`;
            break;
        case 'build':
            const buildId = item.fullId || item.id;
            url = `${base}/cloud-build/builds/${buildId}?${p}`;
            if (item.region && item.region !== 'global') {
                url += `&region=${item.region}`;
            }
            break;
        case 'trigger':
            url = `${base}/cloud-build/triggers/edit/${item.triggerId || item.triggerName}?${p}`;
            break;
        default:
            url = '#';
    }
    console.log(`[Dashboard] Generated ${type} link:`, url);
    return url;
}

// ── API Fetch ─────────────────────────────────────────
async function api(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
}

// ── Quick Links (静的) ────────────────────────────────
let projectId = 'ren-studio-ai';

function renderQuickLinks() {
    const links = [
        ['Cloud Run Services', '本番サービス一覧を開く', `${CONSOLE_BASE}/run?project=${projectId}`],
        ['Cloud Run Jobs', 'Job 実行履歴を開く', `${CONSOLE_BASE}/run/jobs?project=${projectId}`],
        ['Cloud Workflows', 'Executions 画面へ', `${CONSOLE_BASE}/workflows?project=${projectId}`],
        ['Cloud Build', 'Build History へ', `${CONSOLE_BASE}/cloud-build/builds?project=${projectId}`],
        ['Logs Explorer', '障害調査の入口', `${CONSOLE_BASE}/logs?project=${projectId}`],
        ['Monitoring', 'アラートと指標', `${CONSOLE_BASE}/monitoring?project=${projectId}`],
    ];
    const el = $('#quicklinks');
    if (el) {
        el.innerHTML = links.map(([title, desc, href]) => `
      <a class="quicklink" href="${href}" target="_blank" rel="noopener">
        <div class="quicklink__title">${title}</div>
        <div class="quicklink__desc">${desc}</div>
      </a>
    `).join('');
    }
}

// ── Overview 描画 ─────────────────────────────────────
async function loadOverview() {
    try {
        const data = await api('/api/overview');
        setMetric('mc-scheduler', data.schedulerHealth.value, data.schedulerHealth.detail);
        setMetric('mc-workflow', data.workflowState.value, data.workflowState.detail);
        setMetric('mc-resources', data.runningResources.value, data.runningResources.detail);
        setMetric('mc-ips', data.externalIps.value, data.externalIps.detail);
        // 全体ステータス
        const badge = $('#overall-status');
        if (badge) {
            const allOk = data.schedulerHealth.value === 'OK' && data.workflowState.value === '正常';
            badge.textContent = allOk ? '正常' : 'エラー';
            badge.className = `badge ${allOk ? 'badge--green' : 'badge--red'}`;
        }
    } catch (err) {
        console.error('overview error:', err);
    }
}

function setMetric(id, value, sub) {
    const el = $(`#${id}`);
    if (!el) return;
    el.querySelector('.metric-card__value').textContent = value;
    el.querySelector('.metric-card__sub').textContent = sub;
}

// ── Scheduler 描画 ────────────────────────────────────
async function loadScheduler() {
    const container = $('#card-scheduler .card__body');
    try {
        const jobs = await api('/api/scheduler');
        if (!jobs.length) { container.innerHTML = '<p class="loading-placeholder">ジョブなし</p>'; return; }
        container.innerHTML = `
      <div class="filter-bar"><span>フィルタ</span><span class="filter-bar__input">ジョブのフィルタ</span></div>
      ${tableHtml(
            ['名前', '最後の実行のステータス', 'リージョン', '状態', '説明', '頻度', 'ターゲット'],
            jobs.map(j => [
                `<div><strong>${linkHtml(j.name, getConsoleUrl('scheduler', j))}</strong><div style="margin-top:4px;font-size:11px;color:var(--gray-500)">Cloud Scheduler</div></div>`,
                statusHtml(j.lastStatus, toneFor(j.lastStatus)),
                j.region,
                j.state,
                j.description,
                j.schedule,
                linkHtml(j.target, j.target),
            ])
        )}`;
    } catch (err) { container.innerHTML = errorHtml(err.message); }
}

// ── Workflows 描画 ────────────────────────────────────
async function loadWorkflows() {
    const container = $('#card-workflows .card__body');
    try {
        const { workflows, executions } = await api('/api/workflows');
        const wf = workflows[0];
        const latestExec = executions[0];
        let html = '';

        if (wf) {
            html += `
        <div class="wf-detail">
          <div class="wf-detail__header">
            <div>ワークフロー: ${linkHtml(wf.name, getConsoleUrl('workflow', wf))}</div>
            ${latestExec ? statusHtml('現在状態: ' + (latestExec.status === '成功' ? '正常' : latestExec.status), toneFor(latestExec.status)) : ''}
          </div>
          <div class="wf-detail__grid">
            <div><div>場所</div><div class="val">${wf.location}</div></div>
            <div><div>最新のリビジョン</div><div class="val">${wf.revision}</div></div>
            <div><div>直近実行</div><div class="val">${latestExec ? latestExec.created : '—'}</div></div>
            <div><div>ラベル</div><div class="val">${wf.labels}</div></div>
          </div>
        </div>`;
        }

        html += `<div class="filter-bar"><span>フィルタ</span><span class="filter-bar__input">実行をフィルタ</span></div>`;
        html += tableHtml(
            ['状態', '実行 ID', 'ワークフローのリビジョン', '作成日時', '開始時刻', '終了時間'],
            executions.map(ex => [
                `<div style="display:flex;align-items:center;gap:8px">
          <span class="status__dot" style="width:10px;height:10px;border-radius:50%;background:${ex.status === '成功' ? 'var(--green)' : 'var(--red)'}"></span>
          <span class="exec-tag">${ex.stepName || 'end'}</span>
          <span style="font-size:12px;font-weight:500;color:${ex.status === '成功' ? 'var(--green)' : 'var(--red)'}">${ex.status}</span>
        </div>`,
                linkHtml(ex.executionId, getConsoleUrl('execution', ex)),
                ex.revision,
                ex.created,
                ex.started,
                ex.ended,
            ])
        );
        container.innerHTML = html;
    } catch (err) { container.innerHTML = errorHtml(err.message); }
}

// ── Resources (Services + Jobs + Compute) 描画 ───────
async function loadResources() {
    const container = $('#card-resources .card__body');
    try {
        const [svcData, instances] = await Promise.all([
            api('/api/services'),
            api('/api/compute'),
        ]);

        let html = '';

        // Cloud Run Services
        html += '<div class="resource-label">Cloud Run</div>';
        html += tableHtml(
            ['状態', '名前', 'リージョン', '認証', 'Ingress', 'リンク'],
            svcData.services.map(s => [
                statusHtml(s.status, toneFor(s.status)),
                linkHtml(s.name, getConsoleUrl('service', s)),
                s.region,
                s.authentication,
                s.ingress,
                `<div style="display:flex;gap:12px;font-size:11px">${linkHtml('Service', s.uri)}${linkHtml('Logs', `${CONSOLE_BASE}/logs?project=${projectId}`)}</div>`,
            ])
        );

        // Cloud Run Jobs
        html += '<div class="resource-label" style="margin-top:16px">Job</div>';
        html += tableHtml(
            ['状態', '名前', '最終実行', 'リージョン', '起点'],
            svcData.jobs.map(j => [
                statusHtml(j.status, toneFor(j.status)),
                linkHtml(j.name, getConsoleUrl('job', j)),
                j.lastExecution,
                j.region,
                j.trigger,
            ])
        );

        // Compute
        html += '<div class="resource-label" style="margin-top:16px">Compute</div>';
        html += tableHtml(
            ['状態', '名前', 'ゾーン', '内部 IP', '外部 IP', '用途'],
            instances.map(vm => [
                statusHtml(vm.status, toneFor(vm.status)),
                linkHtml(vm.name, getConsoleUrl('compute', vm)),
                vm.zone,
                `<strong>${vm.internalIp}</strong>`,
                `<strong>${vm.externalIp}</strong>`,
                vm.description,
            ])
        );

        container.innerHTML = html;
    } catch (err) { container.innerHTML = errorHtml(err.message); }
}

// ── Builds 描画 ───────────────────────────────────────
async function loadBuilds() {
    const container = $('#card-builds .card__body');
    try {
        const builds = await api('/api/builds');
        container.innerHTML = `
      <div class="filter-bar"><span>フィルタ</span><span class="filter-bar__input">プロパティ名または値を入力</span></div>
      ${tableHtml(
            ['ステータス', 'ビルド', 'リージョン', 'ソース', 'Ref', 'commit', 'トリガー名'],
            builds.map(b => [
                statusHtml(b.status, toneFor(b.status)),
                linkHtml(b.id, getConsoleUrl('build', b)),
                b.region,
                linkHtml(b.source, '#'),
                b.ref,
                linkHtml(b.commit, '#'),
                linkHtml(b.triggerName, getConsoleUrl('trigger', b)),
            ])
        )}`;
    } catch (err) { container.innerHTML = errorHtml(err.message); }
}

// ── Detail-Tab 描画 ───────────────────────────────────
async function loadDetailServices() {
    const svcEl = $('#detail-services');
    const jobEl = $('#detail-jobs');
    try {
        const data = await api('/api/services');
        svcEl.innerHTML = tableHtml(
            ['状態', '名前', 'リージョン', '認証', 'Ingress', 'URI'],
            data.services.map(s => [
                statusHtml(s.status, toneFor(s.status)),
                linkHtml(s.name, getConsoleUrl('service', s)),
                s.region, s.authentication, s.ingress,
                linkHtml(s.uri, s.uri),
            ])
        );
        jobEl.innerHTML = tableHtml(
            ['状態', '名前', '最終実行', 'リージョン', '起点'],
            data.jobs.map(j => [
                statusHtml(j.status, toneFor(j.status)),
                linkHtml(j.name, getConsoleUrl('job', j)),
                j.lastExecution, j.region, j.trigger,
            ])
        );
    } catch (err) {
        svcEl.innerHTML = errorHtml(err.message);
        jobEl.innerHTML = '';
    }
}

async function loadDetailJobs() {
    const el = $('#detail-jobs-full');
    try {
        const data = await api('/api/services');
        el.innerHTML = tableHtml(
            ['状態', '名前', '最終実行', 'リージョン', 'トリガー', '作成者'],
            data.jobs.map(j => [
                statusHtml(j.status, toneFor(j.status)),
                linkHtml(j.name, getConsoleUrl('job', j)),
                j.lastExecution, j.region, j.trigger, j.creator,
            ])
        );
    } catch (err) { el.innerHTML = errorHtml(err.message); }
}

async function loadDetailWorkflows() {
    try {
        const { workflows, executions } = await api('/api/workflows');
        const wfEl = $('#detail-workflows');
        wfEl.innerHTML = tableHtml(
            ['名前', '場所', 'リビジョン', '作成日', '更新日', 'ラベル'],
            workflows.map(w => [
                linkHtml(w.name, getConsoleUrl('workflow', w)), w.location, w.revision, w.created, w.updated, w.labels,
            ])
        );
        const exEl = $('#detail-executions');
        exEl.innerHTML = tableHtml(
            ['状態', '実行 ID', 'リビジョン', '作成日時', '開始時刻', '終了時間'],
            executions.map(ex => [
                statusHtml(ex.status, toneFor(ex.status)),
                linkHtml(ex.executionId, getConsoleUrl('execution', ex)),
                ex.revision, ex.created, ex.started, ex.ended,
            ])
        );
    } catch (err) {
        $('#detail-workflows').innerHTML = errorHtml(err.message);
    }
}

async function loadDetailCompute() {
    const el = $('#detail-compute');
    try {
        const instances = await api('/api/compute');
        el.innerHTML = tableHtml(
            ['状態', '名前', 'ゾーン', '内部 IP', '外部 IP', '用途'],
            instances.map(vm => [
                statusHtml(vm.status, toneFor(vm.status)),
                linkHtml(vm.name, getConsoleUrl('compute', vm)),
                vm.zone, `<strong>${vm.internalIp}</strong>`, `<strong>${vm.externalIp}</strong>`, vm.description,
            ])
        );
    } catch (err) { el.innerHTML = errorHtml(err.message); }
}

async function loadDetailBuilds() {
    const el = $('#detail-builds-full');
    try {
        const builds = await api('/api/builds');
        el.innerHTML = tableHtml(
            ['ステータス', 'ビルド', 'リージョン', 'ソース', 'Ref', 'commit', 'トリガー名'],
            builds.map(b => [
                statusHtml(b.status, toneFor(b.status)),
                linkHtml(b.id, getConsoleUrl('build', b)), b.region, linkHtml(b.source, '#'),
                b.ref, linkHtml(b.commit, '#'), linkHtml(b.triggerName, getConsoleUrl('trigger', b)),
            ])
        );
    } catch (err) { el.innerHTML = errorHtml(err.message); }
}

// ── Tab 切替 ──────────────────────────────────────────
const tabLoaders = {
    overview: () => Promise.all([loadOverview(), loadScheduler(), loadWorkflows(), loadResources()]),
    services: loadDetailServices,
    jobs: loadDetailJobs,
    workflows: loadDetailWorkflows,
    compute: loadDetailCompute,
    builds: loadDetailBuilds,
};

let activeTab = 'overview';

function switchTab(name) {
    activeTab = name;
    $$('.tab').forEach(t => t.classList.toggle('tab--active', t.dataset.tab === name));
    $$('.tab-panel').forEach(p => p.classList.toggle('hidden', p.id !== `panel-${name}`));
    const loader = tabLoaders[name];
    if (loader) loader();
}

// ── 初期化 ────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    // プロジェクトID取得
    try {
        const cfg = await api('/api/config');
        projectId = cfg.projectId;
        const projectEl = $('#project-id');
        if (projectEl) projectEl.textContent = projectId;
        const consoleBtn = $('#btn-console');
        if (consoleBtn) consoleBtn.href = `${CONSOLE_BASE}/home/dashboard?project=${projectId}`;
    } catch (e) { /* ignore */ }

    // Quick Links は概要から削除されたため非表示
    // renderQuickLinks();

    // Tab イベント
    $$('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // 更新ボタン
    const refreshBtn = $('#btn-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            const loader = tabLoaders[activeTab];
            if (loader) loader();
        });
    }

    // 初期ロード
    switchTab('overview');

    // 自動リフレッシュ
    setInterval(() => {
        const loader = tabLoaders[activeTab];
        if (loader) loader();
    }, REFRESH_INTERVAL_MS);
});
