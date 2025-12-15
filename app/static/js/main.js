let currentSlide = 0;
let slides, progressDots, prevBtn, nextBtn, leftClickZone, rightClickZone;
let TOTAL_SLIDES = 0;

function initSlideshow() {
    // Re-select elements now that they exist in the DOM
    slides = document.querySelectorAll('.slide');
    progressDots = document.querySelectorAll('.progress-dot');
    prevBtn = document.querySelector('.nav-btn.prev');
    nextBtn = document.querySelector('.nav-btn.next');
    leftClickZone = document.querySelector('.click-zone.left');
    rightClickZone = document.querySelector('.click-zone.right');
    
    TOTAL_SLIDES = slides.length;
    currentSlide = 0;

    // Attach Event Listeners
    if(progressDots) progressDots.forEach((dot, index) => {
        dot.addEventListener('click', () => showSlide(index));
    });

    if(prevBtn) prevBtn.addEventListener('click', prevSlide);
    if(nextBtn) nextBtn.addEventListener('click', nextSlide);
    if(leftClickZone) leftClickZone.addEventListener('click', prevSlide);
    if(rightClickZone) rightClickZone.addEventListener('click', nextSlide);

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight' || e.key === ' ') {
            e.preventDefault();
            nextSlide();
        } else if (e.key === 'ArrowLeft') {
            e.preventDefault();
            prevSlide();
        }
    });

    // Show first slide
    if (TOTAL_SLIDES > 0) showSlide(0);
}

function showSlide(index) {
  if (index < 0 || index >= TOTAL_SLIDES) return;
  
  // Hide current
  if(slides[currentSlide]) slides[currentSlide].classList.remove('active');
  if(progressDots[currentSlide]) progressDots[currentSlide].classList.remove('active');
  
  currentSlide = index;
  
  // Show new
  if(slides[currentSlide]) slides[currentSlide].classList.add('active');
  if(progressDots[currentSlide]) progressDots[currentSlide].classList.add('active');
  
  // Update visited dots
  progressDots.forEach((dot, i) => {
    if (i < currentSlide) dot.classList.add('visited');
    else dot.classList.remove('visited');
  });
  
  // Update buttons
  if(prevBtn) prevBtn.classList.toggle('hidden', currentSlide === 0);
  if(nextBtn) nextBtn.classList.toggle('hidden', currentSlide === TOTAL_SLIDES - 1);
  
  triggerSlideAnimations(currentSlide);
}

function nextSlide() {
  if (currentSlide < TOTAL_SLIDES - 1) showSlide(currentSlide + 1);
}

function prevSlide() {
  if (currentSlide > 0) showSlide(currentSlide - 1);
}

function triggerSlideAnimations(slideIndex) {
  const slide = slides[slideIndex];
  const animatedElements = slide.querySelectorAll('.initially-hidden');
  
  animatedElements.forEach((el) => {
    const animationClass = el.dataset.animation;
    if (animationClass) {
      el.classList.remove(animationClass);
      void el.offsetWidth;
      el.classList.add(animationClass);
    }
  });
}