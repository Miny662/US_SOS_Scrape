const fs = require('fs');
const path = require('path');
const { scrapeSingleID } = require('./process_request');
const { delay } = require('./helpers');

const startID = 100001;
const endID = 200000;
const NUM_WORKERS = 15;
const REQUEST_INTERVAL_MS = 30 * 1000;
const OUTPUT_DIR = path.resolve(__dirname, 'output');
if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR);

const OUTPUT_FILE = path.join(OUTPUT_DIR, 'MO_buesiness_data.jsonl');
const PROGRESS_FILE = path.join(OUTPUT_DIR, 'progress.txt');

function loadProgress() {
    if (!fs.existsSync(PROGRESS_FILE)) return new Set();
    const lines = fs.readFileSync(PROGRESS_FILE, 'utf-8')
        .split('\n')
        .map(l => l.trim())
        .filter(l => l.length > 0);
    return new Set(lines.map(id => parseInt(id, 10)));
}

function saveProgress(id) {
    fs.appendFileSync(PROGRESS_FILE, id + '\n', 'utf-8');
}

function saveData(record) {
    const line = JSON.stringify(record) + '\n';
    fs.appendFileSync(OUTPUT_FILE, line, 'utf-8');
}

async function worker(sharedQueue, workerId) {
    let proxyIndex = Math.floor(Math.random() * 1000) + 1;
    const workerState = {
        workerId,
        proxyIndex,
        browser: null,
        proxyCreds: null,
    };
    console.log(`Worker ${workerId} started with initial proxy omuhmvei-${proxyIndex}`);
    while (true) {
        if (sharedQueue.length === 0) break;
        const id = sharedQueue.shift();
        const result = await scrapeSingleID(id, workerState);
        if (result && result.success) {
            saveData(result.record);
            saveProgress(id);
            console.log(`Worker ${workerId} successfully scraped and saved ID ${id}`);
        }
        console.log(`Worker ${workerId} waiting 30 seconds before next request...`);
        await delay(REQUEST_INTERVAL_MS);
    }
    if (workerState.browser) {
        try { await workerState.browser.close(); } catch { }
    }
    console.log(`Worker ${workerId} completed.`);
}

async function main() {
    const scriptStart = Date.now();
    const completedIDs = loadProgress();
    const allIDs = [];
    for (let id = startID; id <= endID; id++) {
        if (!completedIDs.has(id)) allIDs.push(id);
    }
    console.log(`Total IDs to scrape: ${allIDs.length}`);
    const sharedQueue = allIDs;
    console.log(`Starting ${NUM_WORKERS} workers with 30s interval between requests each.`);
    await Promise.all(
        Array.from({ length: NUM_WORKERS }, (_, i) => worker(sharedQueue, i + 1))
    );
    const elapsed = Date.now() - scriptStart;
    const sec = Math.floor((elapsed / 1000) % 60);
    const min = Math.floor((elapsed / (1000 * 60)) % 60);
    const hr = Math.floor(elapsed / (1000 * 60 * 60));
    console.log(`All workers done. Total runtime: ${hr}h ${min}m ${sec}s`);
}

main().catch(e => {
    console.error("Fatal error in main:", e);
    process.exit(1);
}); 