"use strict";
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("session")) {
  sessionStorage.setItem("myskills-session", fragment.get("session"));
  history.replaceState(null, "", "/");
}
const view = document.querySelector("#view"),
  dialog = document.querySelector("#detail");
let currentView = "discover",
  currentDetail = null,
  renderSequence = 0,
  detailSequence = 0;
const escape = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const identity = (m) => ({
  skill_id: m.skill_id,
  version: m.version,
  digest: m.digest,
});
function display(value) {
  if (value === null || value === undefined) return "None declared";
  if (Array.isArray(value))
    return value.length ? value.map(display).join("; ") : "None declared";
  if (typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) => `${key.replaceAll("_", " ")}: ${display(item)}`)
      .join("; ");
  return String(value);
}
function status(message) {
  document.querySelector("#status").textContent = message;
}
async function api(action, params = {}) {
  const response = await fetch("/api", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-MySkills-Session": sessionStorage.getItem("myskills-session") || "",
    },
    body: JSON.stringify({ action, params }),
  });
  const body = await response.json();
  if (!response.ok) throw Error(body.error || "Request failed");
  return body.result;
}
function card(m, extra = "") {
  return `<article class="card"><button class="card-title" data-detail="${escape(m.skill_id)}" data-version="${escape(m.version)}" data-digest="${escape(m.digest)}">${escape(m.name)}</button><p>${escape(m.description)}</p><div class="meta"><span class="tag">${escape(m.trust.replaceAll("_", " "))}</span><span class="tag">${escape(m.qualification.status.replaceAll("_", " "))}</span>${extra}</div><div class="subtle">${escape(m.publisher.display_name)}<br>${escape(m.harness_compatibility.join(" · "))}</div></article>`;
}
const empty = (title, body) =>
  `<div class="empty"><h2>${escape(title)}</h2><p>${escape(body)}</p></div>`;
async function render(name = currentView, query = "") {
  currentView = name;
  const sequence = ++renderSequence;
  document.querySelectorAll("nav button").forEach((b) => {
    if (b.dataset.view === name) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  });
  view.innerHTML = '<p class="loading" role="status">Loading your library…</p>';
  try {
    let html = "";
    if (name === "discover") {
      const skills = await api("search", { query });
      html = `<h1>Choose a capability.<br>Understand its boundaries.</h1><p class="intro">Browse the portable skill collection. Inspect provenance, permissions and qualification before adding a skill to your library.</p><div class="summary"><span><strong>${skills.length}</strong> skills found</span><span><strong>0</strong> platform qualified</span><span>Execution requires separate authority</span></div><form class="search" id="search-form"><label><span class="sr-only">Search skills</span><input name="query" type="search" placeholder="Search API contracts, testing, migrations…" value="${escape(query)}"></label><button class="primary">Search</button></form><div class="grid">${skills.map((m) => card(m)).join("")}</div>${skills.length ? "" : empty("No skills found", "Try a broader capability or a different search term.")}`;
    } else if (name === "installed") {
      const items = await api("installed");
      const details = await Promise.all(
        items.map((i) => api("detail", { identity: i.binding })),
      );
      html = `<h1>Installed</h1><p class="intro">Versions are pinned. Enabling a skill makes it a candidate for resolution; it does not authorize execution.</p><div class="grid">${details.map((d, i) => card(d.manifest, `<span class="tag">${items[i].enabled ? "Enabled" : "Disabled"}</span>`)).join("")}</div>${items.length ? "" : empty("Your library is empty", "Inspect a skill in Discover and choose Install to pin its exact version.")}`;
    } else if (name === "private") {
      const draftRecords = await api("my_skills");
      html = `<h1>My Skills</h1><p class="intro">Capture an explicit reusable process. This local prototype qualifies only the static package contract and grants no effects.</p><form id="draft-form" class="builder"><h2>Create a private draft</h2><div class="form-grid"><label class="field">Skill ID<input name="skill_id" required pattern="[a-z0-9]+(-[a-z0-9]+)*" placeholder="design-checklist"></label><label class="field">Version<input name="version" required value="1.0.0"></label></div><label class="field">Purpose<input name="description" required placeholder="Review changes against our design system"></label><label class="field">Instructions<textarea name="instructions" required placeholder="Use our design system. Check loading and error states. Never modify payments."></textarea></label><button class="primary">Create draft</button></form><div class="grid">${draftRecords.map((d, i) => `<article class="card"><h3>${escape(d.manifest.name)}</h3><p>${escape(d.manifest.description)}</p><div class="meta"><span class="tag">${escape(d.state)}</span><span class="tag">v${escape(d.manifest.version)}</span><span class="tag">Private</span></div><div class="actions">${d.state === "draft" ? `<button data-draft-action="validate" data-skill="${escape(d.manifest.skill_id)}" data-version="${escape(d.manifest.version)}" data-digest="${escape(d.manifest.digest)}">Validate</button>` : d.state === "validated" ? `<button data-draft-action="qualify" data-skill="${escape(d.manifest.skill_id)}" data-version="${escape(d.manifest.version)}" data-digest="${escape(d.manifest.digest)}">Run static qualification</button>` : `<button data-detail="${escape(d.manifest.skill_id)}" data-version="${escape(d.manifest.version)}" data-digest="${escape(d.manifest.digest)}">Inspect qualification</button>${d.state === "qualification revoked" ? "" : `<button data-draft-action="accept_install" data-skill="${escape(d.manifest.skill_id)}" data-version="${escape(d.manifest.version)}" data-digest="${escape(d.manifest.digest)}">Accept & install</button>`}`}</div></article>`).join("")}</div>`;
    } else if (name === "updates") {
      const updates = await api("updates");
      html = `<h1>Updates</h1><p class="intro">Review each exact version and its permission changes. Updates remain disabled until you enable them.</p>${updates.length ? updates.map((entry) => entry.versions.map((diff) => `<article class="card"><h3>${escape(diff.to.skill_id)}</h3><p>${escape(diff.from.version)} → ${escape(diff.to.version)}</p><p>${diff.requires_review ? "Security-relevant changes require review." : "No security declarations changed. Content is a new immutable version."}</p><button data-update="${escape(diff.to.skill_id)}" data-version="${escape(diff.to.version)}" data-digest="${escape(diff.to.digest)}" data-revision="${entry.installation.revision}">Review update</button></article>`).join("")).join("") : empty("No updates to review", "Your installed versions stay pinned. New versions never install automatically.")}`;
    } else if (name === "permissions") {
      html = `<h1>Trust & permissions</h1><p class="intro">Know what a skill requests, what has been verified, and which decisions still belong to you.</p><div class="grid"><article class="card"><h2>Installation</h2><p>Pins a version in your library. It grants no tools, credentials, spending or Work authority.</p></article><article class="card"><h2>Qualification</h2><p>Applies to an exact version, digest, runtime, policy and test corpus. A valid manifest alone is not behavioral qualification.</p></article><article class="card"><h2>Execution</h2><p>Requires separate owner, Work and Factory authority. The strictest effects and resource limits win.</p></article><article class="card"><h2>Publication</h2><p>Requires a separate decision after verification. Marketplace publishing and payments are unavailable in this prototype.</p></article></div>`;
    } else {
      const drafts = await api("my_skills");
      const evaluated = drafts.filter((d) =>
        ["qualified", "installed"].includes(d.state),
      );
      html = `<h1>Qualification</h1><p class="intro">Evidence describes only the checks that ran. Static package qualification does not prove that free-form instructions are safe or that their outputs are correct.</p><div class="notice">The 92 imported skills remain NOT_EVALUATED. No skill in this prototype is PLATFORM_QUALIFIED.</div><div class="grid">${evaluated.map((d) => card(d.manifest, '<span class="tag">Static evidence available</span>')).join("")}</div>${evaluated.length ? "" : empty("No qualification evidence yet", "Create and validate a private draft to run the deterministic static package checks.")}`;
    }
    if (sequence === renderSequence) view.innerHTML = html;
  } catch (error) {
    if (sequence === renderSequence)
      view.innerHTML = `<h1>Library unavailable</h1><p class="error" role="alert">${escape(error.message)}</p><button data-retry>Try again</button>`;
  }
}
async function detail(id) {
  const sequence = ++detailSequence;
  const result = await api("detail", { identity: id });
  if (sequence !== detailSequence) return;
  currentDetail = result;
  const d = currentDetail,
    m = d.manifest;
  const facts = [
    ["Publisher", m.publisher.display_name],
    ["Version", m.version],
    ["Digest", m.digest],
    ["Trust", m.trust],
    ["Lifecycle", d.lifecycle],
    [
      "Qualification",
      d.evidence.length
        ? d.evidence
            .map(
              (e) =>
                `${d.current_evidence.includes(e.evidence_digest) ? e.status : "REVOKED / historical"} · ${e.runtime}`,
            )
            .join(", ")
        : m.qualification.status,
    ],
    ["Required capabilities", display(m.required_capabilities)],
    ["Requested effects", display(m.permitted_effects)],
    ["Network", m.network_requirements.mode],
    ["Secrets", display(m.secret_requirements)],
    ["Dependencies", display(m.dependencies)],
    ["Compatible packaging", display(m.harness_compatibility)],
    ["Provenance", m.provenance.source],
    ["Upstream revision", m.provenance.revision],
    ["License", m.provenance.license],
  ];
  document.querySelector("#detail-content").innerHTML =
    `<h2 id="detail-title">${escape(m.name)}</h2><p>${escape(m.description)}</p>${m.metadata_status === "UNREVIEWED" ? '<div class="notice">Requirements have not been reviewed. Empty declarations do not mean this skill has no dependencies. It cannot resolve for execution.</div>' : ""}<dl class="facts">${facts.map(([label, value]) => `<dt>${label}</dt><dd${label === "Digest" ? ' class="mono"' : ""}>${escape(value)}</dd>`).join("")}</dl>${d.evidence.map((e) => `<section class="section"><h3>${d.current_evidence.includes(e.evidence_digest) ? "Static qualification evidence" : "Historical evidence · no longer eligible"}</h3><p>${escape(e.limitations.join(" "))}</p><p class="mono">${escape(e.evidence_digest)}</p><p>Reviewer: ${escape(e.reviewer)}</p></section>`).join("")}<div class="actions">${d.lifecycle === "revoked" ? '<p class="error">This version is revoked. New use is unavailable.</p>' : d.installation ? `<button id="toggle-enabled">${d.installation.enabled ? "Disable" : "Enable"}</button><button id="uninstall">Uninstall</button>` : d.other_installation ? "<p>Another version is installed. Review this exact version in Updates.</p>" : '<button id="install" class="primary">Install exact version</button>'}</div><p class="subtle">Installation grants no execution or publication authority.</p>`;
  if (!dialog.open) dialog.showModal();
}
document.querySelector("#close-detail").onclick = () => {
  detailSequence++;
  dialog.close();
};
dialog.addEventListener("cancel", () => {
  detailSequence++;
});
document.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button || button.id === "approve-update") return;
  try {
    if (button.dataset.view) return await render(button.dataset.view);
    if (button.hasAttribute("data-retry")) return await render();
    if (button.dataset.detail)
      return await detail({
        skill_id: button.dataset.detail,
        version: button.dataset.version,
        digest: button.dataset.digest,
      });
    button.disabled = true;
    if (button.dataset.draftAction) {
      const target = {
        skill_id: button.dataset.skill,
        version: button.dataset.version,
        digest: button.dataset.digest,
      };
      await api(button.dataset.draftAction, { identity: target });
      status("Private skill state updated. No execution occurred.");
      await render("private");
    } else if (button.id === "install") {
      await api("install", { identity: identity(currentDetail.manifest) });
      status(
        "Installed exact version. Starts disabled. No Work authority created.",
      );
      if (dialog.open) await detail(identity(currentDetail.manifest));
    } else if (button.id === "toggle-enabled") {
      const i = currentDetail.installation;
      await api("enable", {
        skill_id: i.binding.skill_id,
        enabled: !i.enabled,
        expected_revision: i.revision,
      });
      status(
        "Enabled state updated. Qualification and authority are still required.",
      );
      if (dialog.open) await detail(identity(currentDetail.manifest));
    } else if (button.id === "uninstall") {
      const i = currentDetail.installation;
      await api("uninstall", {
        skill_id: i.binding.skill_id,
        expected_revision: i.revision,
      });
      dialog.close();
      status("Uninstalled. Historical package identity is retained.");
      await render();
    } else if (button.dataset.update) {
      const target = {
        skill_id: button.dataset.update,
        version: button.dataset.version,
        digest: button.dataset.digest,
      };
      const revision = Number(button.dataset.revision);
      const review = await api("review_update", {
        skill_id: target.skill_id,
        target,
        expected_revision: revision,
      });
      document.querySelector("#detail-content").innerHTML =
        `<h2 id="detail-title">Review update</h2><p>${escape(target.skill_id)} · ${escape(target.version)}</p>${
          Object.entries(review.diff.security_changes)
            .map(
              ([field, change]) =>
                `<h3>${escape(field.replaceAll("_", " "))}</h3><p>Before: ${escape(display(change.before))}<br>After: ${escape(display(change.after))}</p>`,
            )
            .join("") ||
          "<p>No security declarations changed. The content has a new version and digest.</p>"
        }<p class="mono">${escape(target.digest)}</p><p>The new version starts disabled. Existing Work keeps its original version.</p><button id="approve-update" class="primary">Approve exact update</button>`;
      dialog.showModal();
      document.querySelector("#approve-update").onclick = async (event) => {
        const approvalButton = event.currentTarget;
        approvalButton.disabled = true;
        try {
          await api("update", {
            skill_id: target.skill_id,
            target,
            expected_revision: revision,
            decision_digest: review.decision_digest,
          });
          dialog.close();
          status("Update installed and disabled.");
          await render("updates");
        } catch (error) {
          status(error.message);
        } finally {
          approvalButton.disabled = false;
        }
      };
    }
  } catch (error) {
    status(error.message);
  } finally {
    button.disabled = false;
  }
});
document.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target,
    button = form.querySelector("button");
  button.disabled = true;
  try {
    const data = Object.fromEntries(new FormData(form));
    if (form.id === "search-form") await render("discover", data.query);
    if (form.id === "draft-form") {
      await api("draft", data);
      status(
        "Private draft created. Review and validate before qualification.",
      );
      await render("private");
    }
  } catch (error) {
    status(error.message);
  } finally {
    button.disabled = false;
  }
});
render();
