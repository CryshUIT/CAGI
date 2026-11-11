// Mo tung man hinh bang Playwright, kiem tra console error, luu screenshot.
// Chi chay sau khi: data da sinh, backend dang chay tai :8420.
import { chromium } from "playwright";
import { mkdirSync } from "fs";

const BASE = "http://127.0.0.1:8420";
const OUT_DIR = "../../results/dashboard_screenshots";
mkdirSync(OUT_DIR, { recursive: true });

const PAGES = [
  { path: "/", name: "01_overview" },
  { path: "/incidents", name: "02_incidents" },
  { path: "/new-analysis", name: "03_new_analysis" },
  { path: "/explainability", name: "04_explainability" },
  { path: "/settings", name: "05_settings" },
];

const errors = {};

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      errors[page.url()] = errors[page.url()] || [];
      errors[page.url()].push(msg.text());
    }
  });
  page.on("pageerror", (err) => {
    errors[page.url()] = errors[page.url()] || [];
    errors[page.url()].push(String(err));
  });

  for (const p of PAGES) {
    await page.goto(`${BASE}${p.path}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${OUT_DIR}/${p.name}.png`, fullPage: true });
    console.log(`Saved ${p.name}`);
  }

  // Investigation page voi 1 incident co endpoint confirmed - thu bsc_token_hub_2022
  await page.goto(`${BASE}/investigation/bsc_token_hub_2022`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `${OUT_DIR}/06_investigation_overview.png`, fullPage: true });

  await page.click("text=Transaction Timeline");
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT_DIR}/07_investigation_timeline.png`, fullPage: true });

  await page.click("text=Flow Graph");
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${OUT_DIR}/08_investigation_flow.png`, fullPage: true });

  await page.click("text=Explainability (SHAP)");
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT_DIR}/09_investigation_shap.png`, fullPage: true });

  await page.click("text=AADAPT");
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT_DIR}/10_investigation_aadapt.png`, fullPage: true });

  await browser.close();

  console.log("\n=== Console errors theo URL ===");
  console.log(JSON.stringify(errors, null, 2));
})();
