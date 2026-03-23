let currentCard = null;
let dueCards = [];

async function fetchDueCards() {
    const response = await fetch('/api/cards/due');
    dueCards = await response.json();
    document.getElementById('due-count').innerText = `Due: ${dueCards.length}`;
    if (dueCards.length > 0) {
        showNextCard();
    } else {
        document.getElementById('char-display').innerText = "All done! 🎉";
        document.getElementById('show-answer').classList.add('hidden');
    }
}

function showNextCard() {
    currentCard = dueCards[0];
    document.getElementById('char-display').innerText = currentCard.character;
    document.getElementById('stage-badge').innerText = currentCard.stage;
    
    // Hide back
    const romajiElem = document.getElementById('romaji-display');
    romajiElem.innerText = currentCard.romaji;
    
    // Spec: Romaji hidden automatically if romaji_visible is 0
    if (currentCard.romaji_visible === 0) {
        romajiElem.classList.add('hidden-faded');
    } else {
        romajiElem.classList.remove('hidden-faded');
    }
    
    document.getElementById('mnemonic-display').innerText = currentCard.mnemonic || "";
    document.querySelector('.card-back').classList.add('hidden');
    document.getElementById('controls').classList.add('hidden');
    document.getElementById('show-answer').classList.remove('hidden');
    
    // Fetch example sentence
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
        await fetchDueCards(); // Double check
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
        div.onclick = () => {
            document.getElementById('mnemonic-display').innerText = s;
            // TODO: API to save this choice
        };
        list.appendChild(div);
    });
    btn.innerText = "Help me remember this";
    btn.disabled = false;
};

// Start
fetchDueCards();
