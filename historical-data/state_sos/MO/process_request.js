const { connect } = require('puppeteer-real-browser');
const { delay, extractData, isCaptchaPresent, isUrlNotFound, waitForRowClass } = require('./helpers');

const totalProxies = 1000;
const proxyPassword = 'tjynmmev6t7a';
const MAX_RETRIES = 5;

function getProxyCredentials(index) {
    return {
        username: `omuhmvei-${index}`,
        password: proxyPassword,
        host: 'p.webshare.io',
        port: 80,
    };
}

async function scrapeSingleID(id, workerState) {
    for (let retryCount = 0; retryCount <= MAX_RETRIES; retryCount++) {
        const proxyCreds = getProxyCredentials(workerState.proxyIndex);
        console.log(`Worker ${workerState.workerId} scraping ID ${id} with proxy ${proxyCreds.username}, attempt ${retryCount + 1}`);
        try {
            if (!workerState.browser) {
                const { browser } = await connect({
                    headless: false,
                    fingerprint: true,
                    turnstile: true,
                    args: [
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                        '--window-size=1920,0',
                        `--proxy-server=${proxyCreds.host}:${proxyCreds.port}`,
                    ],
                    connectOption: { defaultViewport: null },
                });
                workerState.browser = browser;
                workerState.proxyCreds = proxyCreds;
            }
            const page = await workerState.browser.newPage();
            await page.authenticate({
                username: workerState.proxyCreds.username,
                password: workerState.proxyCreds.password,
            });
            const url = `https://bsd.sos.mo.gov/BusinessEntity/BusinessEntityDetail.aspx?page=beSearch&ID=${id}`;
            await page.goto(url, { waitUntil: 'load', timeout: 120000 });
            const captcha = await isCaptchaPresent(page);
            if (captcha) {
                console.warn(`Worker ${workerState.workerId} CAPTCHA detected on ID ${id}. Rotating proxy and retrying...`);
                await page.close();
                await workerState.browser.close();
                workerState.browser = null;
                workerState.proxyIndex = (workerState.proxyIndex % totalProxies) + 1;
                continue;
            }
            const urlNotFound = await isUrlNotFound(page);
            if (urlNotFound) {
                console.warn(`Worker ${workerState.workerId} "The specified URL cannot be found." message on ID ${id}. Rotating proxy and retrying...`);
                await page.close();
                await workerState.browser.close();
                workerState.browser = null;
                workerState.proxyIndex = (workerState.proxyIndex % totalProxies) + 1;
                continue;
            }
            const hasRow = await waitForRowClass(page, 5 * 60 * 1000, 2000);
            if (!hasRow) {
                console.warn(`Worker ${workerState.workerId} no '.row' elements on ID ${id}. Rotating proxy and retrying...`);
                await page.close();
                await workerState.browser.close();
                workerState.browser = null;
                workerState.proxyIndex = (workerState.proxyIndex % totalProxies) + 1;
                continue;
            }
            await delay(1000);
            const htmlContent = await page.content();
            const record = extractData(htmlContent, id);
            await page.close();
            return { record, id, success: true };
        } catch (error) {
            console.error(`Worker ${workerState.workerId} error scraping ID ${id}: ${error.message}`);
            if (workerState.browser) {
                try { await workerState.browser.close(); } catch { }
                workerState.browser = null;
            }
            workerState.proxyIndex = (workerState.proxyIndex % totalProxies) + 1;
            if (retryCount === MAX_RETRIES) {
                console.error(`Worker ${workerState.workerId} max retries reached for ID ${id}, skipping.`);
                return { id, success: false };
            }
        }
    }
}

module.exports = { scrapeSingleID }; 