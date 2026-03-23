let currentCard = null;
let dueCards = [];
let sessionMissed = [];
let sessionCorrect = [];

async function fetchDueCards() {
    const response = await fetch('/api/cards/due');
    dueCards = await response.json();
    document.getElementById('due-count').innerText = `Due: ${dueCards.length}`;
    if (dueCards.length > 0) {
        showNextCard();
    } else {
        showSessionSummary();
    }
}

async function showSessionSummary() {
    document.getElementById('char-display').innerText = "All done! 🎉";
    document.getElementById('show-answer').classList.add('hidden');
    document.querySelector('.card-back').classList.add('hidden');
    document.getElementById('controls').classList.add('hidden');
    
    if (sessionMissed.length > 0) {
        document.getElementById('example-display').innerText = "Analyzing your session...";
        const debriefRes = await fetch('/api/session/debrief', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ missed: sessionMissed, recurring: [] })
        });
        const data = await debriefRes.json();
        document.getElementById('example-display').innerText = data.debrief;
    }
}

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
        body: JSON.stringify({ card_id: currentCard.card_id, rating })
    });
    
    dueCards.shift();
    document.getElementById('due-count').innerText = `Due: ${dueCards.length}`;
    
    if (dueCards.length > 0) {
        showNextCard();
    } else {
        showSessionSummary();
    }
}

document.getElementById('generate-mnemonic').onclick = async () => {
    const btn = document.getElementById('generate-mnemonic');
    btn.innerText = "Thinking...";
    btn.disabled = true;
    
    const response = await fetch('/api/mnemonics/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character: currentCard.character, romaji: currentCard.romaji })
    });
    
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
        div.onclick = () => {
            document.getElementById('mnemonic-display').innerText = s;
        };
        list.appendChild(div);
    });
    btn.innerText = "Help me remember this";
    btn.disabled = false;
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
fetchDueCards();
