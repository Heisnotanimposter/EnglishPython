function checkAnswers() {
    const answers = {
        q1: "C",
        q2: "False",
        q3: "equal number",
        q4a: "B",
        q4b: "C",
        q4c: "A",
        q5: "24"
    };

    let score = 0;

    if (document.querySelector('input[name="q1"]:checked')?.value === answers.q1) score++;
    if (document.querySelector('input[name="q2"]:checked')?.value === answers.q2) score++;
    if (document.getElementById("q3").value.trim().toLowerCase() === answers.q3) score++;
    if (document.getElementById("q4a").value === answers.q4a) score++;
    if (document.getElementById("q4b").value === answers.q4b) score++;
    if (document.getElementById("q4c").value === answers.q4c) score++;
    if (document.getElementById("q5").value === answers.q5) score++;

    document.getElementById("results").innerText = `You scored ${score}/7`;
}