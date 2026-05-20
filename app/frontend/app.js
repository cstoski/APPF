// ===== Helpers =====
const $ = (id) => document.getElementById(id);

function setBadge(el, text, kind = "") {
  el.textContent = text;
  el.className = "badge" + (kind ? ` ${kind}` : "");
}

function setMsg(el, text, kind = "") {
  el.textContent = text || "";
  el.className = "msg" + (kind ? ` ${kind}` : "");
}

function baseUrl() {
  return $("baseUrl").value.trim().replace(/\/+$/, "");
}

function token() {
  return sessionStorage.getItem("appf_token") || "";
}

function setToken(t) {
  if (t) sessionStorage.setItem("appf_token", t);
  else sessionStorage.removeItem("appf_token");
}

function authHeaders() {
  const t = token();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function apiFetch(path, options = {}) {
  const url = `${baseUrl()}${path}`;
  const headers = {
    ...(options.headers || {}),
    ...authHeaders(),
  };
  const resp = await fetch(url, { ...options, headers });
  const text = await resp.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!resp.ok) {
    const detail = (data && data.detail) ? data.detail : text || resp.statusText;
    throw new Error(`${resp.status} • ${detail}`);
  }
  return data;
}

function fileSelected() {
  return $("fileInput").files && $("fileInput").files[0];
}

function buildDecisoesFromTable() {
  const rows = document.querySelectorAll("#previewTbody tr[data-linha]");
  const decisoes = [];
  rows.forEach((tr) => {
    const linha = parseInt(tr.getAttribute("data-linha"), 10);
    const sel = tr.querySelector("select[data-acao]");
    if (!sel) return;
    const acao = sel.value;
    // só envia se usuário alterou ou se for diferente do default? -> envia tudo para ser determinístico
    decisoes.push({ linha, acao });
  });
  return decisoes;
}

// ===== State =====
let previewItems = []; // itens retornados do backend

function refreshButtons() {
  const authed = !!token();
  const hasFile = !!fileSelected();

  $("btnLogout").disabled = !authed;
  $("btnPreview").disabled = !(authed && hasFile);
  $("btnAplicar").disabled = !(authed && hasFile && previewItems.length > 0);

  $("btnMarcarNovos").disabled = previewItems.length === 0;
  $("btnMarcarDup").disabled = previewItems.length === 0;
  $("btnLimparAcoes").disabled = previewItems.length === 0;
}

function applyFilter() {
  const term = $("filterText").value.trim().toLowerCase();
  const tbody = $("previewTbody");
  const trs = tbody.querySelectorAll("tr[data-linha]");
  trs.forEach((tr) => {
    const hay = tr.getAttribute("data-hay") || "";
    tr.style.display = hay.includes(term) ? "" : "none";
  });
}

// ===== Render =====
function renderSummary(sum) {
  $("kpiTotal").textContent = String(sum.total_linhas ?? 0);
  $("kpiNovos").textContent = String(sum.novos ?? 0);
  $("kpiDuplicados").textContent = String(sum.duplicados ?? 0);
  $("kpiInvalidos").textContent = String(sum.invalidos ?? 0);
  $("kpiSemLgpd").textContent = String(sum.sem_consentimento ?? 0);
}

function statusBadge(status) {
  switch (status) {
    case "NOVO": return `<span class="badge ok">NOVO</span>`;
    case "DUP_CPF": return `<span class="badge warn">DUP_CPF</span>`;
    case "DUP_NOME": return `<span class="badge warn">DUP_NOME</span>`;
    case "SEM_CONSENTIMENTO": return `<span class="badge bad">SEM LGPD</span>`;
    case "INVALIDO": return `<span class="badge bad">INVÁLIDO</span>`;
    default: return `<span class="badge">${status}</span>`;
  }
}

function renderTable(items) {
  const tbody = $("previewTbody");

  if (!items || items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty">Nenhum item no preview.</td></tr>`;
    return;
  }

  tbody.innerHTML = items.map((it) => {
    const linha = it.linha;
    const nome = it.nome_completo || "";
    const cpf = it.cpf || "";
    const status = it.status || "";
    const sugestao = it.sugestao_acao || "PULAR";

    const encontrado = it.existente_id
      ? `#${it.existente_id} • ${it.existente_nome || ""} • ${it.existente_cpf || ""}`
      : "—";

    // trava ações em inválidos e sem consentimento
    const locked = (status === "INVALIDO" || status === "SEM_CONSENTIMENTO");

    const options = ["IMPORTAR", "ATUALIZAR", "PULAR"].map((a) => {
      const sel = (a === sugestao) ? "selected" : "";
      // em NOVO, esconder ATUALIZAR por UX? deixo disponível (pode existir caso peculiar)
      return `<option value="${a}" ${sel}>${a}</option>`;
    }).join("");

    const hay = `${linha} ${nome} ${cpf} ${status} ${encontrado}`.toLowerCase();

    return `
      <tr data-linha="${linha}" data-hay="${hay}">
        <td>${linha}</td>
        <td>${nome}</td>
        <td>${cpf}</td>
        <td>${statusBadge(status)}</td>
        <td>
          <select data-acao ${locked ? "disabled" : ""}>
            ${options}
          </select>
        </td>
        <td>${encontrado}</td>
      </tr>
    `;
  }).join("");

  // eventos
  tbody.querySelectorAll("select[data-acao]").forEach((sel) => {
    sel.addEventListener("change", () => {
      setMsg($("importMsg"), "Ações alteradas (pronto para aplicar).", "ok");
      refreshButtons();
    });
  });

  applyFilter();
}

// ===== Actions =====
async function ping() {
  try {
    setBadge($("pingStatus"), "verificando…");
    await fetch(`${baseUrl()}/docs`, { method: "GET" });
    setBadge($("pingStatus"), "OK", "ok");
  } catch {
    setBadge($("pingStatus"), "Falhou", "bad");
  }
}

async function login() {
  const u = $("username").value.trim();
  const p = $("password").value;

  if (!u || !p) {
    setMsg($("authMsg"), "Informe usuário e senha.", "warn");
    return;
  }

  try {
    setMsg($("authMsg"), "Autenticando…");
    const data = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: u, password: p }),
    });

    setToken(data.access_token);
    setBadge($("authStatus"), `Autenticado: ${u}`, "ok");
    setMsg($("authMsg"), "Login OK.", "ok");
    refreshButtons();
  } catch (e) {
    setToken("");
    setBadge($("authStatus"), "Não autenticado", "bad");
    setMsg($("authMsg"), e.message, "bad");
    refreshButtons();
  }
}

function logout() {
  setToken("");
  setBadge($("authStatus"), "Não autenticado", "");
  setMsg($("authMsg"), "Sessão encerrada.", "warn");
  previewItems = [];
  renderTable([]);
  renderSummary({ total_linhas: 0, novos: 0, duplicados: 0, invalidos: 0, sem_consentimento: 0 });
  refreshButtons();
}

async function licencaStatus() {
  try {
    setMsg($("licMsg"), "Consultando licença…");
    const data = await apiFetch("/api/v1/licenca", { method: "GET" });
    $("hwid").value = data.hwid || "";
    setBadge($("licStatus"), data.ativa ? "ATIVA" : "INATIVA", data.ativa ? "ok" : "bad");
    setMsg($("licMsg"), data.ativa ? "Licença ativa nesta máquina." : "Licença não ativada.", data.ativa ? "ok" : "warn");
  } catch (e) {
    setBadge($("licStatus"), "ERRO", "bad");
    setMsg($("licMsg"), e.message, "bad");
  }
}

async function licencaAtivar() {
  const serial = $("serial").value.trim();
  if (!serial) {
    setMsg($("licMsg"), "Informe o serial.", "warn");
    return;
  }
  try {
    setMsg($("licMsg"), "Ativando licença…");
    const data = await apiFetch("/api/v1/licenca/ativar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ serial }),
    });
    setMsg($("licMsg"), data.mensagem || "Licença ativada.", "ok");
    await licencaStatus();
  } catch (e) {
    setMsg($("licMsg"), e.message, "bad");
  }
}

async function preview() {
  const file = fileSelected();
  if (!file) return;

  try {
    setBadge($("importStatus"), "Gerando preview…", "warn");
    setMsg($("importMsg"), "Enviando arquivo para preview…");

    const fd = new FormData();
    fd.append("arquivo", file);

    // ✅ Endpoint novo do backend (preview detalhado)
    const data = await apiFetch("/api/v1/dados/importar/preview-detalhado", {
      method: "POST",
      body: fd,
    });

    previewItems = data.itens || [];
    renderSummary(data);
    renderTable(previewItems);

    setBadge($("importStatus"), "Preview pronto", "ok");
    setMsg($("importMsg"), "Preview gerado. Revise as ações e clique em “Aplicar”.", "ok");

    refreshButtons();
  } catch (e) {
    setBadge($("importStatus"), "Erro no preview", "bad");
    setMsg($("importMsg"), e.message, "bad");
    previewItems = [];
    renderTable([]);
    refreshButtons();
  }
}

async function aplicar() {
  const file = fileSelected();
  if (!file) return;

  try {
    setBadge($("importStatus"), "Aplicando…", "warn");
    setMsg($("importMsg"), "Enviando decisões e aplicando importação…");

    const fd = new FormData();
    fd.append("arquivo", file);
    fd.append("modo_duplicados", $("modoDuplicados").value);
    fd.append("decisoes_json", JSON.stringify(buildDecisoesFromTable()));

    const data = await apiFetch("/api/v1/dados/importar/aplicar", {
      method: "POST",
      body: fd,
    });

    setBadge($("importStatus"), "Importação aplicada", "ok");
    setMsg(
      $("importMsg"),
      `OK • Importados: ${data.importados} | Atualizados: ${data.atualizados} | Pulados: ${data.pulados} | Sem LGPD: ${data.sem_consentimento}`,
      "ok"
    );

    // Atualiza preview automaticamente após aplicar (opcional)
    previewItems = [];
    renderTable([]);
    refreshButtons();
  } catch (e) {
    setBadge($("importStatus"), "Erro ao aplicar", "bad");
    setMsg($("importMsg"), e.message, "bad");
  }
}

// ===== Bulk actions =====
function marcarNovosImportar() {
  document.querySelectorAll("#previewTbody tr[data-linha]").forEach((tr) => {
    const statusEl = tr.querySelector("td:nth-child(4) .badge");
    const statusText = statusEl ? statusEl.textContent.trim() : "";
    const sel = tr.querySelector("select[data-acao]");
    if (!sel || sel.disabled) return;
    if (statusText === "NOVO") sel.value = "IMPORTAR";
  });
  setMsg($("importMsg"), "NOVOS marcados como IMPORTAR.", "ok");
}

function marcarDupPular() {
  document.querySelectorAll("#previewTbody tr[data-linha]").forEach((tr) => {
    const statusEl = tr.querySelector("td:nth-child(4) .badge");
    const statusText = statusEl ? statusEl.textContent.trim() : "";
    const sel = tr.querySelector("select[data-acao]");
    if (!sel || sel.disabled) return;
    if (statusText === "DUP_CPF" || statusText === "DUP_NOME") sel.value = "PULAR";
  });
  setMsg($("importMsg"), "Duplicados marcados como PULAR.", "ok");
}

function resetarAcoes() {
  // volta para sugestão original baseada no previewItems
  const map = new Map(previewItems.map((it) => [it.linha, it.sugestao_acao || "PULAR"]));
  document.querySelectorAll("#previewTbody tr[data-linha]").forEach((tr) => {
    const linha = parseInt(tr.getAttribute("data-linha"), 10);
    const sel = tr.querySelector("select[data-acao]");
    if (!sel || sel.disabled) return;
    sel.value = map.get(linha) || "PULAR";
  });
  setMsg($("importMsg"), "Ações resetadas para a sugestão do preview.", "ok");
}

// ===== Wire up =====
window.addEventListener("DOMContentLoaded", () => {
  $("btnPing").addEventListener("click", ping);
  $("btnLogin").addEventListener("click", login);
  $("btnLogout").addEventListener("click", logout);

  $("btnLicencaStatus").addEventListener("click", licencaStatus);
  $("btnLicencaAtivar").addEventListener("click", licencaAtivar);

  $("fileInput").addEventListener("change", () => {
    previewItems = [];
    renderTable([]);
    setBadge($("importStatus"), fileSelected() ? "Arquivo selecionado" : "Aguardando arquivo");
    refreshButtons();
  });

  $("btnPreview").addEventListener("click", preview);
  $("btnAplicar").addEventListener("click", aplicar);

  $("filterText").addEventListener("input", applyFilter);

  $("btnMarcarNovos").addEventListener("click", marcarNovosImportar);
  $("btnMarcarDup").addEventListener("click", marcarDupPular);
  $("btnLimparAcoes").addEventListener("click", resetarAcoes);

  // restaura token se existir na sessão
  if (token()) {
    setBadge($("authStatus"), "Autenticado (token carregado)", "ok");
  }
  refreshButtons();
  ping();
});
