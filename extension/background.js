const SERVER_URL = 'http://localhost:8765/activity';

function extractDomain(url) {
    try {
        if (!url || url.startsWith('chrome://') || url.startsWith('chrome-extension://') || url.startsWith('about:')) {
            return null;
        }
        const urlObj = new URL(url);
        return urlObj.hostname;
    } catch (e) {
        return null;
    }
}

function reportDomain(domain) {
    if (!domain) return;
    
    fetch(SERVER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            domain: domain,
            timestamp: Date.now()
        })
    }).catch(err => {
        // Server might not be running yet, silently ignore
        console.debug('RAGEWARE: Could not reach server', err.message);
    });
}

// Track tab activation (switching tabs)
chrome.tabs.onActivated.addListener((activeInfo) => {
    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (chrome.runtime.lastError) return;
        const domain = extractDomain(tab.url);
        reportDomain(domain);
    });
});

// Track tab URL updates (navigation within a tab)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.url || changeInfo.status === 'complete') {
        // Only report for the active tab
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (chrome.runtime.lastError) return;
            if (tabs[0] && tabs[0].id === tabId) {
                const domain = extractDomain(tab.url);
                reportDomain(domain);
            }
        });
    }
});

// Report current tab on extension load
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (chrome.runtime.lastError) return;
    if (tabs[0]) {
        const domain = extractDomain(tabs[0].url);
        reportDomain(domain);
    }
});
