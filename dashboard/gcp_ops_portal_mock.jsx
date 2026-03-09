export default function GcpOpsPortalMock() {
  const schedulerJobs = [
    {
      name: 'ai-tuber-workflow-daily',
      lastStatus: '成功',
      region: 'asia-northeast1',
      state: '有効',
      description: 'Triggers the streaming pipeline workflow daily',
      schedule: '00 08 * * *',
      target: 'https://workflowexecutions.googleapis.com/v1/projects/ren-studio-ai/locations/asia-northeast1/workflows/ai-tuber-streaming-pipeline',
    },
  ];

  const workflowExecutions = [
    ['end', '成功', 'b99c1714-1e09-4d42-a388-de222b9ecb18', '000014-a15', '2026/03/08 16:53:01', '2026/03/08 16:53:01', '2026/03/08 17:09:37'],
    ['end', '成功', '25c27a37-d573-4360-ba68-544e53a27296', '000014-a15', '2026/03/08 15:07:00', '2026/03/08 15:07:00', '2026/03/08 15:23:55'],
    ['end', '成功', '96de7484-66b9-4886-bcc5-8750e4109562', '000014-a15', '2026/03/08 14:30:44', '2026/03/08 14:30:44', '2026/03/08 14:44:53'],
    ['end', '成功', '22289f50-4895-4658-88dc-6b2a17d8c947', '000014-a15', '2026/03/08 08:00:03', '2026/03/08 08:00:03', '2026/03/08 08:16:13'],
    ['end', '成功', '170d6c03-9e2b-4116-beac-56d88e80b192', '000014-a15', '2026/03/07 08:00:03', '2026/03/07 08:00:03', '2026/03/07 08:20:55'],
    ['end', '成功', 'd15e5e8a-4cfc-40e7-b816-491635a32302', '000014-a15', '2026/03/06 08:00:03', '2026/03/06 08:00:03', '2026/03/06 08:19:07'],
    ['stop_body_node', '失敗', 'd633b4cb-e9dc-4b5f-9c0b-8f28b451c6de', '000014-a15', '2026/03/06 01:34:43', '2026/03/06 01:34:43', '2026/03/06 01:52:14'],
  ];

  const workflows = [
    {
      name: 'ai-tuber-streaming-pipeline',
      location: 'asia-northeast1',
      revision: '000014-a15',
      created: '2026/02/11 12:32',
      updated: '2026/03/06 03:03',
      labels: 'managed-by: openfuto',
    },
  ];

  const builds = [
    ['e60ea1c3', 'global', 'koduki/ai-tuber', 'dev/bugfix', 'c49e1a7d', 'ai-tuber-saint-graph'],
    ['21352b1c', 'global', 'koduki/ai-tuber', 'dev/bugfix', 'c49e1a7d', 'ai-tuber-body'],
    ['d99ebb9d', 'global', 'koduki/ai-tuber', 'main', '3798f4ed', 'ai-tuber-mind-data-sync'],
    ['9356c659', 'global', 'koduki/ai-tuber', 'main', '5aa3945c', 'ai-tuber-saint-graph'],
    ['2402e724', 'global', 'koduki/ai-tuber', 'main', 'ce0383d2', 'ai-tuber-body'],
    ['82dfc26d', 'global', 'koduki/ai-tuber', 'main', '2db306a2', 'ai-tuber-body'],
  ];

  const jobs = [
    ['ai-tuber-news-collector', '完了', '2026/03/08 16:53:02', 'asia-northeast1', '$0.21', 'pascalma3@gmail.com', 'Cloud Scheduler'],
    ['ai-tuber-saint-graph', '完了', '2026/03/08 16:55:56', 'asia-northeast1', '$1.06', 'pascalma3@gmail.com', 'Manual'],
  ];

  const services = [
    ['ai-tuber-healthcheck-proxy', '正常', 'コンテナ', '0', 'asia-northeast1', '$1.17', '認証が必要です', 'すべて'],
    ['ai-tuber-tools-weather', '正常', 'コンテナ', '0.01', 'asia-northeast1', '$1.50', '公開アクセス', 'すべて'],
  ];

  const computeInstances = [
    ['ai-tuber-body-node', '稼働中', 'asia-northeast1-a', '10.0.0.3 (nic0)', '35.243.69.228 (nic0)', 'Body 接続確認用'],
  ];

  const navItems = ['概要', 'サービス', 'ジョブ', 'Workflows', 'Compute', 'ビルド', 'コスト'];

  const Card = ({ title, action, children, className = '' }) => (
    <section className={`overflow-hidden rounded-md border border-[#dadce0] bg-white ${className}`}>
      {title || action ? (
        <div className="flex items-center justify-between border-b border-[#e8eaed] px-4 py-3">
          <h2 className="text-[14px] font-medium text-[#202124]">{title}</h2>
          {action ? (
            <button className="text-[12px] font-medium text-[#1a73e8] hover:underline">{action}</button>
          ) : null}
        </div>
      ) : null}
      <div className="p-4">{children}</div>
    </section>
  );

  const StatusDot = ({ tone = 'green' }) => {
    const tones = {
      green: 'bg-[#1e8e3e]',
      blue: 'bg-[#1a73e8]',
      amber: 'bg-[#f29900]',
      gray: 'bg-[#5f6368]',
      red: 'bg-[#d93025]',
    };
    return <span className={`inline-block h-2.5 w-2.5 rounded-full ${tones[tone]}`} />;
  };

  const StatusText = ({ children, tone = 'green' }) => {
    const tones = {
      green: 'text-[#1e8e3e]',
      blue: 'text-[#1a73e8]',
      amber: 'text-[#b06000]',
      gray: 'text-[#5f6368]',
      red: 'text-[#d93025]',
    };

    return (
      <span className={`inline-flex items-center gap-2 text-[12px] font-medium ${tones[tone]}`}>
        <StatusDot tone={tone} />
        {children}
      </span>
    );
  };

  const Table = ({ columns, rows }) => (
    <div className="overflow-hidden rounded-md border border-[#dadce0]">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-[12px] text-[#3c4043]">
          <thead className="bg-[#f8f9fa] text-[#5f6368]">
            <tr>
              {columns.map((c) => (
                <th key={c} className="border-b border-[#e8eaed] px-4 py-2.5 font-medium whitespace-nowrap">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white">
            {rows.map((row, idx) => (
              <tr key={idx} className="border-b border-[#e8eaed] hover:bg-[#f8f9fa]">
                {row.map((cell, i) => (
                  <td key={i} className="px-4 py-3 align-top whitespace-nowrap">
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const MetricCard = ({ label, value, sub, trend }) => (
    <div className="rounded-md border border-[#dadce0] bg-white px-4 py-3">
      <div className="text-[12px] text-[#5f6368]">{label}</div>
      <div className="mt-2 text-[28px] font-normal leading-none tracking-tight text-[#202124]">{value}</div>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="text-[12px] text-[#5f6368]">{sub}</div>
        <div className={`text-[12px] font-medium ${trend === 'down' ? 'text-[#1e8e3e]' : 'text-[#b06000]'}`}>{trend === 'down' ? '↓' : '↑'}</div>
      </div>
    </div>
  );

  const LinkText = ({ children }) => (
    <a href="#" className="text-[#1a73e8] hover:underline">
      {children}
    </a>
  );

  return (
    <div className="min-h-screen bg-[#f8f9fa] font-sans text-[#202124]">
      <header className="sticky top-0 z-20 border-b border-[#dadce0] bg-white">
        <div className="flex h-14 items-center gap-3 px-4">
          <button className="grid h-9 w-9 place-items-center rounded-full text-[#5f6368] hover:bg-[#f1f3f4]">
            <div className="space-y-1">
              <div className="h-0.5 w-4 bg-current" />
              <div className="h-0.5 w-4 bg-current" />
              <div className="h-0.5 w-4 bg-current" />
            </div>
          </button>
          <div className="flex items-center gap-3">
            <div className="text-[22px] font-medium leading-none tracking-tight">
              <span className="text-[#4285F4]">G</span>
              <span className="text-[#DB4437]">o</span>
              <span className="text-[#F4B400]">o</span>
              <span className="text-[#4285F4]">g</span>
              <span className="text-[#0F9D58]">l</span>
              <span className="text-[#DB4437]">e</span>
            </div>
            <div className="text-[22px] font-normal text-[#5f6368]">Cloud</div>
          </div>

          <div className="ml-2 hidden flex-1 items-center lg:flex">
            <div className="flex h-12 w-full max-w-[760px] items-center rounded-full bg-[#f1f3f4] px-4 text-[14px] text-[#5f6368]">
              <svg viewBox="0 0 24 24" className="mr-3 h-5 w-5 fill-current">
                <path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0016 9.5 6.5 6.5 0 109.5 16a6.471 6.471 0 004.23-1.57l.27.28v.79L20 21.5 21.5 20l-6-6zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
              </svg>
              Search resources, jobs, workflows, services
            </div>
          </div>

          <div className="ml-auto flex items-center gap-1">
            {['?', '⋮'].map((item) => (
              <button key={item} className="grid h-9 w-9 place-items-center rounded-full text-[#5f6368] hover:bg-[#f1f3f4]">
                <span className="text-sm">{item}</span>
              </button>
            ))}
            <div className="ml-1 grid h-8 w-8 place-items-center rounded-full bg-[#c2e7ff] text-[12px] font-medium text-[#174ea6]">
              K
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        <aside className="hidden min-h-[calc(100vh-56px)] w-[72px] shrink-0 border-r border-[#dadce0] bg-white xl:block">
          <div className="flex flex-col items-center gap-2 py-4">
            {['⌂', '≡', '▣', '◎', '⚙'].map((icon, i) => (
              <button
                key={i}
                className={`grid h-12 w-12 place-items-center rounded-2xl text-[18px] ${i === 0 ? 'bg-[#e8f0fe] text-[#174ea6]' : 'text-[#5f6368] hover:bg-[#f1f3f4]'}`}
              >
                {icon}
              </button>
            ))}
          </div>
        </aside>

        <main className="min-w-0 flex-1">
          <div className="border-b border-[#dadce0] bg-white px-6 py-4">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div>
                <div className="mb-1 text-[12px] text-[#5f6368]">ホーム / Internal Developer Portal / ren-studio-ai</div>
                <div className="flex items-center gap-3">
                  <h1 className="text-[28px] font-normal text-[#202124]">AI Tuber Platform</h1>
                  <span className="rounded-full bg-[#e6f4ea] px-3 py-1 text-[12px] font-medium text-[#1e8e3e]">正常</span>
                </div>
                <div className="mt-1 text-[13px] text-[#5f6368]">定期実行、ワークフロー、稼働リソース、コスト、Build を確認する運用ポータル</div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button className="rounded-full border border-[#dadce0] bg-white px-4 py-2 text-[13px] text-[#1a73e8] hover:bg-[#f8fbff]">
                  フィルタを追加
                </button>
                <button className="rounded-full bg-[#1a73e8] px-4 py-2 text-[13px] font-medium text-white hover:bg-[#1765cc]">
                  GCP Console を開く
                </button>
              </div>
            </div>

            <div className="mt-4 flex gap-1 overflow-x-auto">
              {navItems.map((item, i) => (
                <button
                  key={item}
                  className={`rounded-t-lg border border-b-0 px-4 py-2 text-[13px] ${i === 0 ? 'border-[#dadce0] bg-[#f8f9fa] text-[#1a73e8]' : 'border-transparent bg-white text-[#5f6368] hover:bg-[#f8f9fa]'}`}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>

          <div className="px-6 py-6">
            <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <MetricCard label="Scheduler 健全性" value="OK" sub="直近実行は成功" trend="down" />
              <MetricCard label="Workflow 現在状態" value="正常" sub="最新 execution は成功" trend="down" />
              <MetricCard label="稼働リソース" value="5" sub="Run 2 / Job 2 / VM 1" trend="down" />
              <MetricCard label="Compute 外部 IP" value="1" sub="確認用 IP あり" trend="down" />
              <MetricCard label="概算コスト" value="$4.48" sub="先週比で減少" trend="down" />
            </section>

            <div className="grid gap-6 2xl:grid-cols-[1.15fr_0.85fr]">
              <div className="space-y-6">
                <Card title="Cloud Scheduler" action="+ 作成">
                  <div className="mb-3 flex items-center gap-2 rounded-md border border-[#dadce0] bg-[#f8f9fa] px-3 py-2 text-[12px] text-[#5f6368]">
                    <span>フィルタ</span>
                    <span className="rounded bg-white px-2 py-0.5 text-[#3c4043]">ジョブのフィルタ</span>
                  </div>
                  <Table
                    columns={['名前', '最後の実行のステータス', 'リージョン', '状態', '説明', '頻度', 'ターゲット']}
                    rows={schedulerJobs.map((w) => [
                      <div>
                        <div className="font-medium"><LinkText>{w.name}</LinkText></div>
                        <div className="mt-1 text-[11px] text-[#5f6368]">Cloud Scheduler</div>
                      </div>,
                      <StatusText tone="green">{w.lastStatus}</StatusText>,
                      w.region,
                      w.state,
                      w.description,
                      w.schedule,
                      <LinkText>{w.target}</LinkText>,
                    ])}
                  />
                </Card>

                <Card title="ワークフロー" action="Executions を開く">
                  <div className="mb-3 rounded-md border border-[#dadce0] bg-white px-4 py-3">
                    <div className="mb-3 flex items-center justify-between gap-3 text-[12px] text-[#5f6368]">
                      <div>
                        <span className="mr-2">ワークフロー:</span>
                        <LinkText>{workflows[0].name}</LinkText>
                      </div>
                      <StatusText tone="green">現在状態: 正常</StatusText>
                    </div>
                    <div className="grid gap-3 md:grid-cols-4 text-[12px] text-[#5f6368]">
                      <div>
                        <div className="mb-1">場所</div>
                        <div className="text-[13px] text-[#202124]">{workflows[0].location}</div>
                      </div>
                      <div>
                        <div className="mb-1">最新のリビジョン</div>
                        <div className="text-[13px] text-[#202124]">{workflows[0].revision}</div>
                      </div>
                      <div>
                        <div className="mb-1">直近実行</div>
                        <div className="text-[13px] text-[#202124]">{workflowExecutions[0][4]}</div>
                      </div>
                      <div>
                        <div className="mb-1">ラベル</div>
                        <div className="text-[13px] text-[#202124]">{workflows[0].labels}</div>
                      </div>
                    </div>
                  </div>
                  <div className="mb-3 flex items-center gap-2 rounded-md border border-[#dadce0] bg-[#f8f9fa] px-3 py-2 text-[12px] text-[#5f6368]">
                    <span>フィルタ</span>
                    <span className="rounded bg-white px-2 py-0.5 text-[#3c4043]">実行をフィルタ</span>
                  </div>
                  <Table
                    columns={['状態', '実行 ID', 'ワークフローのリビジョン', '作成日時', '開始時刻', '終了時間']}
                    rows={workflowExecutions.map((w) => [
                      <div className="flex items-center gap-2">
                        <StatusDot tone={w[1] === '成功' ? 'green' : 'red'} />
                        <span className="rounded-full bg-[#e8eaed] px-2.5 py-1 text-[11px] font-medium text-[#5f6368]">{w[0]}</span>
                        <span className={`text-[12px] font-medium ${w[1] === '成功' ? 'text-[#1e8e3e]' : 'text-[#d93025]'}`}>{w[1]}</span>
                      </div>,
                      <LinkText>{w[2]}</LinkText>,
                      w[3],
                      w[4],
                      w[5],
                      w[6],
                    ])}
                  />
                </Card>

                <Card>
                  <div className="space-y-4">
                    <div>
                      <div className="mb-2 text-[13px] font-medium text-[#202124]">Cloud Run</div>
                      <Table
                        columns={['状態', '名前', 'リージョン', '認証', 'Ingress', 'リンク']}
                        rows={services.map((s) => [
                          <StatusText tone="green">{s[1]}</StatusText>,
                          <LinkText>{s[0]}</LinkText>,
                          s[4],
                          s[6],
                          s[7],
                          <div className="flex gap-3 text-[11px]"><LinkText>Service</LinkText><LinkText>Logs</LinkText><LinkText>Build</LinkText></div>,
                        ])}
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-[13px] font-medium text-[#202124]">Job</div>
                      <Table
                        columns={['状態', '名前', '最終実行', 'リージョン', '起点']}
                        rows={jobs.map((j) => [
                          <StatusText tone="green">{j[1]}</StatusText>,
                          <LinkText>{j[0]}</LinkText>,
                          j[2],
                          j[3],
                          j[6],
                        ])}
                      />
                    </div>
                    <div>
                      <div className="mb-2 text-[13px] font-medium text-[#202124]">Compute</div>
                      <Table
                        columns={['状態', '名前', 'ゾーン', '内部 IP', '外部 IP', '用途']}
                        rows={computeInstances.map((vm) => [
                          <StatusText tone="green">{vm[1]}</StatusText>,
                          <LinkText>{vm[0]}</LinkText>,
                          vm[2],
                          <span className="font-medium text-[#202124]">{vm[3]}</span>,
                          <span className="font-medium text-[#202124]">{vm[4]}</span>,
                          vm[5],
                        ])}
                      />
                    </div>
                  </div>
                </Card>
              </div>

              <div className="space-y-6">
                <Card title="コスト推移">
                  <div className="mb-4 grid grid-cols-2 gap-3">
                    <div className="rounded-md border border-[#dadce0] bg-white px-3 py-3">
                      <div className="text-[11px] text-[#5f6368]">2026/03/01〜2026/03/06</div>
                      <div className="mt-1 text-[28px] font-normal leading-none">$4.48</div>
                      <div className="mt-2 text-[12px] text-[#1e8e3e]">↓ 41.13%</div>
                    </div>
                    <div className="rounded-md border border-[#dadce0] bg-white px-3 py-3">
                      <div className="text-[11px] text-[#5f6368]">2026/03/01〜2026/03/31 (forecasted)</div>
                      <div className="mt-1 text-[28px] font-normal leading-none">$12.54</div>
                      <div className="mt-2 text-[12px] text-[#1e8e3e]">↓ 63.32%</div>
                    </div>
                  </div>

                  <div className="rounded-md border border-[#dadce0] bg-white p-4">
                    <div className="mb-3 flex items-center justify-between text-[12px] text-[#5f6368]">
                      <span>累積表示</span>
                      <div className="flex items-center gap-3">
                        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#5f6368]" />累積表示</span>
                        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-[#1a73e8]" />日次</span>
                      </div>
                    </div>
                    <div className="flex h-72 items-end gap-2">
                      {[0.2, 0.2, 0.2, 2.2, 0.6, 0.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0].map((h, i) => (
                        <div key={i} className="flex flex-1 flex-col items-center gap-2">
                          <div className="relative w-full rounded-sm bg-[#1a73e8]" style={{ height: `${Math.max(h * 34, 8)}px` }}>
                            {i < 6 ? <div className="absolute bottom-0 left-0 right-0 h-2 bg-[#f29900]" /> : <div className="absolute inset-0 rounded-sm bg-[#e8eaed]" />}
                          </div>
                          <div className="text-[10px] text-[#5f6368]">3/{String(i + 1).padStart(2, '0')}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>

                <Card title="Cloud Build" action="Build History を開く">
                  <div className="mb-3 flex items-center gap-2 rounded-md border border-[#dadce0] bg-[#f8f9fa] px-3 py-2 text-[12px] text-[#5f6368]">
                    <span>フィルタ</span>
                    <span className="rounded bg-white px-2 py-0.5 text-[#3c4043]">プロパティ名または値を入力</span>
                  </div>
                  <Table
                    columns={['ステータス', 'ビルド', 'リージョン', 'ソース', 'Ref', 'commit', 'トリガー名']}
                    rows={builds.map((b) => [
                      <StatusText tone="green">成功</StatusText>,
                      <LinkText>{b[0]}</LinkText>,
                      b[1],
                      <LinkText>{b[2]}</LinkText>,
                      b[3],
                      <LinkText>{b[4]}</LinkText>,
                      <LinkText>{b[5]}</LinkText>,
                    ])}
                  />
                </Card>

                <Card title="クイックリンク" action="編集">
                  <div className="grid gap-3 sm:grid-cols-2">
                    {[
                      ['Cloud Run Services', '本番サービス一覧を開く'],
                      ['Cloud Run Jobs', 'Job 実行履歴を開く'],
                      ['Cloud Workflows', 'Executions 画面へ'],
                      ['Cloud Build', 'Build History へ'],
                      ['Logs Explorer', '障害調査の入口'],
                      ['Monitoring', 'アラートと指標'],
                    ].map(([title, desc]) => (
                      <a
                        href="#"
                        key={title}
                        className="rounded-md border border-[#dadce0] bg-white px-4 py-4 transition hover:border-[#aecbfa] hover:bg-[#f8fbff]"
                      >
                        <div className="text-[14px] font-medium text-[#202124]">{title}</div>
                        <div className="mt-1 text-[12px] text-[#5f6368]">{desc}</div>
                      </a>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
