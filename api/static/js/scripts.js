document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const loadingIndicator = document.getElementById('loading-indicator');
    const resultDiv = document.getElementById('result');
    const generateButton = document.getElementById('generate-button');
    const heroElement = document.querySelector('.hero');
    const scrollIndicator = document.querySelector('.scroll-indicator');
    const storyGeneratorSection = document.querySelector('.story-generator-section');

    // Ensure loading indicator and result div are hidden initially
    loadingIndicator.style.display = 'none';
    resultDiv.style.display = 'none';

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        console.log('Form Data:', Object.fromEntries(formData));

        // Show loading indicator and disable button
        loadingIndicator.style.display = 'block';
        generateButton.disabled = true;
        resultDiv.style.display = 'none';

        try {
            const response = await fetch('/generate-story', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            console.log('Response:', result);

            if (response.ok) {
                resultDiv.innerHTML = `
                    <img src="${result.image_url}" alt="Uploaded Image" id="story-image">
                    <pre class="generated-story">${escapeHTML(result.story)}</pre>
                    <button id="download-pdf">Download Story as PDF</button>
                `;
                resultDiv.style.display = 'block'; // Show the result div
                
                // Add event listener to the download button
                document.getElementById('download-pdf').addEventListener('click', () => downloadPDF(result.story, result.image_url));
            } else {
                resultDiv.textContent = result.error || 'An error occurred';
                resultDiv.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
            resultDiv.textContent = 'An error occurred while generating the story.';
            resultDiv.style.display = 'block';
        } finally {
            loadingIndicator.style.display = 'none';
            generateButton.disabled = false;
        }
    });

    const images = [
        'https://images.unsplash.com/photo-1516414447565-b14be0adf13e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2073&q=80',
        'https://images.unsplash.com/photo-1532012197267-da84d127e765?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2787&q=80',
        'https://images.unsplash.com/photo-1474932430478-367dbb6832c1?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80',
        'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2073&q=80',
        'https://images.unsplash.com/photo-1519682337058-a94d519337bc?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80'
    ];
    let currentImageIndex = 0;

    function changeBackgroundImage() {
        heroElement.style.backgroundImage = `url('${images[currentImageIndex]}')`;
        currentImageIndex = (currentImageIndex + 1) % images.length;
    }

    // Set initial background image
    changeBackgroundImage();

    // Change background image every 5 seconds
    setInterval(changeBackgroundImage, 5000);

    scrollIndicator.addEventListener('click', () => {
        storyGeneratorSection.scrollIntoView({ behavior: 'smooth' });
    });

    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.animate-on-scroll');
        elements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementBottom = element.getBoundingClientRect().bottom;
            if (elementTop < window.innerHeight && elementBottom > 0) {
                element.classList.add('animated');
            }
        });
    };

    // Call animateOnScroll on initial load
    animateOnScroll();

    // Add scroll event listener
    window.addEventListener('scroll', animateOnScroll);
});

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

function downloadPDF(story, imageUrl) {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();
    
    // Add the image
    const img = new Image();
    img.onload = function() {
        const imgWidth = 190;
        const imgHeight = (img.height * imgWidth) / img.width;
        pdf.addImage(this, 'JPEG', 10, 10, imgWidth, imgHeight);
        
        // Add the story text
        const splitText = pdf.splitTextToSize(story, 190);
        pdf.text(splitText, 10, imgHeight + 20);
        
        // Save the PDF
        pdf.save('generated_story.pdf');
    };
    img.crossOrigin = "Anonymous";  // This line is important for handling CORS issues
    img.src = imageUrl;
}

function updateProgressBar(percent) {
    const progressBar = document.querySelector('.progress');
    progressBar.style.width = percent + '%';
}
