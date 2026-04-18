let currentCard = null;
let dueCards = [];
let batchSize = 0;
let isPracticeMode = false;
let sessionMissed = [];
let sessionCorrect = [];
let currentSessionId = null;

async function fetchDueCards(practice = false) {
    isPracticeMode = practice;
    const url = practice ? '/api/cards/due?practice=true' : '/api/cards/due';
    const response = await fetch(url);
    dueCards = await response.json();
    batchSize = dueCards.length;
    document.getElementById('due-count').innerText = practice ? "Practice Mode" : `Due: ${dueCards.length}`;
    
    if (dueCards.length > 0) {
        document.getElementById('session-summary').classList.add('hidden');
        document.getElementById('card-container').classList.remove('hidden');
        
        // Start a new session if one isn't already active
        if (!currentSessionId) {
            sessionMissed = [];
            sessionCorrect = [];
            const sessionRes = await fetch('/api/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stage: practice ? 'practice' : dueCards[0].stage })
            });
            const sessionData = await sessionRes.json();
            currentSessionId = sessionData.session_id;
        }
        
        showNextCard();
    } else {
        showSessionSummary(true);
    }
}

async function showSessionSummary(trulyAllDone = false) {
    document.getElementById('card-container').classList.add('hidden');
    document.getElementById('session-summary').classList.remove('hidden');
    
    // End the session if one is active
    if (currentSessionId) {
        await fetch(`/api/session/end/${currentSessionId}`, { method: 'POST' });
        currentSessionId = null;
    }
    
    const title = document.getElementById('summary-title');
    const content = document.getElementById('summary-content');
    const keepGoing = document.getElementById('keep-learning');
    const practiceMore = document.getElementById('start-practice');
    
    content.innerHTML = "";
    
    // If we finished a batch that was smaller than the limit (20), 
    // it means we've exhausted all due cards.
    if (trulyAllDone || batchSize < 20) {
        title.innerText = isPracticeMode ? "Practice Session Done!" : "All caught up! 🎉";
        content.innerText = isPracticeMode 
            ? "You've finished your extra practice session." 
            : "You've finished all your reviews for now.";
        keepGoing.classList.add('hidden');
        practiceMore.classList.remove('hidden');
    } else {
        title.innerText = isPracticeMode ? "Practice Goal Reached! 🎊" : "Goal Reached! 🎊";
        content.innerText = isPracticeMode 
            ? "You've finished your practice batch." 
            : "Great job hitting your review goal for this session.";
        keepGoing.classList.remove('hidden');
        practiceMore.classList.add('hidden');
    }
    // ... rest of debrief logic ...


    if (sessionMissed.length > 0) {
        const debriefArea = document.createElement('div');
        debriefArea.className = "debrief-area";
        debriefArea.innerText = "Analyzing your session...";
        content.appendChild(debriefArea);
        
        const debriefRes = await fetch('/api/session/debrief', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ missed: sessionMissed, recurring: [] })
        });
        const data = await debriefRes.json();
        debriefArea.innerText = data.debrief;
    }
}

document.getElementById('keep-learning').onclick = () => {
    fetchDueCards(isPracticeMode);
};

document.getElementById('start-practice').onclick = () => {
    fetchDueCards(true);
};

function showNextCard() {
    currentCard = dueCards[0];
    document.getElementById('char-display').innerText = currentCard.character;
    document.getElementById('stage-badge').innerText = currentCard.stage;
    
    const romajiElem = document.getElementById('romaji-display');
    romajiElem.innerText = currentCard.romaji;
    
    if (currentCard.romaji_visible === 0) {
        romajiElem.classList.add('hidden-faded');
    } else {
        romajiElem.classList.remove('hidden-faded');
    }
    
    document.getElementById('mnemonic-display').innerText = currentCard.mnemonic || "";
    document.getElementById('mnemonic-suggestions').innerHTML = "";
    document.getElementById('example-display').innerText = "Loading example...";
    document.querySelector('.card-back').classList.add('hidden');
    document.getElementById('controls').classList.add('hidden');
    document.getElementById('show-answer').classList.remove('hidden');
    
    fetchExample(currentCard.character);
}

async function fetchExample(char) {
    const res = await fetch(`/api/example/${char}`);
    const data = await res.json();
    document.getElementById('example-display').innerText = data.example || "";
}

async function saveMnemonic(body, source = "manual") {
    if (!currentCard) return;
    
    await fetch('/api/mnemonics/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: currentCard.card_id, body, source })
    });
}

document.getElementById('show-answer').onclick = () => {
    document.querySelector('.card-back').classList.remove('hidden');
    document.getElementById('controls').classList.remove('hidden');
    document.getElementById('show-answer').classList.add('hidden');
};

async function submitReview(rating) {
    if (rating < 3) {
        sessionMissed.push(currentCard.character);
    } else {
        sessionCorrect.push(currentCard.character);
    }

    await fetch('/api/reviews', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            card_id: currentCard.card_id, 
            rating,
            session_id: currentSessionId
        })
    });
    
    dueCards.shift();
    document.getElementById('due-count').innerText = `Due: ${dueCards.length}`;
    
    if (dueCards.length > 0) {
        showNextCard();
    } else {
        showSessionSummary(false);
    }
}

document.getElementById('edit-mnemonic').onclick = async () => {
    const current = document.getElementById('mnemonic-display').innerText;
    const mnemonic = prompt("Enter your mnemonic phrase:", current);
    if (mnemonic !== null) {
        document.getElementById('mnemonic-display').innerText = mnemonic;
        await saveMnemonic(mnemonic, "manual");
    }
};

document.getElementById('generate-mnemonic').onclick = async () => {
    const btn = document.getElementById('generate-mnemonic');
    const originalText = btn.innerText;
    btn.innerText = "Thinking...";
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/mnemonics/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ character: currentCard.character, romaji: currentCard.romaji })
        });
        
        if (!response.ok) throw new Error("Failed to generate mnemonics");
        
        const data = await response.json();
        const list = document.getElementById('mnemonic-suggestions');
        list.innerHTML = "";
        data.suggestions.forEach(s => {
            const div = document.createElement('div');
            div.className = "mnemonic-suggestion";
            div.innerText = s;
            div.style.cursor = "pointer";
            div.style.padding = "5px";
            div.style.borderBottom = "1px solid #eee";
            div.onclick = async () => {
                document.getElementById('mnemonic-display').innerText = s;
                await saveMnemonic(s, "ai-suggestion");
            };
            list.appendChild(div);
        });
    } catch (err) {
        console.error(err);
        alert("Could not reach the LLM. Is Ollama running?");
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
};

function showView(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    document.getElementById(`${viewName}-view`).classList.remove('hidden');
    if (viewName === 'progress') {
        renderProgress();
    }
}

async function renderProgress() {
    const response = await fetch('/api/mastery');
    const stats = await response.json();
    const grid = document.getElementById('mastery-grid');
    grid.innerHTML = "";
    
    stats.forEach(s => {
        const div = document.createElement('div');
        div.className = "mastery-item";
        div.innerText = s.character;
        div.title = `${s.romaji} - Accuracy: ${s.accuracy || 0}%`;
        
        const alpha = (s.accuracy || 0) / 100;
        div.style.backgroundColor = `rgba(52, 199, 89, ${alpha})`;
        if (alpha < 0.3) div.style.color = "black";
        else div.style.color = "white";
        
        grid.appendChild(div);
    });
}

// Start
const hash = window.location.hash.substring(1);
if (hash === 'progress') {
    showView('progress');
} else {
    fetchDueCards();
}

