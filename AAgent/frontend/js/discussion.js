/**
 * AI圆桌讨论室
 * 支持：主持人、专家状态小窗、实时共识/分歧、规范Transcript
 */

// ── 全局状态 ──────────────────────────────
let discussionId = null;
let discussion = null;
let participants = [];
let messages = [];
let eventSource = null;
let currentRound = 0;
let typingTimers = [];

// ── DOM引用 ────────────────────────────────
const DOM = {
    title:                document.getElementById("discussionTitle"),
    description:          document.getElementById("discussionDescription"),
    status:               document.getElementById("discussionStatus"),
    currentRound:         document.getElementById("currentRound"),
    totalRounds:          document.getElementById("totalRounds"),
    progressBar:          document.getElementById("progressBar"),
    expertsCircle:        document.getElementById("expertsCircle"),
    messagesContainer:    document.getElementById("messagesContainer"),
    emptyMessages:        document.getElementById("emptyMessages"),
    generatingIndicator:  document.getElementById("generatingIndicator"),
    generatingText:       document.getElementById("generatingText"),
    messagesTotal:        document.getElementById("messagesTotal"),
    speakersCount:        document.getElementById("speakersCount"),
    messageCountNumber:   document.getElementById("messageCountNumber"),
    realtimeAgreements:   document.getElementById("realtimeAgreements"),
    realtimeDivergences:  document.getElementById("realtimeDivergences"),
    noConsensus:          document.getElementById("noConsensus"),
    consensusContent:     document.getElementById("consensusContent"),
    consensusSummary:     document.getElementById("consensusSummary"),
    consensusPoints:      document.getElementById("consensusPoints"),
    completionNotice:     document.getElementById("completionNotice")
};

// ── 页面初始化 ─────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
    const params = new URLSearchParams(window.location.search);
    discussionId = parseInt(params.get("id"));

    if (!discussionId) {
        showNotification("讨论ID无效", "error");
        setTimeout(() => window.location.href = "/", 2000);
        return;
    }

    await loadDiscussion();

    if (discussion && discussion.status === "running") {
        connectToSSE();
    }
});

// ── 数据加载 ───────────────────────────────
async function loadDiscussion() {
    try {
        const data = await getDiscussion(discussionId);
        discussion   = data.discussion;
        participants = data.participants || [];
        messages     = data.messages    || [];

        renderDiscussionInfo();
        renderExpertCards();
        renderMessages();
        updateStats();

        if (data.consensus) {
            renderFinalConsensus(data.consensus);
        }
    } catch (err) {
        console.error("加载讨论失败:", err);
        showNotification("加载讨论失败：" + err.message, "error");
        setTimeout(() => window.location.href = "/", 2000);
    }
}

// ── 讨论基本信息 ───────────────────────────
function renderDiscussionInfo() {
    DOM.title.textContent       = discussion.title;
    DOM.description.textContent = discussion.description || "";
    DOM.currentRound.textContent = currentRound || "0";

    const s = getStatusDisplay(discussion.status);
    DOM.status.className   = `badge badge-${discussion.status}`;
    DOM.status.textContent = s.text;
}

// ── 专家状态小窗 ───────────────────────────
function renderExpertCards() {
    DOM.expertsCircle.innerHTML = participants.map(p => `
        <div class="expert-status-card" id="expert-${p.id}" data-id="${p.id}">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                     style="background: ${p.avatar_color}; color: #fff;">
                    ${p.name.charAt(0)}
                </div>
                <div class="min-w-0 flex-1">
                    <div class="text-xs font-semibold truncate">${p.name}</div>
                    <div class="text-xs truncate" style="color: var(--color-text-muted);">${p.role}</div>
                </div>
            </div>
            <div class="mt-1.5 flex items-center gap-1.5">
                <span class="state-dot w-1.5 h-1.5 rounded-full bg-slate-600 flex-shrink-0"></span>
                <span class="state-label text-xs" style="color: var(--color-text-muted);">待机</span>
            </div>
        </div>
    `).join("");

    // 主持人卡片置顶
    const moderatorCard = `
        <div class="expert-status-card mb-3" style="border-color: rgba(99,102,241,0.4); background: rgba(99,102,241,0.08);">
            <div class="flex items-center gap-2">
                <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0"
                     style="background: #6366F1; color: #fff;">主</div>
                <div class="min-w-0 flex-1">
                    <div class="text-xs font-semibold truncate">主持人</div>
                    <div class="text-xs truncate" style="color: var(--color-text-muted);">圆桌主持人</div>
                </div>
            </div>
        </div>
    `;
    DOM.expertsCircle.insertAdjacentHTML("afterbegin", moderatorCard);

    if (DOM.speakersCount) DOM.speakersCount.textContent = `(${participants.length})`;
}

function setExpertState(participantId, state, stateText) {
    const card = document.getElementById(`expert-${participantId}`);
    if (!card) return;

    const dot   = card.querySelector(".state-dot");
    const label = card.querySelector(".state-label");

    card.classList.remove("state-idle", "state-thinking", "state-speaking");
    card.classList.add(`state-${state}`);

    const colors = { idle: "bg-slate-600", thinking: "bg-yellow-400", speaking: "bg-green-400" };
    if (dot) {
        dot.className = `state-dot w-1.5 h-1.5 rounded-full flex-shrink-0 ${colors[state] || "bg-slate-600"}`;
        if (state === "speaking") dot.classList.add("animate-pulse");
    }
    if (label) label.textContent = stateText || state;
}

// ── 渲染历史消息 ───────────────────────────
function renderMessages() {
    if (messages.length === 0) {
        DOM.emptyMessages.classList.remove("hidden");
        DOM.messagesContainer.classList.add("hidden");
        return;
    }
    DOM.emptyMessages.classList.add("hidden");
    DOM.messagesContainer.classList.remove("hidden");
    DOM.messagesContainer.innerHTML = messages.map(msg => {
        const p = participants.find(x => x.id === msg.participant_id);
        return p ? createBubble(msg, p, false) : "";
    }).join("");
    scrollToBottom();
}

function createBubble(msg, p, isModerator) {
    const color    = isModerator ? "#6366F1" : p.avatar_color;
    const name     = isModerator ? "主持人"  : p.name;
    const role     = isModerator ? "圆桌主持人" : p.role;
    const initial  = name.charAt(0);
    const roundTag = msg.round_number || msg.round
        ? `<span class="text-xs px-2 py-0.5 rounded-full ml-1" style="background: var(--color-bg-tertiary); color: var(--color-text-muted);">第 ${msg.round_number || msg.round} 轮</span>`
        : "";

    return `
        <div class="message-bubble animate-fadeIn ${isModerator ? "moderator-bubble" : ""}"
             style="border-left-color: ${color};">
            <div class="flex gap-3">
                <div class="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0"
                     style="background: ${color}; color: #fff;">${initial}</div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center flex-wrap gap-1 mb-1.5">
                        <span class="font-semibold text-sm">${name}</span>
                        <span class="text-xs px-2 py-0.5 rounded-full"
                              style="background: var(--color-bg-tertiary); color: var(--color-text-muted);">${role}</span>
                        ${roundTag}
                        <span class="text-xs ml-auto" style="color: var(--color-text-muted);">${formatDateTime(msg.created_at)}</span>
                    </div>
                    <div class="text-sm leading-relaxed" style="color: var(--color-text-secondary);">${msg.content}</div>
                </div>
            </div>
        </div>`;
}

// ── 新消息（打字机效果）──────────────────
function addMessageTyping(msgData) {
    const isModerator = !!msgData.is_moderator;
    const p  = isModerator ? { avatar_color: "#6366F1", name: "主持人", role: "圆桌主持人" } : msgData.participant;
    const id = `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`;

    DOM.emptyMessages.classList.add("hidden");
    DOM.messagesContainer.classList.remove("hidden");

    const color   = p.avatar_color;
    const name    = isModerator ? "主持人" : p.name;
    const role    = isModerator ? "圆桌主持人" : p.role;
    const initial = name.charAt(0);
    const round   = msgData.round || msgData.round_number;

    DOM.messagesContainer.insertAdjacentHTML("beforeend", `
        <div class="message-bubble animate-fadeIn ${isModerator ? "moderator-bubble" : ""}"
             id="${id}" style="border-left-color: ${color};">
            <div class="flex gap-3">
                <div class="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0"
                     style="background: ${color}; color: #fff;">${initial}</div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center flex-wrap gap-1 mb-1.5">
                        <span class="font-semibold text-sm">${name}</span>
                        <span class="text-xs px-2 py-0.5 rounded-full"
                              style="background: var(--color-bg-tertiary); color: var(--color-text-muted);">${role}</span>
                        ${round ? `<span class="text-xs px-2 py-0.5 rounded-full ml-1" style="background: var(--color-bg-tertiary); color: var(--color-text-muted);">第 ${round} 轮</span>` : ""}
                    </div>
                    <div id="${id}-content" class="text-sm leading-relaxed" style="color: var(--color-text-secondary);"></div>
                </div>
            </div>
        </div>`);

    typeText(id + "-content", msgData.content, () => {
        messages.push(msgData);
        updateStats();
    });

    scrollToBottom();
}

function typeText(elId, text, done) {
    const el = document.getElementById(elId);
    if (!el) { if (done) done(); return; }
    let i = 0;
    function tick() {
        if (i < text.length) {
            el.textContent += text.charAt(i++);
            if (i % 8 === 0) scrollToBottom();
            const t = setTimeout(tick, 22);
            typingTimers.push(t);
        } else {
            if (done) done();
        }
    }
    tick();
}

// ── 最终共识渲染 ────────────────────────
function renderFinalConsensus(consensus) {
    DOM.noConsensus.classList.add("hidden");
    DOM.consensusContent.classList.remove("hidden");

    DOM.consensusSummary.textContent = consensus.summary || "";

    const pts = Array.isArray(consensus.key_points)
        ? consensus.key_points
        : (Array.isArray(consensus.keyPoints) ? consensus.keyPoints : []);

    DOM.consensusPoints.innerHTML = pts.map((pt, i) => `
        <li class="flex items-start gap-2 p-2 rounded-lg" style="background: var(--color-bg-tertiary);">
            <span class="w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style="background: var(--color-status-running); color: #fff;">${i + 1}</span>
            <span class="text-xs leading-relaxed">${pt}</span>
        </li>`).join("");
}

// ── 实时共识更新 ────────────────────────
function updateRealtimeConsensus(agreements, divergences) {
    if (DOM.realtimeAgreements) {
        DOM.realtimeAgreements.innerHTML = (agreements || []).length
            ? agreements.map(a => `
                <div class="flex items-start gap-1.5">
                    <span class="text-blue-400 flex-shrink-0 mt-0.5">✓</span>
                    <span class="text-xs text-slate-300">${a}</span>
                </div>`).join("")
            : `<p class="text-xs text-slate-500 italic">正在提炼...</p>`;
    }
    if (DOM.realtimeDivergences) {
        DOM.realtimeDivergences.innerHTML = (divergences || []).length
            ? divergences.map(d => `
                <div class="flex items-start gap-1.5">
                    <span class="text-orange-400 flex-shrink-0 mt-0.5">⚡</span>
                    <span class="text-xs text-slate-300">${d}</span>
                </div>`).join("")
            : `<p class="text-xs text-slate-500 italic">暂无明显分歧</p>`;
    }
}

// ── SSE 实时连接 ────────────────────────
function connectToSSE() {
    DOM.generatingIndicator.classList.remove("hidden");

    eventSource = connectSSE(discussionId, {
        onMessage: (data) => {
            const isMod = !!data.is_moderator;
            const pName = isMod ? "主持人" : (data.participant && data.participant.name);
            DOM.generatingText.textContent = `${pName} 正在发言...`;

            if (!isMod && data.participant) {
                setExpertState(data.participant.id, "speaking", "发言中");
                setTimeout(() => setExpertState(data.participant.id, "idle", "待机"), 4000);
            }

            addMessageTyping(data);

            if (!isMod) {
                currentRound = data.round || currentRound;
                DOM.currentRound.textContent = currentRound;
                updateProgressBar();
            }
        },

        onStatus: (data) => {
            if (data.type === "expert_state") {
                setExpertState(data.participantId, data.state, data.stateText);
            } else if (data.type === "realtime_consensus") {
                updateRealtimeConsensus(data.agreements, data.divergences);
            }
        },

        onConsensus: (data) => {
            DOM.generatingText.textContent = "正在生成最终共识...";
            renderFinalConsensus({
                summary:    data.summary,
                key_points: data.keyPoints
            });
        },

        onComplete: () => {
            DOM.generatingIndicator.classList.add("hidden");
            discussion.status = "completed";
            DOM.status.className   = "badge badge-completed";
            DOM.status.textContent = "已完成";
            DOM.completionNotice.classList.remove("hidden");
            setTimeout(() => DOM.completionNotice.classList.add("hidden"), 5000);
        },

        onError: () => {
            DOM.generatingIndicator.classList.add("hidden");
            showNotification("实时连接已断开，请刷新页面", "error");
        }
    });
}

// ── 统计与进度 ──────────────────────────
function updateStats() {
    const count = messages.length;
    if (DOM.messagesTotal)     DOM.messagesTotal.textContent     = count;
    if (DOM.messageCountNumber) DOM.messageCountNumber.textContent = count;
}

function updateProgressBar() {
    const max = parseInt(DOM.totalRounds.textContent) || 3;
    DOM.progressBar.style.width = `${Math.min((currentRound / max) * 100, 100)}%`;
}

// ── 工具函数 ────────────────────────────
function scrollToBottom() {
    setTimeout(() => {
        if (DOM.messagesContainer) {
            DOM.messagesContainer.scrollTop = DOM.messagesContainer.scrollHeight;
        }
    }, 80);
}

function showNotification(msg, type = "info") {
    const colors = { success: "#10b981", error: "#ef4444", info: "#3b82f6", warning: "#f59e0b" };
    const el = document.createElement("div");
    el.style.cssText = `position:fixed;top:24px;right:24px;background:${colors[type]};color:#fff;
        padding:12px 20px;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.4);z-index:9999;
        font-size:14px;font-weight:500;max-width:320px;`;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3500);
}

// ── 页面卸载清理 ────────────────────────
window.addEventListener("beforeunload", () => {
    if (eventSource) eventSource.close();
    typingTimers.forEach(t => clearTimeout(t));
});
