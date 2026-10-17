const root = document.documentElement
const themeSwitch = document.getElementById('theme-switch')

const saveTheme = (value) => {
  try {
    if (value) localStorage.setItem('lightmode', value)
    else localStorage.removeItem('lightmode')
  } catch (e) {}
}

const enableLightmode = () => {
  root.classList.add('lightmode')
  saveTheme('active')
}

const disableLightmode = () => {
  root.classList.remove('lightmode')
  saveTheme(null)
}

// filet de sécurité : head.html applique déjà le thème avant l'affichage, mais pas de mal à vérifier
try {
  if (localStorage.getItem('lightmode') === 'active') root.classList.add('lightmode')
} catch (e) {}

if (themeSwitch) {
  themeSwitch.addEventListener("click", () => {
    root.classList.contains('lightmode') ? disableLightmode() : enableLightmode()
  })
}

const menuToggle = document.getElementById('menu-toggle');
const navLinks = document.getElementById('nav-links');

if (menuToggle && navLinks) {
  menuToggle.addEventListener('click', () => {
    const isOpen = navLinks.classList.toggle('open');

    menuToggle.setAttribute('aria-expanded', isOpen);
    menuToggle.setAttribute(
      'aria-label',
      isOpen ? 'Fermer le menu' : 'Ouvrir le menu'
    );
  });

  navLinks.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
      menuToggle.setAttribute('aria-label', 'Ouvrir le menu');
    });
  });
}
