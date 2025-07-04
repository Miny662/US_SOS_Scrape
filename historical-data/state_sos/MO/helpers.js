const cheerio = require('cheerio');

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function extractData(html, id) {
    const $ = cheerio.load(html);
    const keys = [
        "Name(s)", "Principal Office Address", "Type", "Charter No.",
        "Domesticity", "Registered Agent", "Status", "Date Formed",
        "Duration", "Report Due"
    ];
    const info = {};
    const detailSpans = $('span.swLabelDetailsBlack');
    const poaSpan = $('span.swLabelWrap').first();
    let idx = 0;
    keys.forEach(key => {
        if (key === "Principal Office Address") {
            info[key] = poaSpan.text().trim();
        } else {
            info[key] = detailSpans.eq(idx).text().trim() || "";
            idx++;
        }
    });
    function parseTable(tableIndex) {
        const tables = $('table.rgMasterTable');
        if (tableIndex >= tables.length) return [];
        const table = tables.eq(tableIndex);
        const headers = [];
        table.find('th').each((i, el) => {
            headers.push($(el).text().trim());
        });
        const rows = [];
        table.find('tr').each((i, tr) => {
            const cells = $(tr).find('td');
            if (cells.length === headers.length) {
                const row = {};
                cells.each((j, td) => {
                    row[headers[j]] = $(td).text().trim();
                });
                rows.push(row);
            }
        });
        return rows;
    }
    return {
        ID: id,
        "General Information": info,
        Filings: parseTable(0),
        "Principal Office Addresses": parseTable(1),
        Contacts: parseTable(2)
    };
}

async function isCaptchaPresent(page) {
    return await page.evaluate(() => !!document.querySelector('.zone-name-title h1'));
}

async function isUrlNotFound(page) {
    return await page.evaluate(() => {
        const div = document.querySelector('div[style*="border: 3px solid #4991C5"]');
        if (!div) return false;
        return div.textContent.trim() === "The specified URL cannot be found.";
    });
}

async function waitForRowClass(page, timeoutMs = 5 * 60 * 1000, pollInterval = 2000) {
    const startTime = Date.now();
    while (true) {
        const hasRow = await page.evaluate(() => document.getElementsByClassName('row').length > 0);
        if (hasRow) return true;
        if (Date.now() - startTime > timeoutMs) return false;
        await delay(pollInterval);
    }
}

module.exports = {
    delay,
    extractData,
    isCaptchaPresent,
    isUrlNotFound,
    waitForRowClass
}; 