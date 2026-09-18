// 文件说明：教师工作台 React 壳层。旧页面功能通过 DOM bridge 保持兼容，页面逐步迁移到 feature components。
import { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type WorkbenchView = "home" | "review" | "preview" | "performance" | "paper" | "recommend" | "upload";
type PreviewQuestion = {
  question_id?: string;
  display_id?: string;
  source_exam?: string;
  question_number?: number;
  question_type?: string;
  primary_knowledge?: string;
  needs_teacher_review?: boolean;
  stem_html?: string;
  stem_markdown?: string;
  solution_html?: string;
  solution_markdown?: string;
  answer?: string;
};
type UploadJob = {
  status?: "queued" | "running" | "ready" | "failed";
  stage?: "queued" | "ocr" | "structure" | "tag" | "ready" | "failed";
  message?: string;
  job_id?: string;
  file_names?: string[];
  ocr_engine?: string;
  structured_dir?: string;
  workbench_url?: string;
  summary?: {
    question_count?: number;
    review_count?: number;
    preview?: Array<{
      display_id?: string;
      question_number?: number;
      question_type?: string;
      primary_knowledge?: string;
      stem_markdown?: string;
      answer?: string;
      solution_markdown?: string;
    }>;
  };
};

const views: Array<{ id: WorkbenchView; label: string; icon: string; legacyId: string }> = [
  { id: "review", label: "标签审核", icon: "审", legacyId: "nav-review" },
  { id: "preview", label: "题目预览", icon: "览", legacyId: "" },
  { id: "performance", label: "学情概览", icon: "学", legacyId: "nav-performance" },
  { id: "paper", label: "原题错题集", icon: "题", legacyId: "nav-paper" },
  { id: "recommend", label: "个性新题", icon: "生", legacyId: "nav-recommend" },
];

function clickLegacy(id: string) {
  if (!id) return;
  document.getElementById(id)?.click();
}

function previewQuestionFromHash() {
  const match = window.location.hash.match(/^#preview\/(.+)$/);
  if (!match) return "";
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

function readText(id: string, fallback: string) {
  return document.getElementById(id)?.textContent?.trim() || fallback;
}

function readValue(id: string, fallback: string) {
  const element = document.getElementById(id) as HTMLInputElement | null;
  return element?.value || fallback;
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "上传流程发生未知错误";
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function uploadStageIndex(job: UploadJob | null) {
  if (!job) return 0;
  if (job.status === "ready" || job.stage === "ready") return 4;
  if (job.stage === "structure") return 2;
  if (job.stage === "tag") return 3;
  return 1;
}

function looksLikeAnswer(file: File) {
  return /(答案|参考答案|解析|answer|solution)/i.test(file.name);
}

function fileStem(file: File) {
  return file.name.replace(/\.[^.]+$/, "").trim().toLocaleLowerCase();
}

function Sidebar({ view, onViewChange }: { view: WorkbenchView; onViewChange: (view: WorkbenchView) => void }) {
  return (
    <aside className="shell-sidebar">
      <div className="shell-brand">
        <div className="shell-brand-mark">题</div>
        <div>
          <strong>教师题库工作台</strong>
          <span>审核 · 学情 · 生题</span>
        </div>
      </div>

      <nav className="shell-nav" aria-label="教师工作台主导航">
        <span className="shell-nav-label">工作台</span>
        {views.map((item) => (
          <button
            key={item.id}
            type="button"
            className={view === item.id ? "active" : ""}
            onClick={() => {
              onViewChange(item.id);
              clickLegacy(item.legacyId);
            }}
          >
            <i aria-hidden="true">{item.icon}</i>
            <span>{item.label}</span>
            {item.id === "review" && <b>{readText("metric-total", "0")}</b>}
          </button>
        ))}
        <span className="shell-nav-label shell-nav-label--second">题库管理</span>
        <button type="button" className={view === "home" ? "active" : ""} onClick={() => onViewChange("home")}>
          <i aria-hidden="true">库</i><span>题库首页</span>
        </button>
        <button type="button" className={view === "upload" ? "active" : ""} onClick={() => onViewChange("upload")}>
          <i aria-hidden="true">扫</i><span>上传试卷</span>
        </button>
      </nav>

      <div className="shell-sidebar-footer">
        <div className="shell-avatar">教</div>
        <div><strong>教师账户</strong><span>本机题库服务</span></div>
        <span className="shell-online-dot" title="本地服务在线" />
      </div>
    </aside>
  );
}

function ToolsMenu({ open, onClose, onUpload }: { open: boolean; onClose: () => void; onUpload: () => void }) {
  const [reviewer, setReviewer] = useState(() => readValue("reviewer", ""));
  const [status, setStatus] = useState(() => readText("ocr-import-status", "OCR Skill 就绪状态待检查"));

  useEffect(() => {
    const target = document.getElementById("ocr-import-status");
    if (!target) return;
    const observer = new MutationObserver(() => setStatus(target.textContent?.trim() || ""));
    observer.observe(target, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, []);

  if (!open) return null;

  const proxy = (id: string) => {
    onClose();
    clickLegacy(id);
  };

  return (
    <div className="shell-tools-menu" role="menu">
      <label className="shell-reviewer">
        <span>审核人</span>
        <input
          value={reviewer}
          onChange={(event) => {
            setReviewer(event.target.value);
            const input = document.getElementById("reviewer") as HTMLInputElement | null;
            if (input) input.value = event.target.value;
          }}
          placeholder="姓名 / 工号"
        />
      </label>
      <button type="button" className="shell-tool-primary" onClick={() => { onClose(); onUpload(); }}>上传试卷并建立题库</button>
      <span className="shell-tool-status">{status}</span>
      <button type="button" onClick={() => proxy("apply-btn")}>应用审核结果</button>
      <button type="button" onClick={() => proxy("backup-btn")}>下载审核备份</button>
      <button type="button" onClick={() => proxy("import-btn")}>恢复审核备份</button>
      <button type="button" onClick={() => proxy("generation-import-btn")}>导入已生成新题</button>
    </div>
  );
}

function Topbar({ view, bankName, onUpload }: { view: WorkbenchView; bankName: string; onUpload: () => void }) {
  const [toolsOpen, setToolsOpen] = useState(false);
  const label = view === "home" ? "题库总览" : view === "upload" ? "导入试卷" : views.find((item) => item.id === view)?.label || "标签审核";
  return (
    <header className="shell-topbar">
      <div className="shell-breadcrumb"><span>题库运营</span><b>/</b><strong>{label}</strong><small>{bankName}</small></div>
      <div className="shell-topbar-actions">
        <span className="shell-service-status"><i />本地工作台在线</span>
        <button type="button" className="shell-help" onClick={() => setToolsOpen((current) => !current)}>使用帮助</button>
        <button type="button" className="shell-primary" onClick={onUpload}>＋ 上传试卷</button>
        <div className="shell-tools-wrap">
          <button type="button" className={`shell-tools-button ${toolsOpen ? "active" : ""}`} onClick={() => setToolsOpen((current) => !current)}>工具⌄</button>
          <ToolsMenu open={toolsOpen} onClose={() => setToolsOpen(false)} onUpload={onUpload} />
        </div>
      </div>
    </header>
  );
}

function metricValue(id: string) {
  const value = readText(id, "—");
  return /^\d+$/.test(value) ? Number(value) : value;
}

function BankOverviewWorkspace({ bankName, onUpload, onNavigate }: { bankName: string; onUpload: () => void; onNavigate: (view: WorkbenchView) => void }) {
  const safe = metricValue("metric-safe");
  const excluded = metricValue("metric-excluded");
  const total = typeof safe === "number" && typeof excluded === "number" ? safe + excluded : "—";
  const excludedReasons = readText("metric-excluded-reasons", "暂无排除题");
  return (
    <section className="shell-bank-page" aria-label="题库总览">
      <div className="shell-bank-heading">
        <div><span className="shell-kicker">QUESTION BANK</span><h1>{bankName}</h1><p>这是当前题库的工作入口。你可以从这里查看质量概况，进入审核、学情、组卷，或导入一份新试卷。</p></div>
        <button type="button" className="shell-upload-button" onClick={onUpload}>＋ 导入新试卷</button>
      </div>
      <div className="shell-bank-stats">
        <div className="shell-bank-stat shell-bank-stat--blue"><span>题库总量</span><strong>{total}</strong><small>安全题 + 已排除题</small></div>
        <div className="shell-bank-stat shell-bank-stat--gold"><span>待审核</span><strong>{metricValue("metric-total")}</strong><small>需要教师确认的题目</small></div>
        <div className="shell-bank-stat shell-bank-stat--green"><span>安全可用</span><strong>{safe}</strong><small>可进入推荐与组卷</small></div>
        <div className="shell-bank-stat shell-bank-stat--red"><span>已排除</span><strong>{excluded}</strong><small>存在质量或标签问题</small></div>
      </div>
      <div className="shell-bank-columns">
        <div className="shell-upload-card shell-bank-actions-card"><div className="shell-card-heading"><div><span className="shell-card-index">01</span><strong>进入工作区</strong></div><span>保持在当前页面</span></div><div className="shell-bank-action-grid"><button type="button" onClick={() => onNavigate("review")}><b>审</b><span><strong>标签审核</strong><small>处理待审核题目</small></span><i>→</i></button><button type="button" onClick={() => onNavigate("performance")}><b>学</b><span><strong>学情概览</strong><small>查看班级错题数据</small></span><i>→</i></button><button type="button" onClick={() => onNavigate("paper")}><b>卷</b><span><strong>原题错题集</strong><small>整理班级练习卷</small></span><i>→</i></button><button type="button" onClick={() => onNavigate("recommend")}><b>生</b><span><strong>个性新题</strong><small>进入个性化生成</small></span><i>→</i></button></div></div>
        <div className="shell-upload-card shell-bank-health-card"><div className="shell-card-heading"><div><span className="shell-card-index">02</span><strong>题库健康提示</strong></div><span>{excludedReasons === "暂无排除题" ? "状态良好" : "需要关注"}</span></div><div className="shell-bank-health-line"><span className="shell-health-dot" /><div><strong>{excludedReasons === "暂无排除题" ? "当前没有排除题" : "部分题目暂不可用"}</strong><p>{excludedReasons}</p></div></div><div className="shell-bank-tip">建议先完成高优先级审核，再使用安全题进入组卷和推荐。</div></div>
      </div>
      <div className="shell-upload-footnote">当前页面不会离开工作台 · 本地服务在线 · 题库数据来自：{bankName}</div>
    </section>
  );
}

function readWorkbenchQuestions(): PreviewQuestion[] {
  const dataNode = document.getElementById("workbench-data");
  if (!dataNode?.textContent) return [];
  try {
    const data = JSON.parse(dataNode.textContent) as { all_questions?: PreviewQuestion[]; items?: PreviewQuestion[] };
    const rows = Array.isArray(data.all_questions) && data.all_questions.length ? data.all_questions : data.items || [];
    return rows.map((row) => ({ ...row, primary_knowledge: row.primary_knowledge || (row as PreviewQuestion & { tags?: { primary_knowledge?: string } }).tags?.primary_knowledge || "" }));
  } catch {
    return [];
  }
}

function questionTypeLabel(value?: string) {
  return ({ single_choice: "单项选择", multiple_choice: "多项选择", fill_blank: "填空题", solution: "解答题" } as Record<string, string>)[value || ""] || value || "未分类";
}

function PreviewWorkspace({ bankName, selectedQuestionId }: { bankName: string; selectedQuestionId: string }) {
  const questions = useMemo(readWorkbenchQuestions, []);
  const [search, setSearch] = useState("");
  const [questionType, setQuestionType] = useState("");
  const [knowledge, setKnowledge] = useState("");
  const [sourceExam, setSourceExam] = useState("");
  const visibleQuestions = useMemo(() => {
    const needle = search.trim().toLocaleLowerCase();
    return questions.filter((question) => {
      const haystack = [question.display_id, question.source_exam, question.question_number, question.primary_knowledge, question.stem_markdown].join(" ").toLocaleLowerCase();
      return (!needle || haystack.includes(needle)) && (!questionType || question.question_type === questionType) && (!knowledge || question.primary_knowledge === knowledge) && (!sourceExam || question.source_exam === sourceExam);
    });
  }, [knowledge, questionType, questions, search, sourceExam]);
  const knowledgeOptions = useMemo(() => [...new Set(questions.map((question) => question.primary_knowledge).filter(Boolean))].sort(), [questions]);
  const examOptions = useMemo(() => [...new Set(questions.map((question) => question.source_exam).filter(Boolean))].sort(), [questions]);
  const questionGroups = useMemo(() => {
    const groups = new Map<string, PreviewQuestion[]>();
    for (const question of visibleQuestions) {
      const exam = question.source_exam || "未标注试卷";
      groups.set(exam, [...(groups.get(exam) || []), question]);
    }
    return [...groups.entries()];
  }, [visibleQuestions]);

  useEffect(() => {
    if (!selectedQuestionId) return;
    const target = document.getElementById(`preview-question-${selectedQuestionId}`);
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [selectedQuestionId, visibleQuestions.length]);

  useEffect(() => {
    const mathJax = (window as Window & { MathJax?: { typesetPromise?: (elements: Element[]) => Promise<unknown> } }).MathJax;
    const container = document.querySelector(".shell-preview-question-list");
    if (mathJax?.typesetPromise && container) void mathJax.typesetPromise([container]);
  }, [visibleQuestions]);

  return (
    <section className="shell-preview-page" aria-label="题目预览">
      <div className="shell-preview-page-heading">
        <div><span className="shell-kicker">QUESTION LIBRARY</span><h1>题目预览</h1><p>在当前工作台统一查看题库全部题目，不再打开独立的原题 HTML 页面。</p></div>
        <div className="shell-preview-page-count"><strong>{questions.length}</strong><span>道题目</span></div>
      </div>
      <div className="shell-preview-toolbar">
        <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索题号、试卷、知识点或题面" aria-label="搜索题目" />
        <select value={sourceExam} onChange={(event) => setSourceExam(event.target.value)} aria-label="按试卷筛选"><option value="">全部试卷</option>{examOptions.map((value) => <option value={value} key={value}>{value}</option>)}</select>
        <select value={questionType} onChange={(event) => setQuestionType(event.target.value)} aria-label="按题型筛选"><option value="">全部题型</option>{[...new Set(questions.map((question) => question.question_type).filter(Boolean))].map((value) => <option value={value} key={value}>{questionTypeLabel(value)}</option>)}</select>
        <select value={knowledge} onChange={(event) => setKnowledge(event.target.value)} aria-label="按知识点筛选"><option value="">全部知识点</option>{knowledgeOptions.map((value) => <option value={value} key={value}>{value}</option>)}</select>
        <span>显示 {visibleQuestions.length} / {questions.length} 题</span>
      </div>
      <div className="shell-preview-question-list">
        {questionGroups.length ? questionGroups.map(([exam, group]) => (
          <section className="shell-preview-exam-group" key={exam}>
            <header className="shell-preview-exam-heading"><div><span>试卷</span><h2>{exam}</h2></div><strong>{group.length} 题</strong></header>
            <div className="shell-preview-exam-questions">
              {group.map((question, index) => (
                <article className={`shell-preview-question ${selectedQuestionId === question.question_id ? "selected" : ""}`} id={`preview-question-${question.question_id || index}`} key={question.question_id || `${question.display_id}-${index}`}>
                  <header className="shell-preview-question-heading"><div><strong>第 {question.question_number || index + 1} 题</strong><span>{questionTypeLabel(question.question_type)}</span>{question.needs_teacher_review && <small>待审核</small>}</div><small>{question.display_id || ""}</small></header>
                  <div className="shell-preview-question-source">{question.primary_knowledge || "未标注知识点"}</div>
                  {question.stem_html ? <div className="shell-preview-question-stem" dangerouslySetInnerHTML={{ __html: question.stem_html }} /> : <div className="shell-preview-question-stem shell-preview-question-stem--plain">{question.stem_markdown || "暂无题面"}</div>}
                  {(question.answer || question.solution_html || question.solution_markdown) && <details className="shell-preview-answer"><summary>查看答案与解析</summary><div><p><b>答案：</b>{question.answer || "暂无"}</p>{question.solution_html ? <div><b>解析：</b><span dangerouslySetInnerHTML={{ __html: question.solution_html }} /></div> : question.solution_markdown ? <p><b>解析：</b>{question.solution_markdown}</p> : null}</div></details>}
                </article>
              ))}
            </div>
          </section>
        )) : <div className="shell-preview-empty">没有符合条件的题目。</div>}
      </div>
      <div className="shell-upload-footnote">当前题库：{bankName} · 题目预览已在工作台内完成，不会跳转到独立页面</div>
    </section>
  );
}

function UploadWorkspace({ bankName, onBack }: { bankName: string; onBack: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [job, setJob] = useState<UploadJob | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [previewOpen, setPreviewOpen] = useState(false);

  const chooseFiles = (incoming: FileList | File[]) => {
    const accepted = Array.from(incoming).filter((file) => /\.(pdf|docx?)$/i.test(file.name));
    const ordered = accepted.sort((left, right) => Number(looksLikeAnswer(left)) - Number(looksLikeAnswer(right)));
    const unique: File[] = [];
    const positions = new Map<string, number>();
    for (const file of ordered) {
      const key = fileStem(file);
      const position = positions.get(key);
      if (position === undefined) {
        positions.set(key, unique.length);
        unique.push(file);
      } else if (file.name.toLowerCase().endsWith(".pdf") && !unique[position].name.toLowerCase().endsWith(".pdf")) {
        unique[position] = file;
      }
    }
    setFiles(unique.slice(0, 8));
    setJob(null);
    const notices = [];
    if (accepted.length !== Array.from(incoming).length) notices.push("已忽略不支持的文件，只接受 PDF、DOCX 或 DOC。");
    if (unique.length !== accepted.length) notices.push("检测到同名 DOCX/PDF，已优先保留 PDF，避免重复提交。");
    if (unique.length > 0 && unique.every(looksLikeAnswer)) notices.push("当前文件名看起来都是答案/解析，请同时选择一份试卷正文。");
    setError(notices.join(" "));
  };

  const readJson = async (response: Response): Promise<UploadJob & { error?: string }> => {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "试卷上传失败");
    return payload;
  };

  const startImport = async () => {
    if (!files.length) {
      setError("请先选择试卷文件，答案文件可以一起上传。 ");
      return;
    }
    if (files.every(looksLikeAnswer)) {
      setError("不能只上传答案/解析文件，请同时选择试卷正文。 ");
      return;
    }
    setBusy(true);
    setError("");
    setJob({ status: "queued", stage: "queued", file_names: files.map((file) => file.name), message: "正在提交试卷…" });
    try {
      const form = new FormData();
      files.forEach((file) => form.append("files", file, file.name));
      let next = await readJson(await fetch("/api/ocr/import", { method: "POST", body: form }));
      setJob(next);
      while (next.status === "queued" || next.status === "running") {
        await new Promise((resolve) => window.setTimeout(resolve, 1200));
        next = await readJson(await fetch(`/api/ocr/jobs/${encodeURIComponent(next.job_id || "")}`));
        setJob(next);
      }
      if (next.status !== "ready") throw new Error(next.message || "OCR 导入失败");
    } catch (caught) {
      const message = errorMessage(caught);
      setError(message);
      setJob((current) => ({ ...(current || {}), status: "failed", stage: current?.stage || "failed", message }));
    } finally {
      setBusy(false);
    }
  };

  const reset = () => {
    if (busy) return;
    setFiles([]);
    setJob(null);
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  };

  const currentStage = uploadStageIndex(job);
  const previewQuestions = job?.summary?.preview || [];
  const steps = [
    ["upload", "上传文件", "校验试卷与答案"],
    ["ocr", "MinerU OCR", "识别版面、文字与公式"],
    ["structure", "题目结构化", "拆分题目、答案和图片"],
    ["tag", "标注并建库", "生成审核工作台"],
  ];

  return (
    <section className="shell-upload-page" aria-label="上传试卷并建立题库">
      <div className="shell-upload-heading">
        <div>
          <span className="shell-kicker">NEW QUESTION BANK</span>
          <h1>从一份试卷开始</h1>
          <p>上传试卷和答案，系统会自动完成 OCR、题目拆分、知识点标注，并生成一个可审核的新题库。</p>
        </div>
        <button type="button" className="shell-upload-back" onClick={onBack}>返回当前题库</button>
      </div>

      <div className="shell-upload-grid">
        <div className="shell-upload-card shell-upload-drop-card">
          <div className="shell-card-heading"><div><span className="shell-card-index">01</span><strong>选择试卷文件</strong></div><span>最多 8 个文件</span></div>
          <div
            className={`shell-dropzone ${dragging ? "dragging" : ""}`}
            role="button"
            tabIndex={0}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inputRef.current?.click(); }}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFiles(event.dataTransfer.files); }}
          >
            <input ref={inputRef} type="file" accept=".pdf,.docx,.doc" multiple hidden onChange={(event) => event.target.files && chooseFiles(event.target.files)} />
            <span className="shell-upload-symbol">↑</span>
            <strong>拖放试卷到这里</strong>
            <span>或点击选择 PDF / DOCX / DOC</span>
            <small>建议同时上传试卷与答案，系统会自动配对处理</small>
          </div>

          {files.length > 0 && (
            <div className="shell-file-list">
              {files.map((file) => <div className="shell-file-row" key={`${file.name}-${file.size}`}><span className="shell-file-type">{file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "DOC"}</span><div><strong>{file.name}</strong><small>{formatFileSize(file.size)}</small></div><span className="shell-file-ok">已选</span></div>)}
            </div>
          )}

          {error && <div className="shell-upload-error">{error}</div>}
          <div className="shell-upload-actions"><button type="button" className="shell-upload-button" disabled={busy || !files.length} onClick={startImport}>{busy ? "处理中…" : "开始导入并建立题库"}</button><button type="button" className="shell-upload-reset" disabled={busy} onClick={reset}>重新选择</button></div>
        </div>

        <aside className="shell-upload-side">
          <div className="shell-upload-card shell-process-card">
            <div className="shell-card-heading"><div><span className="shell-card-index">02</span><strong>处理进度</strong></div><span>{job?.status === "ready" ? "已完成" : busy ? "进行中" : "等待开始"}</span></div>
            <div className="shell-progress-list">
              {steps.map(([id, label, detail], index) => {
                const state = job?.status === "failed" && index === Math.min(currentStage, 3) ? "error" : index < currentStage ? "done" : index === currentStage && busy ? "active" : "pending";
                return <div className={`shell-progress-step ${state}`} key={id}><span className="shell-step-marker">{state === "done" ? "✓" : state === "error" ? "!" : String(index + 1).padStart(2, "0")}</span><div><strong>{label}</strong><small>{detail}</small></div></div>;
              })}
            </div>
            <p className="shell-process-message">{job?.message || "选择文件后，这里会显示每个处理阶段的实时状态。"}</p>
          </div>
          <div className="shell-upload-card shell-engine-card"><span className="shell-card-index">03</span><strong>当前处理引擎</strong><p>Cherry Studio exam-ocr Skill / MinerU</p><small>题库会在本机服务中生成，原始文件不会写入前端页面。</small></div>
        </aside>
      </div>

      {job?.status === "ready" && (
        <div className="shell-upload-card shell-upload-result">
          <div><span className="shell-kicker">READY</span><h2>新题库已经生成</h2><p>{job.structured_dir ? `题库目录：${job.structured_dir.split(/[\\/]/).pop()}` : "OCR、结构化、标注和工作台均已完成。"}</p></div>
          <div className="shell-result-stats"><div><strong>{job.summary?.question_count ?? "—"}</strong><span>题目入库</span></div><div><strong>{job.summary?.review_count ?? "—"}</strong><span>待审核</span></div><div><strong>{job.file_names?.length ?? files.length}</strong><span>输入文件</span></div></div>
          <div className="shell-result-actions"><button type="button" className="shell-preview-button" disabled={!job.workbench_url} onClick={() => setPreviewOpen((current) => !current)}>{previewOpen ? "收起预览" : "预览新题库"}</button><button type="button" className="shell-upload-button" onClick={() => { if (job.workbench_url) window.location.href = job.workbench_url; }}>进入新题库工作台</button></div>
        </div>
      )}

      {job?.status === "ready" && (
        <section className="shell-upload-card shell-question-preview" aria-label="题目预览">
          <div className="shell-preview-heading">
            <div><span className="shell-kicker">QUESTION PREVIEW</span><h2>题目预览</h2><p>{previewQuestions.length ? `先展示新题库前 ${previewQuestions.length} 题，确认题面后再进入完整审核。` : "题库已经生成，但本次没有返回题目摘要。"}</p></div>
            {job.workbench_url && <button type="button" className="shell-preview-close" onClick={() => setPreviewOpen(true)}>打开完整渲染预览</button>}
          </div>
          {previewQuestions.length ? (
            <div className="shell-question-preview-list">
              {previewQuestions.map((question, index) => (
                <article className="shell-question-preview-item" key={question.display_id || `${question.question_number || index}-${index}`}>
                  <div className="shell-question-preview-meta"><strong>第 {question.question_number || index + 1} 题</strong><span>{question.question_type || "未分类"}</span>{question.primary_knowledge && <small>{question.primary_knowledge}</small>}</div>
                  <div className="shell-question-stem">{question.stem_markdown || "暂无题面摘要"}</div>
                  {(question.answer || question.solution_markdown) ? <details><summary>查看答案与解析</summary><div className="shell-question-answer">{question.answer && <p><b>答案：</b>{question.answer}</p>}{question.solution_markdown && <p><b>解析：</b>{question.solution_markdown}</p>}</div></details> : <div className="shell-question-pending">答案待审核</div>}
                </article>
              ))}
            </div>
          ) : (
            <div className="shell-question-preview-empty">可点击上方“打开完整渲染预览”，在当前导入页面查看新题库工作台。</div>
          )}
        </section>
      )}

      {previewOpen && job?.workbench_url && (
        <div className="shell-upload-card shell-bank-preview">
          <div className="shell-preview-heading"><div><span className="shell-kicker">FULL WORKBENCH</span><h2>完整渲染预览</h2><p>预览窗口保留在当前导入页，不会丢失本次导入结果。</p></div><button type="button" className="shell-preview-close" onClick={() => setPreviewOpen(false)}>关闭预览</button></div>
          <iframe title="新题库工作台预览" src={job.workbench_url} loading="lazy" />
        </div>
      )}

      <div className="shell-upload-footnote">当前题库：{bankName} · 可随时返回，不影响已有审核记录</div>
    </section>
  );
}

function Shell() {
  const root = document.getElementById("react-shell");
  const bankName = root?.dataset.bankName || readText("bank-name", "当前题库");
  const [view, setView] = useState<WorkbenchView>(() => previewQuestionFromHash() ? "preview" : "review");
  const [previewQuestionId, setPreviewQuestionId] = useState(previewQuestionFromHash);

  useEffect(() => {
    const handler = (event: Event) => {
      const next = (event as CustomEvent<WorkbenchView>).detail;
      if (views.some((item) => item.id === next)) setView(next);
    };
    window.addEventListener("workbench:view-change", handler);
    return () => window.removeEventListener("workbench:view-change", handler);
  }, []);

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      const link = target?.closest("a[href*='/questions/'][href*='/preview.html']") as HTMLAnchorElement | null;
      if (!link) return;
      const match = link.href.match(/\/questions\/([^/]+)\/preview\.html(?:$|[?#])/);
      if (!match) return;
      event.preventDefault();
      setPreviewQuestionId(decodeURIComponent(match[1]));
      setView("preview");
    };
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, []);

  const metrics = useMemo(() => ({
    pending: readText("metric-total", "0"),
    safe: readText("metric-safe", "—"),
    excluded: readText("metric-excluded", "—"),
  }), [view]);

  return (
    <div className="shell-root">
      <Sidebar view={view} onViewChange={setView} />
      <div className="shell-main">
        <Topbar view={view} bankName={bankName} onUpload={() => setView("upload")} />
        <div className="shell-context-strip" aria-label="当前题库状态">
          <span><b>{metrics.pending}</b> 待审核</span>
          <span><b>{metrics.safe}</b> 安全可用题</span>
          <span><b>{metrics.excluded}</b> 已排除题</span>
          <span className="shell-context-hint">左侧导航切换工作区，具体操作保留在各功能页面</span>
        </div>
      </div>
      {view === "home" && <BankOverviewWorkspace bankName={bankName} onUpload={() => setView("upload")} onNavigate={(next) => { setView(next); if (next !== "upload") clickLegacy(`nav-${next}`); }} />}
      {view === "preview" && <PreviewWorkspace bankName={bankName} selectedQuestionId={previewQuestionId} />}
      {view === "upload" && <UploadWorkspace bankName={bankName} onBack={() => { setView("review"); clickLegacy("nav-review"); }} />}
    </div>
  );
}

const mount = document.getElementById("react-shell");
if (mount) createRoot(mount).render(<Shell />);
