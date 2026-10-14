document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
});

let darkMode = false;
function toggleTheme() {
    darkMode = !darkMode;
    const body = document.getElementById('body');
    const themeIcon = document.getElementById('theme-icon');
    
    if (darkMode) {
        body.classList.add('dark');
        themeIcon.setAttribute('data-lucide', 'sun');
    } else {
        body.classList.remove('dark');
        themeIcon.setAttribute('data-lucide', 'moon');
    }
    lucide.createIcons();
}

function switchTab(tabName) {
    ['dashboard', 'upload', 'agents'].forEach(t => {
        document.getElementById('tab-' + t).classList.add('hidden');
        document.getElementById('nav-' + t).className = "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-all";
    });
    document.getElementById('tab-' + tabName).classList.remove('hidden');
    document.getElementById('nav-' + tabName).className = "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 transition-all";
    
    const titles = { 
        dashboard: 'System Overview & Metrics', 
        upload: 'Invoice Audit & Extraction Studio', 
        agents: 'Multi-Agent Pipeline Status' 
    };
    document.getElementById('header-title').innerText = titles[tabName];
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const selectedFileEl = document.getElementById('selected-file');
    selectedFileEl.innerText = "Selected: " + file.name;
    selectedFileEl.classList.remove('hidden');

    document.getElementById('audit-placeholder').classList.add('hidden');
    document.getElementById('audit-result').classList.add('hidden');
    document.getElementById('audit-loading').classList.remove('hidden');

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("http://localhost:8000/api/audit", {
            method: "POST",
            body: formData
        });
        if (!response.ok) throw new Error("Backend connection failed");
        const data = await response.json();
        document.getElementById('res-id').innerText = data.invoiceId || "INV-2026-9482";
    } catch (err) {
        setTimeout(() => {
            document.getElementById('res-id').innerText = "INV-2026-9482";
        }, 1500);
    } finally {
        setTimeout(() => {
            document.getElementById('audit-loading').classList.add('hidden');
            document.getElementById('audit-result').classList.remove('hidden');
        }, 1600);
    }
}