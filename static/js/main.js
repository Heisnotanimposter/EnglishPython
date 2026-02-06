document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    const navLinks = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('.tab-content');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Remove active class from all links and sections
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            // Add active class to clicked link
            link.classList.add('active');

            // Show corresponding section
            const tabId = link.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Reading Module
    const pdfList = document.getElementById('pdf-list');
    const modal = document.getElementById('pdf-viewer-modal');
    const pdfFrame = document.getElementById('pdf-frame');
    const closeModal = document.querySelector('.close-modal');
    const filterBtns = document.querySelectorAll('.filter-btn');
    let allMaterials = [];

    // Fetch materials
    fetch('/api/materials')
        .then(response => response.json())
        .then(data => {
            allMaterials = data;
            renderMaterials(data);
        });

    function renderMaterials(materials) {
        pdfList.innerHTML = '';
        materials.forEach(item => {
            const div = document.createElement('div');
            div.className = 'pdf-item';
            div.innerHTML = `
                <div class="pdf-icon"><i class="fa-solid fa-file-pdf"></i></div>
                <div class="pdf-name">${item.name}</div>
                <div class="pdf-category">${item.category}</div>
            `;
            div.addEventListener('click', () => {
                openPdf(item.path);
            });
            pdfList.appendChild(div);
        });
    }

    function openPdf(path) {
        pdfFrame.src = `/pdfs/${path}`;
        modal.classList.remove('hidden');
    }

    closeModal.addEventListener('click', () => {
        modal.classList.add('hidden');
        pdfFrame.src = '';
    });

    // Filtering
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.getAttribute('data-filter');

            if (filter === 'all') {
                renderMaterials(allMaterials);
            } else {
                const filtered = allMaterials.filter(m => m.category === filter);
                renderMaterials(filtered);
            }
        });
    });

    // Writing Module
    const startTimerBtn = document.getElementById('start-timer');
    const resetTimerBtn = document.getElementById('reset-timer');
    const timerDisplay = document.getElementById('timer');
    const textArea = document.getElementById('writing-area');
    const wordCounter = document.getElementById('word-counter');
    let timerInterval;
    let timeLeft = 3600; // 60 minutes

    function updateTimer() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    startTimerBtn.addEventListener('click', () => {
        if (timerInterval) return;
        timerInterval = setInterval(() => {
            if (timeLeft > 0) {
                timeLeft--;
                updateTimer();
            } else {
                clearInterval(timerInterval);
                alert('Time is up!');
            }
        }, 1000);
    });

    resetTimerBtn.addEventListener('click', () => {
        clearInterval(timerInterval);
        timerInterval = null;
        timeLeft = 3600;
        updateTimer();
    });

    textArea.addEventListener('input', () => {
        const text = textArea.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        wordCounter.textContent = words;
    });

    // Speaking Module
    const recordBtn = document.getElementById('record-btn');
    const stopBtn = document.getElementById('stop-btn');
    const resultDiv = document.getElementById('speaking-result');
    const scoreVal = document.getElementById('score-val');
    const feedbackVal = document.getElementById('feedback-val');
    const waves = document.querySelectorAll('.wave');

    recordBtn.addEventListener('click', () => {
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        resultDiv.classList.add('hidden');

        // Simulate recording animation
        waves.forEach(w => w.style.animationPlayState = 'running');
    });

    stopBtn.addEventListener('click', () => {
        recordBtn.disabled = false;
        stopBtn.disabled = true;
        waves.forEach(w => w.style.animationPlayState = 'paused');

        // Mock submission
        const formData = new FormData();
        formData.append('audio', new Blob(['mock audio'], { type: 'audio/wav' }));

        fetch('/api/evaluate/speaking', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                scoreVal.textContent = data.score;
                feedbackVal.textContent = data.feedback;
                resultDiv.classList.remove('hidden');
            });
    });

    // Initialize waves as paused
    waves.forEach(w => w.style.animationPlayState = 'paused');

    // Listening Module
    const audioList = document.getElementById('audio-list');
    const audioPlayer = document.getElementById('main-audio-player');
    const trackNameDisplay = document.getElementById('current-track-name');
    const checkAnswersBtn = document.getElementById('check-answers-btn');
    const questionsContainer = document.getElementById('questions-container');
    const evaluationControls = document.getElementById('evaluation-controls');
    const calculateScoreBtn = document.getElementById('calculate-score-btn');
    const listeningScoreDisplay = document.getElementById('listening-score');
    const totalQuestionsDisplay = document.getElementById('total-questions');

    fetch('/api/audio')
        .then(response => response.json())
        .then(data => {
            renderAudioList(data);
        });

    function renderAudioList(files) {
        audioList.innerHTML = '';

        // Group by Book -> Test
        const groups = {};
        files.forEach(file => {
            const key = `${file.book} - Test ${file.test}`;
            if (!groups[key]) groups[key] = [];
            groups[key].push(file);
        });

        for (const [groupName, groupFiles] of Object.entries(groups)) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'audio-group';
            groupDiv.style.marginBottom = '1rem';

            const header = document.createElement('div');
            header.className = 'group-header';
            header.textContent = groupName;
            header.style.fontWeight = 'bold';
            header.style.padding = '0.5rem';
            header.style.background = 'rgba(255,255,255,0.05)';
            header.style.borderRadius = '4px';
            header.style.marginBottom = '0.5rem';
            groupDiv.appendChild(header);

            groupFiles.forEach(file => {
                const div = document.createElement('div');
                div.className = 'audio-item';
                div.innerHTML = `
                    <div><i class="fa-solid fa-music"></i> ${file.name}</div>
                    <div style="font-size: 0.8em; color: #94a3b8;">Section: ${file.section}</div>
                `;
                div.addEventListener('click', () => {
                    playAudio(file, div);
                });
                groupDiv.appendChild(div);
            });
            audioList.appendChild(groupDiv);
        }
    }

    function playAudio(file, element) {
        // Update UI
        document.querySelectorAll('.audio-item').forEach(el => el.classList.remove('playing'));
        element.classList.add('playing');

        trackNameDisplay.textContent = file.name;
        audioPlayer.src = `/audio/${file.path}`;
        audioPlayer.play();

        // Generate Questions
        generateQuestions(file.section);

        // Reset Evaluation UI
        checkAnswersBtn.classList.remove('hidden');
        evaluationControls.classList.add('hidden');
        checkAnswersBtn.disabled = false;
        checkAnswersBtn.textContent = "Start Evaluation";
    }

    function generateQuestions(section) {
        questionsContainer.innerHTML = '';
        let startQ = 1;
        let endQ = 40;

        // If section is 1, 2, 3, 4, we assume 10 questions each.
        // Section 1: 1-10, Section 2: 11-20, etc.
        // Note: This is a heuristic. Sometimes sections have different counts, but 10 is standard.
        if (section !== 'All' && !isNaN(section)) {
            const secNum = parseInt(section);
            startQ = (secNum - 1) * 10 + 1;
            endQ = secNum * 10;
        }

        for (let i = startQ; i <= endQ; i++) {
            const div = document.createElement('div');
            div.className = 'question-item';
            div.style.display = 'grid';
            div.style.gridTemplateColumns = '30px 1fr 1fr'; // Label, User Input, Correct Input
            div.style.gap = '10px';
            div.style.marginBottom = '10px';

            div.innerHTML = `
                <label style="align-self: center;">${i}.</label>
                <input type="text" class="answer-input user-answer" data-q="${i}" placeholder="Your Answer">
                <input type="text" class="answer-input correct-answer hidden" data-q="${i}" placeholder="Correct Answer" style="border-color: #f59e0b;">
            `;
            questionsContainer.appendChild(div);
        }

        totalQuestionsDisplay.textContent = endQ - startQ + 1;
    }

    checkAnswersBtn.addEventListener('click', () => {
        // Switch to Evaluation Mode
        const userInputs = document.querySelectorAll('.user-answer');
        const correctInputs = document.querySelectorAll('.correct-answer');

        userInputs.forEach(input => input.disabled = true);
        correctInputs.forEach(input => input.classList.remove('hidden'));

        checkAnswersBtn.classList.add('hidden');
        evaluationControls.classList.remove('hidden');
    });

    calculateScoreBtn.addEventListener('click', () => {
        let score = 0;
        const userInputs = document.querySelectorAll('.user-answer');
        const correctInputs = document.querySelectorAll('.correct-answer');

        userInputs.forEach((uInput, index) => {
            const cInput = correctInputs[index];
            const userVal = uInput.value.trim().toLowerCase();
            const correctVal = cInput.value.trim().toLowerCase();

            // Basic validation
            if (userVal && correctVal && userVal === correctVal) {
                score++;
                uInput.style.borderColor = '#10b981'; // Green
                cInput.style.borderColor = '#10b981';
            } else {
                uInput.style.borderColor = '#ef4444'; // Red
            }
        });

        listeningScoreDisplay.textContent = score;
        alert(`You scored ${score} out of ${userInputs.length}!`);
    });

    // Dictation Module
    const dictationAudioList = document.getElementById('dictation-audio-list');
    const dictationAudioPlayer = document.getElementById('dictation-audio-player');
    const dictationTrackName = document.getElementById('dictation-track-name');
    const dictationInput = document.getElementById('dictation-input');
    const referenceTranscript = document.getElementById('reference-transcript');
    const paraphraseInput = document.getElementById('paraphrase-input');
    
    let currentPass = 1;
    let currentAudioFile = null;
    let dictationMode = 'standard';
    let savedParaphrases = [];

    // Fetch audio files for dictation
    fetch('/api/audio')
        .then(response => response.json())
        .then(data => {
            renderDictationAudioList(data);
        });

    function renderDictationAudioList(files) {
        dictationAudioList.innerHTML = '';
        const groups = {};
        
        files.forEach(file => {
            const key = `${file.book} - Test ${file.test}`;
            if (!groups[key]) groups[key] = [];
            groups[key].push(file);
        });

        for (const [groupName, groupFiles] of Object.entries(groups)) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'audio-group';
            groupDiv.style.marginBottom = '1rem';

            const header = document.createElement('div');
            header.className = 'group-header';
            header.textContent = groupName;
            header.style.fontWeight = 'bold';
            header.style.padding = '0.5rem';
            header.style.background = 'rgba(255,255,255,0.05)';
            header.style.borderRadius = '4px';
            header.style.marginBottom = '0.5rem';
            groupDiv.appendChild(header);

            groupFiles.forEach(file => {
                const div = document.createElement('div');
                div.className = 'audio-item';
                div.innerHTML = `
                    <div><i class="fa-solid fa-music"></i> ${file.name}</div>
                    <div style="font-size: 0.8em; color: #94a3b8;">Section: ${file.section}</div>
                `;
                div.addEventListener('click', () => {
                    selectDictationAudio(file, div);
                });
                groupDiv.appendChild(div);
            });
            dictationAudioList.appendChild(groupDiv);
        }
    }

    function selectDictationAudio(file, element) {
        document.querySelectorAll('.audio-item').forEach(el => el.classList.remove('playing'));
        element.classList.add('playing');
        
        currentAudioFile = file;
        dictationTrackName.textContent = file.name;
        dictationAudioPlayer.src = `/audio/${file.path}`;
        
        // Reset passes
        currentPass = 1;
        resetPassControls();
    }

    function resetPassControls() {
        document.querySelectorAll('.pass-badge').forEach((badge, index) => {
            badge.classList.remove('active', 'completed');
            if (index === 0) badge.classList.add('active');
        });
        
        document.querySelectorAll('.pass-btn').forEach(btn => btn.disabled = true);
        document.getElementById('start-pass-1').disabled = false;
        document.getElementById('start-pass-1').classList.add('active');
        
        dictationInput.placeholder = 'Write down exactly what you hear... (1st Pass)';
        updatePassDisplay();
    }

    function updatePassDisplay() {
        document.getElementById('current-pass-display').textContent = currentPass;
        document.querySelectorAll('.pass-badge').forEach((badge, index) => {
            if (index < currentPass - 1) {
                badge.classList.add('completed');
                badge.classList.remove('active');
            } else if (index === currentPass - 1) {
                badge.classList.add('active');
            } else {
                badge.classList.remove('active', 'completed');
            }
        });
    }

    // Pass control buttons
    document.getElementById('start-pass-1').addEventListener('click', () => {
        startPass(1);
    });

    document.getElementById('start-pass-2').addEventListener('click', () => {
        startPass(2);
    });

    document.getElementById('start-pass-3').addEventListener('click', () => {
        startPass(3);
    });

    document.getElementById('replay-audio').addEventListener('click', () => {
        dictationAudioPlayer.currentTime = 0;
        dictationAudioPlayer.play();
    });

    function startPass(passNumber) {
        currentPass = passNumber;
        updatePassDisplay();
        
        // Update placeholder based on pass
        if (passNumber === 1) {
            dictationInput.placeholder = 'Write down exactly what you hear, even if incomplete... (1st Pass)';
        } else if (passNumber === 2) {
            dictationInput.placeholder = 'Replay and fill in gaps, focusing on grammar and word choice... (2nd Pass)';
        } else {
            dictationInput.placeholder = 'Final pass - refine accuracy, check articles, prepositions, verb tenses... (3rd Pass)';
        }
        
        // Enable next pass button
        if (passNumber < 3) {
            const nextPassBtn = document.getElementById(`start-pass-${passNumber + 1}`);
            nextPassBtn.disabled = false;
        }
        
        // Update active button
        document.querySelectorAll('.pass-btn').forEach(btn => btn.classList.remove('active'));
        document.getElementById(`start-pass-${passNumber}`).classList.add('active');
        
        // Play audio
        dictationAudioPlayer.currentTime = 0;
        dictationAudioPlayer.play();
    }

    // Dictation tabs
    const dictTabs = document.querySelectorAll('.dict-tab');
    const dictTabContents = document.querySelectorAll('.dict-tab-content');

    dictTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            
            dictTabs.forEach(t => t.classList.remove('active'));
            dictTabContents.forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });

    // Word count
    dictationInput.addEventListener('input', () => {
        const text = dictationInput.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        document.getElementById('dict-word-count').textContent = words;
    });

    // Mode selector
    document.querySelectorAll('input[name="dictation-mode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            dictationMode = e.target.value;
            updateDictationMode();
            saveDictationProgress();
        });
    });

    function updateDictationMode() {
        switch(dictationMode) {
            case 'shadow':
                dictationInput.placeholder = 'Shadow Dictation: Speak along with the audio while writing. This helps with pronunciation and rhythm.';
                if (dictationAudioPlayer.src) {
                    dictationAudioPlayer.play();
                }
                break;
            case 'summary':
                dictationInput.placeholder = 'Summarization Dictation: Capture the main ideas instead of word-for-word transcription. Focus on key concepts.';
                break;
            case 'gapfill':
                dictationInput.placeholder = 'Gap-Fill Dictation: Fill in the missing words. Upload or enter a transcript with blanks (marked as ____) first.';
                prepareGapFillMode();
                break;
            default:
                dictationInput.placeholder = 'Standard Dictation: Write down exactly what you hear...';
        }
    }

    function prepareGapFillMode() {
        // For gap-fill mode, we need a transcript with gaps
        // The user should have already uploaded or entered a transcript
        const transcript = referenceTranscript.value;
        
        if (transcript && transcript.includes('____')) {
            // Create gap-fill template
            const gapFillText = transcript.replace(/____/g, '______');
            dictationInput.value = gapFillText;
            dictationInput.readOnly = false;
            
            // Highlight gaps for user to fill
            dictationInput.style.background = 'rgba(255, 193, 7, 0.1)';
            dictationInput.style.borderColor = '#ffc107';
            
            // Switch to transcription tab
            document.querySelectorAll('.dict-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.dict-tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector('[data-tab="transcription"]').classList.add('active');
            document.getElementById('tab-transcription').classList.add('active');
        } else {
            // Prompt user to enter transcript with gaps
            alert('For Gap-Fill mode:\n\n1. Go to the "Transcript" tab\n2. Enter or upload a transcript with gaps marked as "____" (four underscores)\n3. Then switch back to Gap-Fill mode');
            
            // Switch to transcript tab
            document.querySelectorAll('.dict-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.dict-tab-content').forEach(c => c.classList.remove('active'));
            document.querySelector('[data-tab="transcript"]').classList.add('active');
            document.getElementById('tab-transcript').classList.add('active');
        }
    }

    // Enhance shadow dictation with audio synchronization
    dictationAudioPlayer.addEventListener('play', () => {
        if (dictationMode === 'shadow') {
            // Enable microphone input for shadow dictation
            // Note: Actual microphone input would require Web Audio API
            console.log('Shadow dictation mode: Speak along with the audio while writing.');
        }
    });

    // Save and load dictation progress
    function saveDictationProgress() {
        const progress = {
            currentPass: currentPass,
            userText: dictationInput.value,
            audioFile: currentAudioFile,
            mode: dictationMode,
            timestamp: new Date().toISOString()
        };
        localStorage.setItem('dictation_progress', JSON.stringify(progress));
    }

    function loadDictationProgress() {
        const saved = localStorage.getItem('dictation_progress');
        if (saved) {
            try {
                const progress = JSON.parse(saved);
                currentPass = progress.currentPass || 1;
                if (progress.userText) {
                    dictationInput.value = progress.userText;
                }
                if (progress.mode) {
                    document.querySelector(`input[name="dictation-mode"][value="${progress.mode}"]`).checked = true;
                    dictationMode = progress.mode;
                    updateDictationMode();
                }
                updatePassDisplay();
            } catch (e) {
                console.error('Error loading progress:', e);
            }
        }
    }

    // Auto-save progress
    dictationInput.addEventListener('input', () => {
        saveDictationProgress();
        const text = dictationInput.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        document.getElementById('dict-word-count').textContent = words;
    });

    // Load progress on page load
    loadDictationProgress();

    // Transcript upload
    document.getElementById('transcript-file').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                referenceTranscript.value = event.target.result;
            };
            reader.readAsText(file);
        }
    });

    document.getElementById('load-transcript-btn').addEventListener('click', () => {
        const fileInput = document.getElementById('transcript-file');
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            const reader = new FileReader();
            reader.onload = (event) => {
                referenceTranscript.value = event.target.result;
            };
            reader.readAsText(file);
        }
    });

    document.getElementById('enter-transcript-btn').addEventListener('click', () => {
        referenceTranscript.readOnly = false;
        referenceTranscript.focus();
    });

    // Generate gap-fill template
    document.getElementById('generate-gap-fill-btn').addEventListener('click', () => {
        const transcript = referenceTranscript.value.trim();
        if (!transcript) {
            alert('Please first enter or load a transcript.');
            return;
        }

        // Simple gap-fill generator: remove every 5th-8th word randomly
        const words = transcript.split(/\s+/);
        const gapFillWords = [];
        
        for (let i = 0; i < words.length; i++) {
            // Remove about 20% of words (every 5th word on average)
            if (Math.random() < 0.2 && words[i].length > 2 && !words[i].match(/^[.,!?;:]+$/)) {
                gapFillWords.push('____');
            } else {
                gapFillWords.push(words[i]);
            }
        }
        
        const gapFillText = gapFillWords.join(' ');
        referenceTranscript.value = gapFillText;
        alert('Gap-fill template generated! Words have been replaced with "____". You can edit it manually if needed.');
    });

    // Comparison
    document.getElementById('compare-btn').addEventListener('click', () => {
        compareTranscripts();
    });

    function compareTranscripts() {
        const userText = dictationInput.value.trim();
        const referenceText = referenceTranscript.value.trim();

        if (!userText || !referenceText) {
            alert('Please provide both your transcription and the reference transcript.');
            return;
        }

        fetch('/api/dictation/compare', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_text: userText,
                reference_text: referenceText
            })
        })
        .then(response => response.json())
        .then(data => {
            displayComparison(data);
            displayErrorSummary(data.errors);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error comparing transcripts. Please try again.');
        });
    }

    function displayComparison(data) {
        const userDisplay = document.getElementById('user-text-display');
        const correctDisplay = document.getElementById('correct-text-display');

        userDisplay.innerHTML = `<h4>Your Transcription</h4><div class="comparison-content">${data.user_html}</div>`;
        correctDisplay.innerHTML = `<h4>Reference Transcript</h4><div class="comparison-content">${data.reference_html}</div>`;

        document.getElementById('tab-comparison').classList.add('active');
        document.querySelectorAll('.dict-tab').forEach(t => t.classList.remove('active'));
        document.querySelector('[data-tab="comparison"]').classList.add('active');
    }

    function displayErrorSummary(errors) {
        document.getElementById('error-summary').classList.remove('hidden');
        
        let grammarCount = 0, spellingCount = 0, listeningCount = 0, vocabCount = 0;
        
        errors.forEach(error => {
            switch(error.category) {
                case 'grammar':
                    grammarCount++;
                    break;
                case 'spelling':
                    spellingCount++;
                    break;
                case 'listening':
                    listeningCount++;
                    break;
                case 'vocabulary':
                    vocabCount++;
                    break;
            }
        });

        document.getElementById('total-errors').textContent = errors.length;
        document.getElementById('grammar-errors').textContent = grammarCount;
        document.getElementById('spelling-errors').textContent = spellingCount;
        document.getElementById('listening-errors').textContent = listeningCount;
        document.getElementById('vocab-errors').textContent = vocabCount;
    }

    // Paraphrase functionality
    document.getElementById('save-paraphrase-btn').addEventListener('click', () => {
        const paraphrase = paraphraseInput.value.trim();
        if (paraphrase) {
            savedParaphrases.push({
                text: paraphrase,
                date: new Date().toLocaleString(),
                audio: currentAudioFile ? currentAudioFile.name : 'Unknown'
            });
            updateParaphraseList();
            paraphraseInput.value = '';
        }
    });

    document.getElementById('clear-paraphrase-btn').addEventListener('click', () => {
        paraphraseInput.value = '';
    });

    function updateParaphraseList() {
        const list = document.getElementById('paraphrase-list');
        if (savedParaphrases.length > 0) {
            document.getElementById('paraphrase-saved').classList.remove('hidden');
            list.innerHTML = savedParaphrases.map((item, index) => `
                <div class="paraphrase-item">
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem;">
                        ${item.date} - ${item.audio}
                    </div>
                    <div>${item.text}</div>
                    <button onclick="deleteParaphrase(${index})" style="margin-top: 0.5rem; padding: 0.25rem 0.5rem; background: #ef4444; border: none; border-radius: 4px; color: white; cursor: pointer;">Delete</button>
                </div>
            `).join('');
        }
    }

    window.deleteParaphrase = function(index) {
        savedParaphrases.splice(index, 1);
        updateParaphraseList();
    };
});
