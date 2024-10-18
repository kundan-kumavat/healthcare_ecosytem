const body = document.querySelector('body'),
      sidebar = body.querySelector('.sidebar'),
      toggle = body.querySelector('.toggle')
      searchBtn = body.querySelector('.search-box'),
      modeSwitch = body.querySelector('.toggle-switch'),
      modeText = body.querySelector('.mode-text');

const navLinks = document.getElementsByClassName('nav-link')

;[...navLinks].forEach(navLink => {
    navLink.addEventListener('click', isActive)
});

function isActive(){
    const current = this
    current.classList.add('active')
    const attri = current.getAttribute('url_for');
    localStorage.setItem('activeLink', attri);
}

document.addEventListener('DOMContentLoaded', () => {
    const localLink = localStorage.getItem('activeLink');

    const activeLink = body.querySelector('.nav-link.active')
    activeLink.classList.remove('active')

    if(activeLink){
        const current = document.querySelector(`.nav-link[url_for=${localLink}]`)
        current.classList.add('active');
    }
})

toggle.addEventListener('click', () => {
    sidebar.classList.toggle('close')
})

modeSwitch.addEventListener('click', () => {
    body.classList.toggle('dark')

    if(body.classList.contains('dark')){
        modeText.innerText = "Light Mode"
    }else{
        modeText.innerText = "Dark Mode"
    }
})

const notifications = document.querySelector(".notifications");

// Object containing details for different types of toasts
const toastDetails = {
    timer: 5000,
    success: {
        icon: 'fa-circle-check',
        text: 'Success: Login successful!',
    },
    error: {
        icon: 'fa-circle-xmark',
        text: 'Error: Invalid credentials.',
    },
    info: {
        icon: 'fa-circle-xmark',
        text: 'Error: Invalid credentials.',
    }
};

const removeToast = (toast) => {
    toast.classList.add("hide");
    if (toast.timeoutId) clearTimeout(toast.timeoutId); // Clear the timeout for the toast
    setTimeout(() => toast.remove(), 500); // Removing the toast after 500ms
};

const createToast = (type) => {
    const { icon, text } = toastDetails[type]; // Get the icon and text based on the type
    const toast = document.createElement("li"); // Create a new 'li' element for the toast
    toast.className = `toast ${type}`; // Assign the appropriate class to the toast
    toast.innerHTML = `<div class="column">
                         <i class="fa-solid ${icon}"></i>
                         <span>${text}</span>
                      </div>
                      <i class="fa-solid fa-xmark" onclick="removeToast(this.parentElement)"></i>`;
    notifications.appendChild(toast); // Append the toast to the notifications container
    toast.timeoutId = setTimeout(() => removeToast(toast), toastDetails.timer); // Set a timeout to auto-remove the toast
};

function showNotification(type) {
    console.log(`Notification Type: ${type}`);  // Add this for debugging
    createToast(type);
}