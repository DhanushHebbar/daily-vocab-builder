console.log("Script loaded.");

function speakText(text) {
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance(text);
    synth.speak(utter);
}


document.addEventListener('DOMContentLoaded', function () {
    const feedbackForm = document.getElementById('feedback-form');

    if (feedbackForm) {
        feedbackForm.addEventListener('submit', function (event) {
            event.preventDefault(); // 🛑 Prevent default form submission

            const formData = new FormData(feedbackForm);

            fetch('/sentence_feedback', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json()) // Adjust if you're returning JSON or HTML
            .then(data => {
                // Handle response data
                console.log('Feedback submitted successfully');
            })
            .catch(error => {
                console.error('Error submitting feedback:', error);
            });
        });
    }
});
