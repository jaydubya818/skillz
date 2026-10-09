import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdir, writeFile, readFile } from "node:fs/promises";
const { chromium } = await import(
  process.env.MYSKILLS_PLAYWRIGHT_MODULE ||
    "../scripts/myskills-browser/node_modules/playwright/index.mjs"
);
const server = spawn(
  process.env.PYTHON || "python3",
  ["-m", "myskills.ui", "--port", "0"],
  { stdio: ["ignore", "pipe", "inherit"] },
);
const url = await new Promise((resolve, reject) => {
  let data = "";
  server.stdout.on("data", (chunk) => {
    data += chunk;
    if (data.includes("\n")) {
      try {
        resolve(JSON.parse(data.split("\n")[0]).url);
      } catch (error) {
        reject(error);
      }
    }
  });
  server.on("exit", (code) => reject(Error(`server exited ${code}`)));
  setTimeout(() => reject(Error("server timeout")), 10000).unref();
});
const browser = await chromium.launch({ headless: true });
const output =
  process.env.MYSKILLS_BROWSER_OUTPUT || ".artifacts/myskills/browser";
await mkdir(output, { recursive: true });
const checks = [];
async function check(name, fn) {
  await fn();
  checks.push({ name, result: "PASS" });
}
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  const axeSource = await readFile(
    new URL(
      "../scripts/myskills-browser/node_modules/axe-core/axe.min.js",
      import.meta.url,
    ),
    "utf8",
  );
  async function accessibility(name) {
    await page.evaluate(axeSource);
    await check("Accessibility: " + name, async () => {
      const results = await page.evaluate(() =>
        axe.run({
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        }),
      );
      assert.deepEqual(
        results.violations.map((v) => ({
          id: v.id,
          nodes: v.nodes.map((n) => n.target),
        })),
        [],
      );
    });
  }
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(url);
  await page.getByRole("heading", { level: 1 }).waitFor();
  await check("Discover shows actual catalog", async () =>
    assert.equal(await page.locator(".card").count(), 92),
  );
  await accessibility("Discover desktop");
  await page.screenshot({ path: `${output}/discover-desktop.png` });
  await check("Desktop layout regression", async () => {
    assert.equal(
      await page
        .locator("aside")
        .evaluate((el) => Math.round(el.getBoundingClientRect().width)),
      230,
    );
    assert.equal(
      await page
        .locator(".grid")
        .evaluate(
          (el) => getComputedStyle(el).gridTemplateColumns.split(" ").length,
        ),
      2,
    );
  });
  await page
    .getByRole("searchbox", { name: "Search skills" })
    .fill("API contracts");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("button", { name: /Api and interface design/i }).click();
  await page.getByRole("dialog").waitFor();
  await page
    .getByRole("heading", { name: /Api and interface design/i })
    .waitFor();
  await check("Detail exposes trust and exact digest", async () => {
    assert.match(await page.locator("dialog").innerText(), /UNTRUSTED/);
    assert.match(
      await page.locator("dialog").innerText(),
      /sha256:[a-f0-9]{64}/,
    );
  });
  await page
    .getByRole("button", { name: "Install exact version", exact: true })
    .click();
  await page.getByRole("button", { name: "Enable", exact: true }).waitFor();
  await page.getByRole("button", { name: "Enable", exact: true }).click();
  await page.getByRole("button", { name: "Disable", exact: true }).waitFor();
  await page.getByRole("button", { name: "Disable", exact: true }).click();
  await page.getByRole("button", { name: "Enable", exact: true }).waitFor();
  await accessibility("Skill detail dialog");
  await page.screenshot({ path: `${output}/detail-desktop.png` });
  await page.keyboard.press("Escape");
  await check("Escape closes accessible detail dialog", async () =>
    assert.equal(await page.locator("dialog").evaluate((el) => el.open), false),
  );
  await page.getByRole("button", { name: "Installed", exact: true }).click();
  await page.getByRole("heading", { name: "Installed", exact: true }).waitFor();
  await check("UI and action service use same installed state", async () => {
    const result = await page.evaluate(async () => {
      const response = await fetch("/api", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-MySkills-Session": sessionStorage.getItem("myskills-session"),
        },
        body: JSON.stringify({ action: "installed", params: {} }),
      });
      return response.json();
    });
    assert.equal(result.result.length, 1);
    assert.equal(result.result[0].enabled, false);
    assert.equal(result.result[0].binding.skill_id, "api-and-interface-design");
  });
  await page.getByRole("button", { name: "My Skills", exact: true }).click();
  async function createPrivate(version, instructions) {
    await page.getByLabel("Skill ID", { exact: true }).fill("design-checklist");
    await page.getByLabel("Version", { exact: true }).fill(version);
    await page
      .getByLabel("Purpose", { exact: true })
      .fill("Review design system");
    await page.getByLabel("Instructions", { exact: true }).fill(instructions);
    await page
      .getByRole("button", { name: "Create draft", exact: true })
      .click();
    const card = page.locator(".card").filter({ hasText: `v${version}` });
    await card.getByRole("button", { name: "Validate", exact: true }).click();
    await card
      .getByRole("button", { name: "Run static qualification", exact: true })
      .click();
    await card
      .getByRole("button", { name: "Inspect qualification", exact: true })
      .waitFor();
    return card;
  }
  let card = await createPrivate(
    "1.0.0",
    "Use our design system. Never modify payments.",
  );
  await card
    .getByRole("button", { name: "Accept & install", exact: true })
    .click();
  await check(
    "Private lifecycle separates qualification from install",
    async () => {
      await card
        .locator(".tag")
        .filter({ hasText: /^installed$/ })
        .waitFor();
      assert.match(await card.innerText(), /installed/);
    },
  );
  await createPrivate(
    "1.1.0",
    "Use our design system. Check mobile. Never modify payments.",
  );
  await page.getByRole("button", { name: "Updates", exact: true }).click();
  await page
    .getByRole("button", { name: "Review update", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Review update", exact: true })
    .waitFor();
  await check("Nested permission changes remain readable", async () => {
    const text = await page.locator("dialog").innerText();
    assert.ok(!text.includes("[object Object]"));
    assert.match(text, /revision:/);
  });
  await accessibility("Permission review dialog");
  await page.screenshot({ path: `${output}/update-desktop.png` });
  await page
    .getByRole("button", { name: "Approve exact update", exact: true })
    .click();
  await page
    .getByRole("status")
    .filter({ hasText: "Update installed and disabled." })
    .waitFor();
  await check(
    "Updated installation pins successor and remains disabled",
    async () => {
      const data = await page.evaluate(async () => {
        const response = await fetch("/api", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-MySkills-Session": sessionStorage.getItem("myskills-session"),
          },
          body: JSON.stringify({ action: "installed", params: {} }),
        });
        return (await response.json()).result;
      });
      const item = data.find((i) => i.binding.skill_id === "design-checklist");
      assert.equal(item.binding.version, "1.1.0");
      assert.equal(item.enabled, false);
    },
  );
  await page
    .getByRole("button", { name: "Qualification", exact: true })
    .click();
  await page
    .getByRole("heading", { name: "Qualification", exact: true })
    .waitFor();
  await check(
    "No authentication bypass or arbitrary owner/admin action",
    async () => {
      const origin = new URL(url).origin;
      const denied = await page.request.post(origin + "/api", {
        data: { action: "installed", params: {} },
      });
      assert.equal(denied.status(), 403);
      const token = new URL(url).hash.slice("#session=".length);
      const cross = await page.request.post(origin + "/api", {
        headers: {
          "X-MySkills-Session": token,
          Origin: "https://attacker.invalid",
        },
        data: { action: "installed", params: {} },
      });
      assert.equal(cross.status(), 403);
      const admin = await page.request.post(origin + "/api", {
        headers: { "X-MySkills-Session": token },
        data: { action: "revoke_publisher", params: {} },
      });
      assert.equal(admin.status(), 400);
      const owner = await page.request.post(origin + "/api", {
        headers: { "X-MySkills-Session": token },
        data: { action: "search", params: { owner: "other" } },
      });
      assert.equal(owner.status(), 400);
    },
  );
  await check(
    "Late private-list responses cannot retarget visible actions",
    async () => {
      const drafts = await page.evaluate(async () => {
        const r = await fetch("/api", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-MySkills-Session": sessionStorage.getItem("myskills-session"),
          },
          body: JSON.stringify({ action: "my_skills", params: {} }),
        });
        return (await r.json()).result;
      });
      let held = null,
        seen = 0,
        validated = null;
      await page.route("**/api", async (route) => {
        const body = route.request().postDataJSON();
        if (body.action === "validate") validated = body.params.identity;
        if (body.action !== "my_skills") return route.continue();
        seen++;
        if (seen === 1) {
          held = route;
          return;
        }
        return route.fulfill({
          json: { result: [{ ...drafts[1], state: "draft" }] },
        });
      });
      await page
        .getByRole("button", { name: "My Skills", exact: true })
        .click();
      await page.waitForFunction(() => document.querySelector(".loading"));
      await page
        .getByRole("button", { name: "Installed", exact: true })
        .click();
      await page
        .getByRole("heading", { name: "Installed", exact: true })
        .waitFor();
      await page
        .getByRole("button", { name: "My Skills", exact: true })
        .click();
      await page.locator(".card").filter({ hasText: "v1.1.0" }).waitFor();
      assert.ok(held);
      await held.fulfill({
        json: { result: [{ ...drafts[0], state: "draft" }] },
      });
      await page.getByRole("button", { name: "Validate", exact: true }).click();
      await page
        .getByRole("status")
        .filter({ hasText: "Private skill state updated" })
        .waitFor();
      assert.equal(validated.version, "1.1.0");
      await page.unroute("**/api");
    },
  );
  await page.route("**/api", async (route) => {
    if (route.request().postDataJSON().action === "search")
      return route.abort();
    return route.continue();
  });
  await page.getByRole("button", { name: "Discover", exact: true }).click();
  await page.getByRole("heading", { name: "Library unavailable" }).waitFor();
  await page.unroute("**/api");
  await page.getByRole("button", { name: "Try again", exact: true }).click();
  await page.getByRole("searchbox").waitFor();
  checks.push({
    name: "Error and retry return to canonical state",
    result: "PASS",
  });
  await page.getByRole("button", { name: "Discover", exact: true }).click();
  await page.getByRole("searchbox").waitFor();
  await page.getByRole("searchbox").fill("nothing-matches-this-query");
  await page.getByRole("button", { name: "Search", exact: true }).click();
  await page.getByRole("heading", { name: "No skills found" }).waitFor();
  await page.getByRole("button", { name: "Discover", exact: true }).click();
  await page.getByRole("searchbox").waitFor();
  await page.setViewportSize({ width: 390, height: 844 });
  await accessibility("Discover mobile");
  await page.screenshot({ path: `${output}/discover-mobile.png` });
  await check("Mobile layout regression", async () => {
    assert.equal(
      await page
        .locator(".grid")
        .evaluate(
          (el) => getComputedStyle(el).gridTemplateColumns.split(" ").length,
        ),
      1,
    );
    assert.equal(
      await page.locator("nav button[aria-current=page]").innerText(),
      "Discover",
    );
  });
  await check("Mobile layout has no horizontal page overflow", async () =>
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      true,
    ),
  );
  await check(
    "Controls have accessible names and one primary heading",
    async () => {
      assert.equal(await page.locator("h1").count(), 1);
      const unlabeled = await page.evaluate(
        () =>
          [...document.querySelectorAll("button,input,textarea")].filter(
            (el) =>
              el.getClientRects().length &&
              !(
                el.getAttribute("aria-label") ||
                el.textContent.trim() ||
                el.labels?.length
              ),
          ).length,
      );
      assert.equal(unlabeled, 0);
    },
  );
  await page.keyboard.press("Tab");
  await check("Keyboard focus is visible", async () =>
    assert.ok(
      await page.evaluate(() => document.activeElement !== document.body),
    ),
  );
  const screenshotA = await page.screenshot();
  const screenshotB = await page.screenshot();
  await check("Critical mobile screenshot is stable at rest", async () =>
    assert.ok(screenshotA.equals(screenshotB)),
  );
  await check("No browser script errors", async () =>
    assert.deepEqual(errors, []),
  );
  if (process.env.MYSKILLS_VISUAL_BASELINE) {
    for (const name of [
      "discover-desktop",
      "detail-desktop",
      "update-desktop",
      "discover-mobile",
    ]) {
      await check("Pixel regression: " + name, async () =>
        assert.ok(
          (await readFile(`${output}/${name}.png`)).equals(
            await readFile(
              `${process.env.MYSKILLS_VISUAL_BASELINE}/${name}.png`,
            ),
          ),
        ),
      );
    }
  }

  await writeFile(
    `${output}/report.json`,
    JSON.stringify(
      {
        checks,
        limitations: [
          "axe WCAG A/AA automation, layout regression, keyboard and screenshot stability checks; not a complete manual WCAG audit.",
          "Static package qualification only; no instructions executed.",
        ],
        production_effects: 0,
        paid_operations: 0,
      },
      null,
      2,
    ),
  );
  console.log(
    JSON.stringify({ checks: checks.length, status: "PASS", output }),
  );
} finally {
  await browser.close();
  server.kill("SIGTERM");
}
